
import sys
import os
from io import StringIO
from pathlib import Path
import time
import datetime
import json
import random
import math
import re
import base64
import hashlib
import glob

# Zip-container writes (docx/epub/xlsx/pptx) need seek-on-write; the FUSE
# workspace mount rejects it. Redirect zip writes to /tmp, copy back on close.

_SC_ZIP_SHIM_ROOT = globals().get("_SC_ZIP_SHIM_ROOT", "/workspace")


def _sc_install_zip_write_shim():
    import os as _os
    import shutil as _sh
    import uuid as _uu
    import zipfile as _zfmod

    if getattr(_zfmod.ZipFile, "_sc_ws_shim", False):
        return
    _orig_init = _zfmod.ZipFile.__init__
    _orig_close = _zfmod.ZipFile.close

    def _sc_ws_target(file, mode):
        if not any(c in str(mode) for c in "wxa"):
            return None
        try:
            p = _os.fspath(file)
        except TypeError:
            return None  # file object, not a path — leave untouched
        if isinstance(p, bytes):
            try:
                p = p.decode()
            except Exception:
                return None
        ap = _os.path.abspath(p)
        root = _os.path.abspath(_SC_ZIP_SHIM_ROOT)
        if ap == root or ap.startswith(root + _os.sep):
            return ap
        return None

    def _sc_init(self, file, mode="r", *a, **k):
        self._sc_zip_final = None
        target = _sc_ws_target(file, mode)
        if target:
            # Exclusive-create semantics must survive the redirect: the tmp
            # file never exists, so without this check "x" would silently
            # OVERWRITE an existing workspace archive on close.
            if "x" in str(mode) and _os.path.exists(target):
                raise FileExistsError(17, "File exists", target)
            tmp = _os.path.join(
                "/tmp",
                "_sc_zip_" + _uu.uuid4().hex[:12]
                + (_os.path.splitext(target)[1] or ".zip"),
            )
            if "a" in str(mode) and _os.path.exists(target):
                _sh.copyfile(target, tmp)
            self._sc_zip_final = (tmp, target)
            file = tmp
        _orig_init(self, file, mode, *a, **k)

    def _sc_close(self):
        _orig_close(self)
        fin = getattr(self, "_sc_zip_final", None)
        if fin:
            self._sc_zip_final = None
            tmp, target = fin
            _d = _os.path.dirname(target)
            if _d:
                _os.makedirs(_d, exist_ok=True)
            # copyfile (data only, sequential) then unlink: shutil.move
            # would copystat, which some FUSE mounts refuse.
            _sh.copyfile(tmp, target)
            try:
                _os.unlink(tmp)
            except OSError:
                pass

    _zfmod.ZipFile.__init__ = _sc_init
    _zfmod.ZipFile.close = _sc_close
    _zfmod.ZipFile._sc_ws_shim = True


_sc_install_zip_write_shim()


# Import commonly used libraries (installed in sandbox container)
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    Image = ImageDraw = ImageFont = ImageFilter = None

try:
    import numpy as np
    numpy = np
except ImportError:
    np = numpy = None

try:
    import pandas as pd
    pandas = pd
except ImportError:
    pd = pandas = None

try:
    from PyPDF2 import PdfReader, PdfWriter, PdfMerger
except ImportError:
    PdfReader = PdfWriter = PdfMerger = None

try:
    from docx import Document as DocxDocument
    Document = DocxDocument
except ImportError:
    DocxDocument = Document = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    import ebooklib
    from ebooklib import epub
except ImportError:
    ebooklib = epub = None

try:
    import openpyxl
except ImportError:
    openpyxl = None

try:
    import cv2
except ImportError:
    cv2 = None

try:
    from pdf2image import convert_from_path, convert_from_bytes
except ImportError:
    convert_from_path = convert_from_bytes = None

try:
    # MoviePy 2.x syntax (host container)
    from moviepy import (
        VideoFileClip, ImageClip, TextClip, AudioFileClip,
        CompositeVideoClip, CompositeAudioClip,
        concatenate_videoclips, concatenate_audioclips, vfx
    )
except ImportError:
    try:
        # MoviePy 1.x syntax (sandbox container uses 1.x for crossfadein/crossfadeout support)
        from moviepy.editor import (
            VideoFileClip, ImageClip, TextClip, AudioFileClip,
            CompositeVideoClip, CompositeAudioClip,
            concatenate_videoclips, concatenate_audioclips, vfx
        )
    except ImportError:
        VideoFileClip = ImageClip = TextClip = AudioFileClip = None
        CompositeVideoClip = CompositeAudioClip = None
        concatenate_videoclips = concatenate_audioclips = vfx = None

# ROBUSTNESS: MoviePy 1.x CompositeAudioClip does not set .fps, so a direct
# write_audiofile() raises "'CompositeAudioClip' object has no attribute 'fps'".
# Patch __init__ so every instance gets an fps (derived from its inputs, else
# 44100), covering write_audiofile() and any other downstream export path.
if CompositeAudioClip is not None:
    try:
        _orig_cac_init = CompositeAudioClip.__init__
        def _safe_cac_init(self, *args, **kwargs):
            _orig_cac_init(self, *args, **kwargs)
            if not getattr(self, "fps", None):
                _derived = 44100
                for _c in (getattr(self, "clips", None) or []):
                    _f = getattr(_c, "fps", None)
                    if _f:
                        _derived = max(_derived, int(_f))
                self.fps = _derived
        CompositeAudioClip.__init__ = _safe_cac_init
    except Exception:
        pass

# Set workspace constant
WORKSPACE = "/workspace"

# Robustness: workspace files are flattened to /workspace/<basename>. If code
# opens a file via a session_id/file_id-prefixed path (which doesn't exist in the
# sandbox) for READING, transparently fall back to the basename at the workspace
# root. Only the failure case is affected — normal opens are unchanged, and the
# original error is re-raised when no basename match exists. This also covers
# PIL.Image.open(path), which reads via builtins.open under the hood. Wrapped so
# a patch failure can never break execution.
try:
    import builtins as _sc_builtins
    _sc_real_open = _sc_builtins.open
    def _sc_ws_open(file, mode='r', *a, **k):
        try:
            return _sc_real_open(file, mode, *a, **k)
        except (FileNotFoundError, IsADirectoryError, OSError):
            try:
                if isinstance(file, (str, bytes)) and str(mode)[:1] == 'r':
                    _bn = os.path.basename(str(file))
                    _alt = os.path.join('/workspace', _bn)
                    if _bn and _alt != str(file) and os.path.exists(_alt):
                        return _sc_real_open(_alt, mode, *a, **k)
            except Exception:
                pass
            raise
    _sc_builtins.open = _sc_ws_open
except Exception:
    pass

_DEAD_CLIP_NAMES = frozenset()

def _sc_basename(p):
    import os
    return os.path.basename(str(p))


def _sc_filter_dead_clips(clips):
    if not _DEAD_CLIP_NAMES:
        return list(clips)
    return [c for c in clips if _sc_basename(c) not in _DEAD_CLIP_NAMES]


def _sc_guard_not_dead_take(path, what="clip"):
    if _DEAD_CLIP_NAMES and _sc_basename(path) in _DEAD_CLIP_NAMES:
        raise ValueError(
            "%s: '%s' is a superseded dead take — animate from the scene's current still first."
            % (what, _sc_basename(path))
        )

_SUPERCOOL_FONT_DIRS = ['/usr/share/fonts/truetype/supercool', '/app/assets/fonts', '/workspace']

_SUPERCOOL_FONT_CATALOG = {
    # style: { weight: filename }
    "serif":          {"regular": "EBGaramond-Regular.ttf", "bold": "EBGaramond-Bold.ttf", "italic": "EBGaramond-Italic.ttf"},
    "serif_elegant":  {"regular": "PlayfairDisplay-Regular.ttf", "bold": "PlayfairDisplay-Bold.ttf", "italic": "PlayfairDisplay-Italic.ttf"},
    "serif_display":  {"regular": "Cinzel-Regular.ttf", "bold": "Cinzel-Bold.ttf"},
    "slab":           {"regular": "RobotoSlab-Regular.ttf", "bold": "RobotoSlab-Bold.ttf"},
    "sans":           {"regular": "Inter-Regular.ttf", "medium": "Inter-Medium.ttf", "bold": "Inter-Bold.ttf", "italic": "Inter-SemiBoldItalic.ttf"},
    "sans_geometric": {"regular": "Montserrat-Regular.ttf", "bold": "Montserrat-Bold.ttf"},
    "sans_condensed": {"regular": "Oswald-Regular.ttf", "medium": "Oswald-Medium.ttf", "bold": "Oswald-Bold.ttf"},
    "script":         {"regular": "DancingScript-Regular.ttf", "bold": "DancingScript-Bold.ttf"},
    "script_formal":  {"regular": "GreatVibes-Regular.ttf"},
    "script_casual":  {"regular": "Pacifico-Regular.ttf"},
    "display":        {"regular": "BebasNeue-Regular.ttf"},
    "display_impact": {"regular": "Anton-Regular.ttf"},
}

_SUPERCOOL_FONT_ALIASES = {
    "elegant": "serif_elegant", "playfair": "serif_elegant", "high_contrast_serif": "serif_elegant",
    "garamond": "serif", "body": "serif", "literary": "serif", "old_style_serif": "serif", "book": "serif",
    "cinzel": "serif_display", "fantasy": "serif_display", "epic": "serif_display", "display_serif": "serif_display", "gothic": "serif_display",
    "robotoslab": "slab", "roboto_slab": "slab", "editorial": "slab",
    "inter": "sans", "clean": "sans", "ui": "sans", "modern": "sans", "clean_sans": "sans", "neutral": "sans",
    "montserrat": "sans_geometric", "geometric": "sans_geometric", "geometric_sans": "sans_geometric",
    "oswald": "sans_condensed", "condensed": "sans_condensed", "condensed_sans": "sans_condensed", "thriller": "sans_condensed", "noir": "sans_condensed",
    "dancing": "script", "dancingscript": "script", "handwriting": "script", "romance": "script", "cursive": "script",
    "greatvibes": "script_formal", "great_vibes": "script_formal", "calligraphy": "script_formal", "wedding": "script_formal", "formal": "script_formal",
    "pacifico": "script_casual", "fun": "script_casual", "casual": "script_casual",
    "bebas": "display", "bebasneue": "display", "bebas_neue": "display", "headline": "display", "poster": "display",
    "anton": "display_impact", "impact": "display_impact", "heavy_display": "display_impact", "sports": "display_impact",
}

_SUPERCOOL_WEIGHT_ALIASES = {
    "normal": "regular", "book": "regular", "light": "regular", "thin": "regular", "400": "regular",
    "med": "medium", "semibold": "bold", "semi_bold": "bold", "demibold": "bold", "600": "medium",
    "heavy": "bold", "black": "bold", "extrabold": "bold", "700": "bold", "800": "bold", "900": "bold",
    "oblique": "italic",
}

# Search order when the requested weight isn't present in a family.
_SUPERCOOL_WEIGHT_FALLBACK = {
    "regular": ["regular", "medium", "bold", "italic"],
    "medium":  ["medium", "bold", "regular", "italic"],
    "bold":    ["bold", "medium", "regular", "italic"],
    "italic":  ["italic", "regular", "medium", "bold"],
}

# Absolute last-resort system fonts (always present in the sandbox base image).
_SUPERCOOL_SYSTEM_FALLBACKS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]


def _supercool_resolve_font(filename):
    """Return the first existing absolute path for a bundled font filename."""
    for d in _SUPERCOOL_FONT_DIRS:
        try:
            p = os.path.join(d, filename)
            if os.path.exists(p):
                return p
        except Exception:
            continue
    return None


def pick_font(style="sans", weight="regular"):
    """Resolve a bundled design font to an absolute .ttf path.

    Use with PIL:  ImageFont.truetype(pick_font("serif_elegant", "bold"), 96)

    STYLES (aliases accepted): serif (EB Garamond), serif_elegant (Playfair
    Display), serif_display (Cinzel), slab (Roboto Slab), sans (Inter),
    sans_geometric (Montserrat), sans_condensed (Oswald), script (Dancing
    Script), script_formal (Great Vibes), script_casual (Pacifico),
    display (Bebas Neue), display_impact (Anton).
    WEIGHTS: regular | medium | bold | italic  (semibold/black/etc. map sensibly).

    Always returns a real, existing path — falls back within the family, then to
    Inter, then to a system font, so it can never raise on a typo'd style.
    """
    s = str(style or "sans").strip().lower().replace("-", "_").replace(" ", "_")
    s = _SUPERCOOL_FONT_ALIASES.get(s, s)
    if s not in _SUPERCOOL_FONT_CATALOG:
        s = "sans"
    w = str(weight or "regular").strip().lower().replace("-", "_").replace(" ", "_")
    w = _SUPERCOOL_WEIGHT_ALIASES.get(w, w)
    if w not in _SUPERCOOL_WEIGHT_FALLBACK:
        w = "regular"

    family = _SUPERCOOL_FONT_CATALOG[s]
    for cand in _SUPERCOOL_WEIGHT_FALLBACK[w]:
        fn = family.get(cand)
        if fn:
            path = _supercool_resolve_font(fn)
            if path:
                return path
    # Family files missing on disk → fall back to Inter, then any catalog font.
    for fn in ("Inter-Regular.ttf", "Inter-Bold.ttf"):
        path = _supercool_resolve_font(fn)
        if path:
            return path
    for fam in _SUPERCOOL_FONT_CATALOG.values():
        for fn in fam.values():
            path = _supercool_resolve_font(fn)
            if path:
                return path
    for sys_path in _SUPERCOOL_SYSTEM_FALLBACKS:
        if os.path.exists(sys_path):
            return sys_path
    raise FileNotFoundError(
        "pick_font: no usable font found in " + repr(_SUPERCOOL_FONT_DIRS)
    )


def list_fonts():
    """Return {style: [available weights]} for the bundled design fonts."""
    out = {}
    for style, fam in _SUPERCOOL_FONT_CATALOG.items():
        avail = [w for w, fn in fam.items() if _supercool_resolve_font(fn)]
        if avail:
            out[style] = avail
    return out


def _sc_ffprobe_stream(path):
    """(width, height, fps, vcodec) for a video file's first video stream, or None."""
    import subprocess, json as _json
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height,avg_frame_rate,codec_name,pix_fmt,sample_aspect_ratio",
             "-of", "json", path],
            capture_output=True, text=True)
        st = (_json.loads(r.stdout).get("streams") or [{}])[0]
        w = int(st.get("width") or 0); h = int(st.get("height") or 0)
        fr = st.get("avg_frame_rate") or "0/1"
        try:
            _num, _den = fr.split("/"); fps = (float(_num) / float(_den)) if float(_den) else 0.0
        except Exception:
            fps = 0.0
        # (w, h, fps, codec, pix_fmt, sar) — ALL of these must match for a safe
        # stream-copy concat; differing pix_fmt/SAR/fps can produce a file that
        # ffmpeg accepts (returncode 0) but stutters at the segment joins.
        return w, h, round(fps, 3), st.get("codec_name"), st.get("pix_fmt"), st.get("sample_aspect_ratio")
    except Exception:
        return None


def _sc_has_audio(path):
    """True if the file has at least one audio stream."""
    import subprocess
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0",
                            "-show_entries", "stream=codec_type", "-of", "csv=p=0", path],
                           capture_output=True, text=True)
        return "audio" in (r.stdout or "")
    except Exception:
        return False


def _sc_media_duration(path):
    import subprocess
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=noprint_wrappers=1:nokey=1", path],
                           capture_output=True, text=True)
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def stitch_video(clips, audio=None, output="final_video.mp4", size=None, fps=30,
                 keep_audio=False, preset="veryfast", crf=20):
    """Stitch an ORDERED list of video clips into ONE file — fast, the right way.

    OPTIONAL ADDITIVE FAST-PATH. Use this for a plain ordered concat (optionally
    with a master audio track laid over the whole video). It AUTO-picks the
    fastest safe method: a stream-COPY concat (near-instant) when the clips
    already match, else a SINGLE filter_complex pass (NOT a per-clip re-encode
    loop — that loop runs N full encodes and is needlessly slow). It returns a normal file path you
    can keep processing (burn captions, add an intro card, color-grade, etc.), so
    it never locks you out of custom composition. For crossfades / transitions /
    burned-in captions / overlays / per-scene effects, keep hand-writing ffmpeg —
    this helper only does the plain stitch.

    Args:
      clips: list of video file paths IN FINAL PLAY ORDER (you control ordering —
             build it from your plan/segment_prompts.json by index, not filename).
      audio: optional master audio path (the user's song / a VO) laid over the
             FULL video, REPLACING any per-clip audio. None = no master track.
      output: output filename (workspace-relative).
      size: "WxH" target, e.g. "1080x1920". None => inferred from the first clip.
      fps: target fps used only when re-encoding (the copy path keeps source fps).
      keep_audio: when audio is None, True concatenates each clip's OWN audio
                  (e.g. lip-synced clips that already carry their slice audio);
                  False makes the stitched video silent.
      preset/crf: libx264 params for the re-encode (filter_complex) path only.
                  Use 'ultrafast' if the re-encode path is slow on a big video.

    Returns dict: {"output", "duration", "mode" ('copy'|'filter'), "width", "height"}.
    Does NOT use -shortest, so a master audio track is never truncated; make sure
    your video covers the audio length (extend/add scenes) before relying on it.
    """
    import subprocess, os
    # Dead-take filter is injected separately (_DEAD_TAKE_GUARD_BODY); look it up
    # defensively so this helper still works if that body wasn't injected.
    _dead_filt = globals().get("_sc_filter_dead_clips")
    if globals().get("_DEAD_CLIP_NAMES") and _dead_filt:
        _before = len(clips)
        clips = _dead_filt(clips)
        if len(clips) != _before:
            print("[stitch_video] Dropped %d superseded dead take(s) from the clip list"
                  % (_before - len(clips)))
    if not clips:
        raise ValueError("stitch_video: clips list is empty")
    missing = [c for c in clips if not os.path.exists(c)]
    if missing:
        raise FileNotFoundError("stitch_video: missing clip(s): " + ", ".join(missing[:5]))

    probes = [_sc_ffprobe_stream(c) for c in clips]
    first = next((p for p in probes if p), None)
    if size:
        _wh = str(size).lower().split("x")
        tw, th = int(_wh[0]), int(_wh[1])
    elif first:
        tw, th = first[0], first[1]
    else:
        tw, th = 1080, 1920

    # Stream-copy concat is only SAFE when every clip matches on resolution, fps,
    # codec, pixel format AND aspect ratio — otherwise the copy may succeed but
    # judder/stutter at the joins. Any mismatch → take the (safe) filter path.
    uniform = bool(first) and all(
        p and p[0] == first[0] and p[1] == first[1] and p[2] == first[2]
        and p[3] == first[3] and p[4] == first[4] and p[5] == first[5]
        for p in probes
    )

    def _run(cmd):
        return subprocess.run(cmd, capture_output=True, text=True)

    listfile = "_sc_concat_list.txt"
    with open(listfile, "w") as fh:
        for c in clips:
            fh.write("file '" + os.path.abspath(c) + "'" + chr(10))

    mode = None
    # FAST PATH: stream-copy concat when clips are uniform.
    if uniform:
        silent = "_sc_silent_concat.mp4"
        r = _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile, "-c", "copy", silent])
        if r.returncode == 0:
            if audio:
                r2 = _run(["ffmpeg", "-y", "-i", silent, "-i", audio,
                           "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", output])
            elif keep_audio:
                r2 = _run(["ffmpeg", "-y", "-i", silent, "-c", "copy", "-movflags", "+faststart", output])
            else:
                r2 = _run(["ffmpeg", "-y", "-i", silent, "-an", "-c:v", "copy", "-movflags", "+faststart", output])
            if r2.returncode == 0:
                mode = "copy"

    # FALLBACK: single filter_complex pass (scale+pad each input, ONE encode).
    if mode is None:
        inputs = []
        for c in clips:
            inputs += ["-i", c]
        n = len(clips)
        parts = []
        for i in range(n):
            parts.append(
                "[%d:v]scale=%d:%d:force_original_aspect_ratio=decrease,"
                "pad=%d:%d:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=%d[v%d]"
                % (i, tw, th, tw, th, int(fps), i))
        # Decide how audio is handled on the filter path:
        #   - master `audio` given  -> overlay it (replaces per-clip audio)
        #   - keep_audio (no master) -> concat each clip's OWN audio, but ONLY if
        #     EVERY clip actually has an audio stream (concat a=1 needs a matching
        #     audio per segment). If some clip is silent, we can't cleanly keep
        #     per-clip audio in one pass — warn loudly and produce a silent video
        #     rather than failing or silently losing only some tracks.
        keep_perclip = bool(keep_audio) and not audio
        if keep_perclip and not all(_sc_has_audio(c) for c in clips):
            print("[stitch_video] WARNING: keep_audio requested but not every clip "
                  "has an audio stream — producing SILENT video (overlay a master "
                  "`audio` track instead to guarantee sound).")
            keep_perclip = False

        cmd = ["ffmpeg", "-y"] + inputs
        if audio:
            cmd += ["-i", audio]
        if keep_perclip:
            seg = "".join("[v%d][%d:a]" % (i, i) for i in range(n))
            fc = ";".join(parts) + ";" + seg + ("concat=n=%d:v=1:a=1[outv][outa]" % n)
            cmd += ["-filter_complex", fc, "-map", "[outv]", "-map", "[outa]"]
        else:
            labels = "".join("[v%d]" % i for i in range(n))
            fc = ";".join(parts) + ";" + labels + ("concat=n=%d:v=1:a=0[outv]" % n)
            cmd += ["-filter_complex", fc, "-map", "[outv]"]
            if audio:
                cmd += ["-map", "%d:a:0" % n]
        cmd += ["-c:v", "libx264", "-preset", str(preset), "-crf", str(crf),
                "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
        cmd += (["-c:a", "aac", "-b:a", "192k"] if (audio or keep_perclip) else ["-an"])
        cmd += [output]
        r = _run(cmd)
        if r.returncode != 0:
            raise RuntimeError("stitch_video failed: " + (r.stderr or "")[-700:])
        mode = "filter"

    dur = _sc_media_duration(output)
    op = _sc_ffprobe_stream(output)
    ow, oh = (op[0], op[1]) if op else (tw, th)
    print("[stitch_video] mode=%s clips=%d -> %s (%.2fs, %dx%d)" % (mode, len(clips), output, dur, ow, oh))
    return {"output": output, "duration": round(dur, 3), "mode": mode, "width": ow, "height": oh}


def _bc_probe_wh_dur(path):
    import subprocess, json as _json
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-show_entries", "format=duration",
             "-of", "json", path], capture_output=True, text=True)
        d = _json.loads(r.stdout)
        st = (d.get("streams") or [{}])[0]
        w = int(st.get("width") or 0); h = int(st.get("height") or 0)
        dur = float((d.get("format") or {}).get("duration") or 0.0)
        return w, h, dur
    except Exception:
        return 0, 0, 0.0


def _bc_ts(t):
    """Seconds -> ASS timestamp H:MM:SS.cc (centiseconds)."""
    if t < 0:
        t = 0.0
    h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
    return "%d:%02d:%05.2f" % (h, m, s)


def _bc_wrap(text, max_chars):
    """Greedy word-wrap to <= max_chars per line; returns lines joined with ASS \\N."""
    words = " ".join(str(text).split()).split(" ")
    lines = []; cur = ""
    for w in words:
        cand = (cur + " " + w).strip()
        if len(cand) <= max_chars or not cur:
            cur = cand
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return "\\N".join(lines)


def _bc_escape(text):
    """Escape text for the ASS Text field (it is the LAST field, so commas are
    safe; only brace override-blocks and newlines need handling)."""
    return str(text).replace("\\", "").replace("{", "(").replace("}", ")").replace("\n", " ").strip()


def burn_captions(video_in, segments, output="captioned.mp4", font=None,
                  font_size=None, max_chars_per_line=None, margin_v=None,
                  primary_color="&H00FFFFFF", outline=3, preset="veryfast", crf=20):
    """Burn time-synced captions onto a video in ONE ffmpeg subtitles pass.

    USE THIS instead of hand-writing .ass/.srt or chaining per-line overlay
    filters — those mis-format (the ",0,0,," artifact), overflow the frame edges,
    bunch up, and OOM/timeout on tall video. This builds a correct ASS file with
    matching Format/Dialogue specs, safe-area margins, and automatic wrapping.

    Args:
      video_in: path to the (already assembled) silent or full video.
      segments: list of caption cues. Each item is either a (start, end, text)
                tuple OR a dict {"start","end","text"} — i.e. exactly the
                `segments` returned by audio_generate(mode='transcribe'). Pass the
                FULL set so every spoken line is captioned (no gaps). Text is
                wrapped automatically — do NOT pre-insert \\N.
      output: output filename (workspace-relative).
      font: font family name (libass resolves by name) or None to auto-pick a
            clean bold sans via pick_font.
      font_size/max_chars_per_line/margin_v: optional overrides; sane defaults are
            derived from the video height/width when omitted.
      primary_color: ASS &HAABBGGRR colour (default opaque white).

    Returns dict {"output","duration","cues"}.
    """
    import subprocess, os
    if not os.path.exists(video_in):
        raise FileNotFoundError("burn_captions: video not found: " + str(video_in))

    # Normalize cues to (start, end, text)
    cues = []
    for seg in (segments or []):
        if isinstance(seg, dict):
            s = seg.get("start"); e = seg.get("end"); t = seg.get("text")
        else:
            s, e, t = seg[0], seg[1], seg[2]
        if s is None or e is None or t is None:
            continue
        t = _bc_escape(t)
        if not t:
            continue
        cues.append((float(s), float(e), t))
    if not cues:
        raise ValueError("burn_captions: no usable caption segments")

    W, H, dur = _bc_probe_wh_dur(video_in)
    if not W or not H:
        W, H = 1080, 1920

    # Defaults scaled to the frame. Caption sits in the lower-third safe area.
    if not font_size:
        font_size = max(24, int(round(H * 0.040)))   # ~77px on a 1920-tall video
    if not margin_v:
        margin_v = max(40, int(round(H * 0.10)))     # keep clear of the very bottom
    margin_h = max(40, int(round(W * 0.08)))         # left/right safe area
    if not max_chars_per_line:
        # Rough fit: usable width / (approx glyph advance). Keeps lines on-screen.
        usable = max(1, W - 2 * margin_h)
        max_chars_per_line = max(14, int(usable / (font_size * 0.52)))

    if not font:
        try:
            fp = pick_font("sans_geometric", "bold")
            # libass wants a family NAME, not a path; derive a usable name and
            # also pass fontsdir so the exact file resolves.
            font = os.path.splitext(os.path.basename(fp))[0]
            fonts_dir = os.path.dirname(fp)
        except Exception:
            font = "DejaVu Sans"; fonts_dir = None
    else:
        fonts_dir = None

    # ---- Build a CORRECT ASS file (Format lines MATCH the value lines) --------
    style_fmt = ("Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, "
                 "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, "
                 "Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
                 "MarginL, MarginR, MarginV, Encoding")
    style_line = ("Style: Cap,%s,%d,%s,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,"
                  "1,%d,1,2,%d,%d,%d,1" % (font, font_size, primary_color,
                                           outline, margin_h, margin_h, margin_v))
    ev_fmt = "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
    lines = [
        "[Script Info]", "ScriptType: v4.00+",
        "PlayResX: %d" % W, "PlayResY: %d" % H,
        "WrapStyle: 0", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]", style_fmt, style_line, "",
        "[Events]", ev_fmt,
    ]
    for s, e, t in cues:
        if e <= s:
            e = s + 0.6
        wrapped = _bc_wrap(t, max_chars_per_line)
        # 9 fixed fields then Text (commas in text are safe — Text is last).
        lines.append("Dialogue: 0,%s,%s,Cap,,0,0,0,,%s" % (_bc_ts(s), _bc_ts(e), wrapped))

    ass_path = "_bc_subs.ass"
    with open(ass_path, "w") as fh:
        fh.write("\n".join(lines) + "\n")

    # subtitles filter: escape path for ffmpeg filtergraph; reference the file in cwd.
    vf = "subtitles=" + ass_path
    if fonts_dir:
        vf += ":fontsdir=" + fonts_dir
    cmd = ["ffmpeg", "-y", "-i", video_in, "-vf", vf,
           "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
           "-pix_fmt", "yuv420p", "-c:a", "copy", output]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        # Retry without -c:a copy in case the source had no/incompatible audio.
        cmd2 = ["ffmpeg", "-y", "-i", video_in, "-vf", vf,
                "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
                "-pix_fmt", "yuv420p", "-an", output]
        r2 = subprocess.run(cmd2, capture_output=True, text=True)
        if r2.returncode != 0:
            raise RuntimeError("burn_captions failed: " + (r.stderr or r2.stderr or "")[-700:])
    # Persist cue timings as an underscore-named sidecar (hidden from chat/file
    # lists, fetchable by file_id) so the video preview offers a click-to-seek
    # TRANSCRIPT — parity with video_edit's caption path, for hand-rolled burns.
    try:
        import json as _json
        _stem = os.path.splitext(os.path.basename(output))[0]
        _tr = [{"s": round(s, 3), "e": round(e, 3), "t": t.replace("\\N", " ")} for s, e, t in cues]
        with open("_transcript_%s.json" % _stem, "w") as _tf:
            _json.dump(_tr, _tf, ensure_ascii=False)
    except Exception:
        pass

    odur = _bc_probe_wh_dur(output)[2]
    print("[burn_captions] %d cues -> %s (%.2fs, %dx%d, font=%s/%dpx)" % (
        len(cues), output, odur, W, H, font, font_size))
    return {"output": output, "duration": round(odur, 3), "cues": len(cues)}


def _bt_probe_wh_dur(path):
    import subprocess
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "stream=width,height",
                            "-show_entries", "format=duration",
                            "-of", "default=noprint_wrappers=1", path],
                           capture_output=True, text=True)
        vals = dict(ln.split("=", 1) for ln in (r.stdout or "").strip().splitlines() if "=" in ln)
        return int(float(vals.get("width", 0))), int(float(vals.get("height", 0))), float(vals.get("duration", 0.0))
    except Exception:
        return 0, 0, 0.0


def burn_title(video_in, lines, output="titled.mp4", position="top", font=None,
               start=None, end=None, max_width_frac=0.86, font_frac=0.045,
               preset="veryfast", crf=20):
    """Burn STATIC on-screen text (hook / headline / CTA) onto a video with
    GUARANTEED fit — automatic word-wrap and shrink-to-fit against the frame
    WIDTH, safe margins, pill background, centered.

    USE THIS instead of hand-rolling a PIL/drawtext text burn. Hand-rolled
    burns size text from the frame HEIGHT and center it with x=(W-tw)//2 and
    NO width check, so a long line starts off-frame and clips on both edges
    (a real shipped ad cut the first and last characters off both CTA lines).
    For TIMED subtitle cues use burn_captions; this is for static text.

    Args:
      video_in: input video path.
      lines: one string or a list of strings (each may wrap further to fit).
      output: output filename (give it a persistent, non-underscore name if it
              becomes a video_edit timeline segment).
      position: 'top' (upper-third hook band), 'center', or 'lower'
                (lower-third band, above captions).
      font: font FILE path; default picks a bold geometric sans via pick_font.
      start/end: optional visibility window in seconds (default: whole video).
      max_width_frac: maximum text width as a fraction of the frame width.
      font_frac: starting font size as a fraction of frame height (shrinks to fit).

    Returns {"output","font_size","lines","duration"}.
    """
    import subprocess, os
    from PIL import Image, ImageDraw, ImageFont

    if not os.path.exists(video_in):
        raise FileNotFoundError("burn_title: video not found: " + str(video_in))
    if isinstance(lines, str):
        lines = [lines]
    lines = [str(l).strip() for l in (lines or []) if str(l).strip()]
    if not lines:
        raise ValueError("burn_title: no text given")

    W, H, dur = _bt_probe_wh_dur(video_in)
    if not W or not H:
        W, H = 1080, 1920

    if not font:
        try:
            font = pick_font("sans_geometric", "bold")
        except Exception:
            font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    max_w = int(W * max_width_frac)
    fs = max(18, int(H * font_frac))

    # SHRINK-TO-FIT + WORD-WRAP with MEASURED widths (not estimates): shrink
    # until every wrapped line truly fits max_w and the block stays <= 5 lines.
    probe = Image.new("RGB", (8, 8))
    dmeasure = ImageDraw.Draw(probe)
    def _wrap_at(size):
        f = ImageFont.truetype(font, size)
        out = []
        for text in lines:
            words = text.split()
            cur = ""
            for wd in words:
                cand = (cur + " " + wd).strip()
                if dmeasure.textlength(cand, font=f) <= max_w or not cur:
                    cur = cand
                else:
                    out.append(cur)
                    cur = wd
            if cur:
                out.append(cur)
        widest = max((dmeasure.textlength(l, font=f) for l in out), default=0)
        return out, widest

    while True:
        wrapped, widest = _wrap_at(fs)
        if (widest <= max_w and len(wrapped) <= 5) or fs <= 18:
            break
        fs -= 2

    f = ImageFont.truetype(font, fs)
    line_h = int(fs * 1.45)
    block_h = len(wrapped) * line_h
    if position == "center":
        y0 = max(0, (H - block_h) // 2)
    elif position == "lower":
        y0 = max(0, H - int(H * 0.16) - block_h)
    else:  # top
        y0 = int(H * 0.12)

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    y = y0
    pad = int(fs * 0.4)
    for line in wrapped:
        tw = int(d.textlength(line, font=f))
        x = max(pad, (W - tw) // 2)
        d.rounded_rectangle([x - pad, y - int(pad * 0.6), x + tw + pad, y + fs + int(pad * 0.6)],
                            radius=int(fs * 0.4), fill=(0, 0, 0, 150))
        for dx in (-2, -1, 1, 2):
            for dy in (-2, -1, 1, 2):
                d.text((x + dx, y + dy), line, font=f, fill=(0, 0, 0, 220))
        d.text((x, y), line, font=f, fill=(255, 255, 255, 255))
        y += line_h
    png = "_bt_overlay.png"
    img.save(png)

    ov = "[0:v][1:v]overlay=0:0"
    if start is not None or end is not None:
        a = float(start or 0.0)
        ov += (":enable='between(t,%f,%f)'" % (a, float(end))) if end is not None else (":enable='gte(t,%f)'" % a)
    ov += "[v]"
    r = subprocess.run(["ffmpeg", "-y", "-i", video_in, "-i", png,
                        "-filter_complex", ov, "-map", "[v]", "-map", "0:a?",
                        "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                        "-movflags", "+faststart", output],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("burn_title failed: " + (r.stderr or "")[-600:])
    odur = _bt_probe_wh_dur(output)[2]
    print("[burn_title] %d line(s) @ %dpx -> %s (%.2fs, %dx%d)" % (
        len(wrapped), fs, output, odur, W, H))
    return {"output": output, "font_size": fs, "lines": wrapped, "duration": round(odur, 3)}


def _mv_dur(path):
    import subprocess
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=noprint_wrappers=1:nokey=1", path],
                           capture_output=True, text=True)
        return float((r.stdout or "0").strip())
    except Exception:
        return 0.0


def _mv_mean_db(path):
    """mean_volume (dB) of an audio/video file's audio, or -91.0 if silent/none."""
    import subprocess, re
    try:
        r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
                            "-map", "0:a", "-af", "volumedetect", "-f", "null", "-"],
                           capture_output=True, text=True)
        m = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?)\s*dB", r.stderr or "")
        return float(m.group(1)) if m else -91.0
    except Exception:
        return -91.0


def _mv_mean_db_window(path, ss, dur):
    """mean_volume (dB) of just the [ss, ss+dur] window of a file's audio, or
    -91.0 if silent/unreadable. Used to check the leading/trailing edge of a mix."""
    import subprocess, re
    try:
        r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats",
                            "-ss", "%f" % max(0.0, ss), "-t", "%f" % max(0.05, dur),
                            "-i", path, "-map", "0:a", "-af", "volumedetect",
                            "-f", "null", "-"],
                           capture_output=True, text=True)
        m = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?)\s*dB", r.stderr or "")
        return float(m.group(1)) if m else -91.0
    except Exception:
        return -91.0


def _mv_lufs(path):
    """Integrated loudness (LUFS) of a file's audio via ebur128, or None."""
    import subprocess, re
    try:
        r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
                            "-map", "0:a", "-af", "ebur128=framelog=quiet",
                            "-f", "null", "-"],
                           capture_output=True, text=True)
        m = re.findall(r"I:\s*(-?\d+(?:\.\d+)?)\s*LUFS", r.stderr or "")
        return float(m[-1]) if m else None
    except Exception:
        return None


def _mv_music_gain_auto(vo_lufs, music_lufs, separation_lu=13.0,
                        min_gain=0.04, max_gain=0.5):
    """Linear music gain placing the bed `separation_lu` LU under the voice —
    the same loudness math the video_edit mixer uses. None when either
    measurement is missing/implausible (caller keeps its fallback)."""
    try:
        v = float(vo_lufs); m = float(music_lufs)
    except (TypeError, ValueError):
        return None
    if not (-60.0 < v < 0.0) or not (-60.0 < m < 0.0):
        return None
    gain_db = (v - separation_lu) - m
    gain = 10.0 ** (gain_db / 20.0)
    return max(min_gain, min(max_gain, gain))


def _mv_read_mono(path):
    """Read a WAV as a list of mono float samples in [-1,1] (stdlib only)."""
    import wave, array
    w = wave.open(path, "rb")
    try:
        n = w.getnframes(); ch = w.getnchannels(); sw = w.getsampwidth()
        raw = w.readframes(n)
    finally:
        w.close()
    if sw != 2:
        return []
    a = array.array("h")
    a.frombytes(raw)
    data = list(a)
    if ch == 2:
        data = [(data[i] + data[i + 1]) * 0.5 for i in range(0, len(data) - 1, 2)]
    inv = 1.0 / 32768.0
    return [s * inv for s in data]


def _mv_pearson(xs, ys):
    """Pearson correlation of two equal-length sequences (abs value returned)."""
    n = min(len(xs), len(ys))
    if n < 100:
        return 0.0
    xs = xs[:n]; ys = ys[:n]
    sx = sum(xs); sy = sum(ys)
    mx = sx / n; my = sy / n
    cov = sxx = syy = 0.0
    for i in range(n):
        dx = xs[i] - mx; dy = ys[i] - my
        cov += dx * dy; sxx += dx * dx; syy += dy * dy
    if sxx <= 0 or syy <= 0:
        return 0.0
    return abs(cov / ((sxx ** 0.5) * (syy ** 0.5)))


def _mv_pearson_signed(xs, ys):
    """SIGNED Pearson of two equal-length sequences. The sign matters for the
    envelope rescue below: a mix whose voice is PRESENT peaks WITH the speech
    (positive), while the classic dropped-VO bug (the voiceover keys the music
    duck but never reaches the amix) makes the music DIP where the speech is —
    a NEGATIVE envelope correlation that abs() would wrongly count as a match."""
    n = min(len(xs), len(ys))
    if n < 8:
        return 0.0
    xs = xs[:n]; ys = ys[:n]
    mx = sum(xs) / n; my = sum(ys) / n
    cov = sxx = syy = 0.0
    for i in range(n):
        dx = xs[i] - mx; dy = ys[i] - my
        cov += dx * dy; sxx += dx * dx; syy += dy * dy
    if sxx <= 0 or syy <= 0:
        return 0.0
    return cov / ((sxx ** 0.5) * (syy ** 0.5))


def _mv_env50(xs, sr=8000):
    """50 Hz RMS envelope (syllable-rate; robust to codec, gain, small shifts)."""
    hop = max(1, int(sr / 50.0))
    out = []; i = 0; ln = len(xs)
    while i < ln:
        seg = xs[i:i + hop]
        if not seg:
            break
        s = 0.0
        for v in seg:
            s += v * v
        out.append((s / len(seg)) ** 0.5)
        i += hop
    return out


def _mv_env_lag_corr(out_samples, vo_samples, sr=8000, max_lag_s=1.5):
    """Best SIGNED envelope correlation over +-max_lag_s and its lag in ms.

    Rescue metric for the VO verify: the sample-level fixed-offset Pearson
    reads ~0 whenever the mixed voice sits even a few ms off the stem
    (container edit lists / encoder priming / a deliberate small VO delay) — a
    verified false 'no voice' verdict on a perfectly good mix (measured: fixed
    -0.008 vs 0.983 offset-tolerant at 405 ms on a real delivered preview).
    Envelopes compare syllable ENERGY patterns, so they tolerate misalignment,
    and the SIGNED correlation keeps the classic duck-keyed dropped-VO bug
    failing (its envelope correlation is negative — see _mv_pearson_signed)."""
    ef = _mv_env50(out_samples, sr)
    ed = _mv_env50(vo_samples, sr)
    if len(ef) < 10 or len(ed) < 10:
        return 0.0, 0.0
    max_lag = int(max_lag_s * 50.0)
    best = -1.0; best_lag = 0
    for lag in range(-max_lag, max_lag + 1):
        xs = []; ys = []
        for i in range(len(ef)):
            j = i - lag
            if 0 <= j < len(ed):
                xs.append(ef[i]); ys.append(ed[j])
        if len(xs) >= 8:
            c = _mv_pearson_signed(xs, ys)
            if c > best:
                best = c; best_lag = lag
    return best, (best_lag / 50.0) * 1000.0


def mix_voiceover(video_in, voiceover, music=None, output="final_with_audio.mp4",
                  vo_start=0.0, vo_gain=1.0, music_gain=None, duck=True,
                  fade=2.0, verify=True, min_corr=0.12, keep_native="auto",
                  accept_quiet_music=False):
    """Mux a voiceover (+ optional music bed) onto a video — correctly, and VERIFY
    the voice is actually audible in the result.

    USE THIS instead of hand-writing the adelay/sidechaincompress/amix graph.
    Hand-rolled VO+music mixes routinely ship a video with NO voice (the VO link
    gets consumed by the ducking sidechain and never reaches the amix). This
    helper splits the VO so it both keys the duck AND is mixed in, then confirms
    the voice survived by correlating the final mix against the VO waveform.

    Args:
      video_in: assembled video to lay audio onto. Its own AUDIBLE audio
                (dialogue! ambience!) is KEPT in the mix by default, ducked
                under the VO — the old replace behavior silently ERASED spoken
                performances when a narrator was added (real shipped films
                delivered narration-only over clips generated WITH dialogue).
      voiceover: path to the narration/VO audio (REQUIRED).
      music: optional background music path (looped/trimmed to the video length).
      output: output filename (workspace-relative).
      vo_start: seconds before the VO begins (e.g. an 11s music-only intro).
      vo_gain: VO level (1.0 = unchanged).
      music_gain: OMIT (None, the default) and the helper MEASURES both stems
            and levels the bed ~13 LU under the voice — audible but never
            fighting it. A pinned constant on a quietly-mastered score buries
            the music (the 'music is barely there' defect); an explicit value
            that lands the bed >16 LU under the voice is therefore raised to
            the audibility target unless accept_quiet_music=True. 0 = mute
            the bed (always honored).
      accept_quiet_music: True keeps a deliberately near-silent explicit
            music_gain even when it measures as buried under the voice.
      duck: True ducks the bed (music + kept native audio) under the VO via
            sidechaincompress; False keeps the bed at constant level.
      fade: seconds of audio fade-in/out applied to the MUSIC BED only (never to
            the voice or the kept native audio — fading those silences words).
      verify: True (default) raises RuntimeError if the VO is NOT detectable in
              the output — turning a silently-broken render into a hard failure.
      min_corr: correlation threshold for "VO present" (lower = more lenient).
      keep_native: 'auto' (default) keeps the video's own audio when it is
                   audible (mean volume above -60 dB); True forces keep;
                   False restores the legacy replace behavior.

    Returns dict {"output","duration","vo_present","vo_correlation","mode",
    "native_kept"}.
    """
    import subprocess, os
    # Dead-take guard is injected separately (_DEAD_TAKE_GUARD_BODY); look it up
    # defensively so this helper still works if that body wasn't injected.
    _dead_guard = globals().get("_sc_guard_not_dead_take")
    if _dead_guard:
        _dead_guard(video_in, "mix_voiceover")
    if not os.path.exists(video_in):
        raise FileNotFoundError("mix_voiceover: video not found: " + str(video_in))
    if not voiceover or not os.path.exists(voiceover):
        raise FileNotFoundError("mix_voiceover: voiceover not found: " + str(voiceover))

    total = _mv_dur(video_in)
    if total <= 0:
        raise ValueError("mix_voiceover: could not read video duration")

    # Guard 1: the VO stem itself must not be silent (catches a dead TTS file).
    if _mv_mean_db(voiceover) <= -80.0:
        raise RuntimeError("mix_voiceover: the voiceover file appears SILENT "
                           "(mean_volume <= -80 dB) — regenerate the narration.")

    # LOUDNESS-AWARE BED LEVEL (same policy as the video_edit mixer): with no
    # explicit music_gain, MEASURE both stems and place the bed ~13 LU under
    # the voice — a fixed constant on a quietly-mastered AI score buried the
    # music entirely (the 'music is barely there' defect across real shipped
    # films). An explicit gain that measures >16 LU under the voice is raised
    # to the target too — unless accept_quiet_music=True (deliberate
    # subliminal bed) or gain==0 (mute, always honored).
    music_note = None
    if music and os.path.exists(music):
        _vo_I = _mv_lufs(voiceover)
        _m_I = _mv_lufs(music)
        import math as _math

        def _sep_at(gain):
            if _vo_I is None or _m_I is None:
                return None
            return _vo_I - (_m_I + 20.0 * _math.log10(max(1e-6, float(gain))))

        if music_gain is None:
            _auto = _mv_music_gain_auto(_vo_I, _m_I)
            if _auto is not None:
                music_gain = _auto
                # Report the ACHIEVED separation — the gain clamp can stop
                # short of the 13 LU target on a very quiet bed.
                music_note = ("bed auto-leveled: voice %.1f LUFS, music %.1f LUFS "
                              "-> gain %.3f (~%.0f LU under the voice)"
                              % (_vo_I, _m_I, music_gain, _sep_at(music_gain)))
            else:
                music_gain = 0.22  # measurement failed -> legacy default
        elif float(music_gain) > 0.0 and not accept_quiet_music:
            _sep = _sep_at(music_gain)
            if _sep is not None and _sep > 16.0:
                _auto = _mv_music_gain_auto(_vo_I, _m_I)
                if _auto is not None and _auto > float(music_gain):
                    music_gain = _auto
                    music_note = (
                        "the explicit music_gain that was set would sit the bed "
                        "~%.0f LU under the voice (effectively inaudible) — "
                        "raised to %.3f (now ~%.0f LU under). Pass "
                        "accept_quiet_music=True to keep a deliberately quiet bed."
                        % (_sep, music_gain, _sep_at(music_gain)))
    if music_gain is None:
        music_gain = 0.22

    def _run(cmd):
        return subprocess.run(cmd, capture_output=True, text=True)

    # 1) VO delayed to vo_start and padded/trimmed to the full video length.
    vo_delayed = "_mv_vo.wav"
    ms = int(round(max(0.0, vo_start) * 1000))
    r = _run(["ffmpeg", "-y", "-i", voiceover,
              "-af", "adelay=%d:all=1,apad,atrim=0:%f,volume=%f" % (ms, total, vo_gain),
              "-ar", "44100", "-ac", "2", vo_delayed])
    if r.returncode != 0:
        raise RuntimeError("mix_voiceover: VO prep failed: " + (r.stderr or "")[-500:])

    # NATIVE-AUDIO PRESERVATION: the video's own soundtrack (spoken dialogue,
    # ambience) joins the bed under the VO instead of being silently replaced.
    # 'auto' keeps it only when it is actually audible, so silent stitches and
    # video-only concats behave exactly as before.
    native_kept = False
    native_bed = None
    if keep_native == "auto":
        _keep = _mv_mean_db(video_in) > -60.0
    else:
        _keep = bool(keep_native)
    if _keep:
        native_bed = "_mv_native.wav"
        r = _run(["ffmpeg", "-y", "-i", video_in,
                  "-map", "0:a:0", "-af", "apad,atrim=0:%f" % total,
                  "-ar", "44100", "-ac", "2", native_bed])
        if r.returncode != 0 or not os.path.exists(native_bed):
            native_bed = None  # no usable audio stream -> legacy behavior
        else:
            native_kept = True

    mix = "_mv_mix.wav"
    if music and os.path.exists(music):
        music_bed = "_mv_music.wav"
        r = _run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", music,
                  "-t", "%f" % total, "-ar", "44100", "-ac", "2", music_bed])
        if r.returncode != 0:
            raise RuntimeError("mix_voiceover: music prep failed: " + (r.stderr or "")[-500:])
        if native_bed:
            # Pre-mix music (gained + faded) with the kept native audio (unity,
            # un-faded — fading dialogue loses words) into ONE bed, then run the
            # standard duck graph on it at unity gain.
            _combined = "_mv_bed.wav"
            r = _run(["ffmpeg", "-y", "-i", music_bed, "-i", native_bed,
                      "-filter_complex",
                      "[0:a]volume=%f,afade=t=in:st=0:d=%f,afade=t=out:st=%f:d=%f[m];"
                      "[m][1:a]amix=inputs=2:duration=longest:normalize=0[a]"
                      % (music_gain, fade, max(0.0, total - fade), fade),
                      "-map", "[a]", "-ar", "44100", "-ac", "2", _combined])
            if r.returncode != 0:
                raise RuntimeError("mix_voiceover: bed pre-mix failed: " + (r.stderr or "")[-500:])
            music_bed = _combined
            _bed_gain, _bed_fade = 1.0, 0.0  # already leveled and faded above
        else:
            _bed_gain, _bed_fade = music_gain, fade
        _fade_expr = (
            ",afade=t=in:st=0:d=%f,afade=t=out:st=%f:d=%f"
            % (_bed_fade, max(0.0, total - _bed_fade), _bed_fade)
        ) if _bed_fade > 0.0 else ""
        if duck:
            # asplit the VO: one copy KEYS the sidechain duck, the other is MIXED
            # in. (Reusing a single [voc] label here is THE bug this helper kills.)
            #
            # The fade is applied to the MUSIC bed ONLY (before the duck/amix), never
            # to the final mix — fading the combined output silences the opening and
            # closing WORDS of the voice. The voice stays at full level end-to-end.
            filt = (
                "[1:a]volume=%f,asplit=2[voc_sc][voc_mix];"
                "[0:a]volume=%f%s[mus];"
                "[mus][voc_sc]sidechaincompress=threshold=0.04:ratio=9:attack=8:release=320[duck];"
                "[duck][voc_mix]amix=inputs=2:duration=longest:normalize=0[a]"
                % (vo_gain, _bed_gain, _fade_expr)
            )
        else:
            # Fade the music bed only; keep the voice un-faded so no words are lost.
            filt = (
                "[0:a]volume=%f%s[mus];"
                "[1:a]volume=%f[voc];"
                "[mus][voc]amix=inputs=2:duration=longest:normalize=0[a]"
                % (_bed_gain, _fade_expr, vo_gain)
            )
        r = _run(["ffmpeg", "-y", "-i", music_bed, "-i", vo_delayed,
                  "-filter_complex", filt, "-map", "[a]", "-ar", "44100", "-ac", "2", mix])
        if r.returncode != 0:
            raise RuntimeError("mix_voiceover: mix failed: " + (r.stderr or "")[-500:])
    elif native_bed:
        # No music, but the video HAS audible native audio (dialogue/ambience):
        # duck it under the VO exactly like a music bed at unity gain.
        if duck:
            filt = (
                "[1:a]volume=%f,asplit=2[voc_sc][voc_mix];"
                "[0:a]anull[nat];"
                "[nat][voc_sc]sidechaincompress=threshold=0.04:ratio=9:attack=8:release=320[duck];"
                "[duck][voc_mix]amix=inputs=2:duration=longest:normalize=0[a]" % vo_gain
            )
        else:
            filt = (
                "[0:a]anull[nat];[1:a]volume=%f[voc];"
                "[nat][voc]amix=inputs=2:duration=longest:normalize=0[a]" % vo_gain
            )
        r = _run(["ffmpeg", "-y", "-i", native_bed, "-i", vo_delayed,
                  "-filter_complex", filt, "-map", "[a]", "-ar", "44100", "-ac", "2", mix])
        if r.returncode != 0:
            raise RuntimeError("mix_voiceover: native mix failed: " + (r.stderr or "")[-500:])
    else:
        mix = vo_delayed  # VO only

    # 1b) MASTER CEILING — guarantee the mix sits ~1 dB below full scale so it can
    # never clip. amix above uses normalize=0 (it SUMS levels) and applied NO output
    # ceiling, so a near-full-scale VO + the music bed could push peaks to/over 0 dBFS
    # (a real shipped defect: ad mixes flagged "likely digital clipping" at peak 0.0).
    # A look-ahead brick-wall limiter at -1 dBFS (limit=0.89) only attenuates peaks
    # that would exceed the ceiling; level=disabled means it does NOT auto-gain quiet
    # audio up (we want headroom, not loudness maximization), so it never changes the
    # voice/music balance or breaks the VO-correlation check below. Fail-open: if the
    # limiter pass fails for any reason, fall through with the un-limited mix.
    _mastered = "_mv_master.wav"
    _rm = _run(["ffmpeg", "-y", "-i", mix, "-af", "alimiter=limit=0.89:level=false",
                "-ar", "44100", "-ac", "2", _mastered])
    if _rm.returncode == 0 and os.path.exists(_mastered) and os.path.getsize(_mastered) > 0:
        mix = _mastered

    # 2) Mux audio onto the video (copy video to keep captions/quality).
    r = _run(["ffmpeg", "-y", "-i", video_in, "-i", mix,
              "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
              "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
              "-shortest", output])
    if r.returncode != 0:
        # Fall back to re-encoding the video if stream-copy refused the source.
        r = _run(["ffmpeg", "-y", "-i", video_in, "-i", mix,
                  "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264",
                  "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                  "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                  "-shortest", output])
        if r.returncode != 0:
            raise RuntimeError("mix_voiceover: mux failed: " + (r.stderr or "")[-500:])

    # 3) VERIFY the VO survived: correlate the output audio against the VO
    # waveform inside the speech window. Music is uncorrelated with the VO, so a
    # low correlation here means the voice did not make it into the mix.
    corr = None
    if verify:
        vo_dur = max(0.0, _mv_dur(voiceover))
        win = min(15.0, vo_dur) if vo_dur else 15.0
        ck_out = "_mv_ck_out.wav"; ck_vo = "_mv_ck_vo.wav"
        _run(["ffmpeg", "-y", "-ss", "%f" % vo_start, "-t", "%f" % win, "-i", output,
              "-map", "0:a:0", "-ac", "1", "-ar", "8000", ck_out])
        _run(["ffmpeg", "-y", "-ss", "%f" % vo_start, "-t", "%f" % win, "-i", vo_delayed,
              "-ac", "1", "-ar", "8000", ck_vo])
        try:
            _out_s = _mv_read_mono(ck_out); _vo_s = _mv_read_mono(ck_vo)
            corr = _mv_pearson(_out_s, _vo_s)
            # OFFSET-TOLERANT RESCUE: the fixed-offset sample Pearson reads ~0
            # whenever the mixed voice sits even a few ms off the stem (container
            # edit lists / AAC priming / a small deliberate VO delay) — a verified
            # FALSE 'no voice' on a good mix (fixed -0.008 vs 0.983 at 405 ms lag
            # on a real delivered preview; the helper then failed 3x and pushed
            # the agent into hand-rolling the exact graph this helper exists to
            # prevent). Before failing, scan +-1.5 s of lag on the 50 Hz RMS
            # envelopes: a PRESENT voice correlates strongly and POSITIVELY at
            # its true lag; the classic dropped-VO bug (voice keys the duck but
            # never reaches the amix) correlates NEGATIVELY (music dips at
            # speech), so it still fails.
            if corr is not None and corr < min_corr:
                _env_c, _env_lag = _mv_env_lag_corr(_out_s, _vo_s)
                # 0.6: a PRESENT voice dominates the mix envelope (measured 0.96
                # on a real lagged-but-good mix); the max-over-lags scan can
                # inflate a spurious peak on a voiceless ducked bed to ~0.35
                # (measured on a rebuilt dropped-VO output), so the bar sits
                # well above spurious and well below genuine.
                if _env_c >= 0.6:
                    print("[mix_voiceover] VO verified via offset-tolerant envelope "
                          "match: correlation %.3f at %.0f ms lag (fixed-offset read "
                          "%.3f — misalignment, not a dropped voice)."
                          % (_env_c, _env_lag, corr))
                    corr = _env_c
        except Exception as _e:
            corr = None
        if corr is not None and corr < min_corr:
            raise RuntimeError(
                "mix_voiceover: VERIFY FAILED — the voiceover is NOT audible in '%s' "
                "(VO correlation %.3f < %.3f). The mix dropped the voice; do not deliver "
                "this file. (Use this helper rather than a hand-rolled amix.)"
                % (output, corr, min_corr))

        # EDGE-AUDIBILITY GUARD: a fade applied to the VOICE (not just the music)
        # silences the opening/closing WORDS. Compare the output's leading and
        # trailing edge to the VO stem in the same region; if the VO clearly has
        # speech there but the output edge is much quieter, the mix attenuated the
        # voice. Warn (don't raise) — a naturally-quiet intro is a benign false
        # positive, and the structural fix (fade music only) already prevents it.
        try:
            _edge = min(2.0, max(0.6, (vo_dur or total) * 0.08))
            _speech_end = vo_start + (vo_dur or total)
            for _label, _ss in (("intro", vo_start),
                                ("outro", max(vo_start, _speech_end - _edge))):
                _out_db = _mv_mean_db_window(output, _ss, _edge)
                _vo_db = _mv_mean_db_window(vo_delayed, _ss, _edge)
                # Only flag when the VO stem clearly has speech in that edge window.
                if _vo_db > -45.0 and _out_db < _vo_db - 12.0:
                    print(
                        "[mix_voiceover] WARNING: %s edge of the VOICE looks attenuated "
                        "in '%s' (output %.1f dB vs voiceover %.1f dB over %.1fs). The "
                        "first/last words may be inaudible — fade the MUSIC bed only, "
                        "not the final mix." % (_label, output, _out_db, _vo_db, _edge)
                    )
        except Exception:
            pass

    dur = _mv_dur(output)
    _mode = "vo"
    if music:
        _mode += "+music"
    if native_kept:
        _mode += "+native"
    if _mode == "vo":
        _mode = "vo-only"
    print("[mix_voiceover] %s (%.2fs) vo_start=%.1fs music=%s native_kept=%s duck=%s vo_corr=%s%s" % (
        output, dur, vo_start, bool(music), native_kept, bool(duck),
        ("%.3f" % corr) if corr is not None else "n/a",
        (" | " + music_note) if music_note else ""))
    return {"output": output, "duration": round(dur, 3),
            "vo_present": (corr is None or corr >= min_corr),
            "vo_correlation": corr, "mode": _mode, "native_kept": native_kept,
            "music_gain_used": (round(float(music_gain), 3) if music else None),
            **({"music_note": music_note} if music_note else {})}


def check_lipsync_alignment(final_video, driver_audio, window_start=0.0,
                            window_dur=None, max_lag_ms=150.0, min_corr=0.5,
                            search_seconds=3.0):
    """Verify a lip-synced PERFORMANCE scene's mouth still matches the audio in
    the FINAL assembled video.

    Catches the classic desync: a synced clip's mouth is aligned to its OWN
    audio, but the assembly stripped that audio (`-an`) and laid a SEPARATE
    continuous VO over the window, so the words land at a different offset than
    the mouth. This cross-correlates the FINAL's audio inside the scene window
    against the synced clip's own (mouth-aligned) audio and reports the lag.

    Args:
      final_video: the assembled, mixed deliverable.
      driver_audio: the scene's synced clip (its embedded audio IS the mouth
                    driver) OR the exact VO slice it was lip-synced to.
      window_start: where the performance scene starts in the final timeline (s).
      window_dur: scene window length (s); defaults to the driver's duration.
      max_lag_ms: |lag| above this = an audible desync (aligned=False).
      min_corr: below this the two audios aren't the same content (can't judge).
      search_seconds: max offset to search for the alignment peak.

    Returns {"checked","aligned","lag_ms","correlation"}. FAIL-OPEN: any error
    returns checked=False, aligned=True — a tool hiccup never blocks delivery.
    """
    import subprocess, os, tempfile
    res = {"checked": False, "aligned": True, "lag_ms": None, "correlation": None}
    tmp = None
    try:
        if not (final_video and os.path.exists(final_video)):
            return res
        if not (driver_audio and os.path.exists(driver_audio)):
            return res
        SR = 8000
        if window_dur is None:
            window_dur = _mv_dur(driver_audio) or 0.0
        if not window_dur or window_dur < 0.4:
            return res
        tmp = tempfile.mkdtemp(prefix="_lsa_")
        fw = os.path.join(tmp, "fin.wav"); dw = os.path.join(tmp, "drv.wav")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
                        "-ss", "%f" % max(0.0, window_start), "-t", "%f" % window_dur,
                        "-i", final_video, "-map", "0:a:0", "-ac", "1", "-ar", str(SR), fw],
                       capture_output=True, text=True, timeout=60)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-t", "%f" % window_dur,
                        "-i", driver_audio, "-ac", "1", "-ar", str(SR), dw],
                       capture_output=True, text=True, timeout=60)
        if not (os.path.exists(fw) and os.path.exists(dw)):
            return res
        fa = _mv_read_mono(fw); da = _mv_read_mono(dw)
        if len(fa) < SR // 2 or len(da) < SR // 2:
            return res

        # 50 Hz RMS envelope — captures syllable timing and is robust to codec /
        # gain / channel differences between the mix and the raw slice.
        fps_env = 50.0
        hop = int(SR / fps_env)

        def _env(x):
            out = []; i = 0; ln = len(x)
            while i < ln:
                seg = x[i:i + hop]
                if not seg:
                    break
                s = 0.0
                for v in seg:
                    s += v * v
                out.append((s / len(seg)) ** 0.5)
                i += hop
            return out

        ef = _env(fa); ed = _env(da)
        n = min(len(ef), len(ed))
        if n < 8:
            return res
        max_lag = int(round(search_seconds * fps_env))

        def _corr_at(lag):
            xs = []; ys = []
            for i in range(n):
                j = i - lag
                if 0 <= j < len(ed) and i < len(ef):
                    xs.append(ef[i]); ys.append(ed[j])
            return _mv_pearson(xs, ys) if len(xs) >= 8 else 0.0

        best_lag = 0; best = -1.0
        for lag in range(-max_lag, max_lag + 1):
            c = _corr_at(lag)
            if c > best:
                best = c; best_lag = lag
        lag_ms = (best_lag / fps_env) * 1000.0
        # "Inconclusive" (correlation too low to judge — e.g. the wrong driver was
        # passed, or the window is music-only/silent) must NOT raise a false desync
        # alarm. Only report aligned=False on a CONFIDENT desync (high corr at a lag
        # beyond the threshold). conclusive=False tells the agent to recheck inputs.
        conclusive = best >= min_corr
        aligned = (not conclusive) or (abs(lag_ms) <= max_lag_ms)
        res = {"checked": True, "aligned": bool(aligned), "conclusive": bool(conclusive),
               "lag_ms": round(lag_ms, 1), "correlation": round(best, 4)}
        _f = os.path.basename(final_video)
        if not conclusive:
            print("[check_lipsync_alignment] %s @%.2fs: correlation %.3f too low to "
                  "judge (inconclusive, not flagged) — confirm driver_audio is THIS "
                  "scene's own synced clip/slice." % (_f, window_start, best))
        elif not aligned:
            print("[check_lipsync_alignment] TIMING DESYNC: %s @%.2fs — the audio is "
                  "offset from the synced clip's own audio by %.0f ms (corr %.2f). The "
                  "window's audio is NOT the synced clip's own audio at zero offset. "
                  "On a video_edit timeline: re-issue video_edit(action='lip_sync', "
                  "lipsync=[{index: N}]) WITHOUT audio — the tool auto-slices the "
                  "master at the segment's true playback window; do NOT hand-cut an "
                  "offset-adjusted slice to chase this number. Off-timeline: "
                  "re-assemble keeping this scene's own audio (do NOT overlay a "
                  "separate VO across it)." % (_f, window_start, lag_ms, best))
        else:
            print("[check_lipsync_alignment] TIMING OK: %s @%.2fs — audio lag %.0f ms "
                  "(corr %.2f). This measures TIMING ONLY: it does NOT assess "
                  "mouth-shape/viseme quality, so never tell the user the lips "
                  "'match' or are 'verified' based on this check. If the user says "
                  "the lip-sync looks wrong, that is a generation-quality issue this "
                  "check cannot see — do not cite these numbers as a rebuttal."
                  % (_f, window_start, lag_ms, best))
        return res
    except Exception:
        return res
    finally:
        if tmp:
            try:
                import shutil; shutil.rmtree(tmp, ignore_errors=True)
            except Exception:
                pass


def check_audio_continuity(final_video, min_active_fraction=0.6,
                           max_gap_s=1.5, noise_db=-45.0, min_silence_s=0.4):
    """Confirm a finished MUSIC / continuous-audio video actually plays sound the
    whole way through — catches the "no music / huge gaps between vocals" defect
    where a lip-synced music video shipped with vocals-only or gappy audio (the
    instrumental stripped, silence between sung phrases).

    Runs ffmpeg silencedetect over the FINAL cut and reports how much of the
    timeline is silent and the longest silent gap. For a song the audio should be
    near-continuous, so a large silent fraction or a multi-second gap means the
    music/track is missing or got stripped during assembly.

    Args:
      final_video: the assembled, mixed deliverable.
      min_active_fraction: fail below this fraction of the timeline carrying sound.
      max_gap_s: fail if any single silent gap is longer than this.
      noise_db: level below which audio counts as silence (silencedetect noise=).
      min_silence_s: shortest silence to report (silencedetect d=).

    Returns {"checked","ok","duration_s","total_silence_s","active_fraction",
    "longest_gap_s","gaps"}. FAIL-OPEN: any error returns checked=False, ok=True
    so a tool hiccup never blocks delivery.
    """
    import subprocess, os, re
    res = {"checked": False, "ok": True, "duration_s": None, "total_silence_s": None,
           "active_fraction": None, "longest_gap_s": None, "gaps": []}
    try:
        if not (final_video and os.path.exists(final_video)):
            return res
        dur = _mv_dur(final_video)
        if not dur or dur < 0.5:
            return res
        r = subprocess.run(
            ["ffmpeg", "-hide_banner", "-nostats", "-i", final_video,
             "-map", "0:a:0", "-af",
             "silencedetect=noise=%gdB:d=%g" % (noise_db, min_silence_s),
             "-f", "null", "-"],
            capture_output=True, text=True, timeout=120)
        log = r.stderr or ""
        starts = [float(m) for m in re.findall(r"silence_start:\s*(-?\d+(?:\.\d+)?)", log)]
        ends = [float(m) for m in re.findall(r"silence_end:\s*(-?\d+(?:\.\d+)?)", log)]
        gaps = []
        for i, s in enumerate(starts):
            e = ends[i] if i < len(ends) else dur
            gaps.append((max(0.0, s), min(dur, e)))
        total_sil = sum(max(0.0, e - s) for s, e in gaps)
        longest = max((e - s for s, e in gaps), default=0.0)
        active = max(0.0, 1.0 - (total_sil / dur)) if dur else 0.0
        ok = (active >= min_active_fraction) and (longest <= max_gap_s)
        res = {"checked": True, "ok": bool(ok), "duration_s": round(dur, 2),
               "total_silence_s": round(total_sil, 2),
               "active_fraction": round(active, 3),
               "longest_gap_s": round(longest, 2),
               "gaps": [[round(s, 2), round(e, 2)] for s, e in gaps]}
        _f = os.path.basename(final_video)
        if not ok:
            print("[check_audio_continuity] GAPPY/SILENT AUDIO: %s — only %.0f%% of the "
                  "%.1fs timeline has sound (longest silent gap %.1fs). For a music video "
                  "this means the music/track is missing or was stripped: keep each synced "
                  "clip's OWN full-mix audio when stitching, or lay the user's CONTINUOUS "
                  "full song over the whole cut, then re-check." % (_f, active * 100, dur, longest))
        else:
            print("[check_audio_continuity] OK: %s — audio plays continuously (%.0f%% active, "
                  "longest gap %.1fs)." % (_f, active * 100, longest))
        return res
    except Exception:
        return res


def slice_master_audio_for_lipsync(master_audio, ordered_clips, performance_clips,
                                   out_dir=".", prefix="_perfslice_", transitions=None):
    """MASTER-AUDIO lip-sync alignment (music OR spoken, generated OR uploaded).
    Cut each PERFORMANCE clip's lip-sync driver slice at the clip's ACTUAL
    cumulative offset in the FINAL ASSEMBLY ORDER (measured with ffprobe) — NEVER
    a planned/lyric/script offset.

    Why: you will lay ONE continuous master track over the whole assembled cut
    (video_edit set_audio audio_mode='music_master'). For the synced mouths to
    line up, each clip's driver slice must come from EXACTLY the audio position the
    clip ends up occupying. Slicing at planned offsets drifts whenever real clip
    durations differ from the plan (they almost always do).

    NOTE: if instead you keep each performance clip's OWN audio and lay the master
    track ONLY under the B-roll/non-performance scenes (the VO-narration lane),
    you don't need this helper — there's no continuous overlay across a synced
    window to drift. Use this ONLY when laying a continuous master over everything.

    Args:
      master_audio: the master track file (the SAME file you lay as music_master) —
        a song or an uploaded spoken/VO track.
      ordered_clips: clip filenames in the EXACT order you will assemble
        (the from_clips / stitch_video order). Use the BASE (pre-lipsync) names;
        lip_sync preserves duration so offsets are unchanged. When the workspace
        EDL (edit_project.json) TRIMS a clip (in/out), offsets automatically use
        the trimmed played length — slice AFTER setting your trims so they're
        visible here.
      performance_clips: the subset of ordered_clips that are lip-sync performance
        scenes (filenames).
      transitions: OPTIONAL list aligned to ordered_clips giving the CROSSFADE
        overlap (seconds) INTO each clip (the xfade/acrossfade duration at the
        boundary BEFORE that clip; 0 / None for a hard cut). A crossfade overlaps
        adjacent clips, so the rendered timeline is SHORTER than the plain duration
        sum and every clip after a crossfade lands earlier — pass this so the
        offsets stay correct. Index 0 is ignored (nothing precedes the first clip).
        Omit it ONLY when all boundaries are hard cuts (recommended around
        performance clips anyway — a crossfade blurs the synced mouth).
    Returns: {clip_basename: slice_path} for each performance clip — feed each as
      that clip's lip_sync audio_file. Order from_clips IDENTICALLY afterward.
    """
    import os, subprocess
    def _dur(p):
        try:
            r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                "format=duration", "-of", "default=nw=1:nk=1", p],
                               capture_output=True, text=True)
            return float((r.stdout or "0").strip() or 0.0)
        except Exception:
            return 0.0
    def _overlap(i):
        # crossfade overlap (seconds) INTO clip i; 0 for the first clip / hard cuts.
        if not transitions or i == 0 or i >= len(transitions):
            return 0.0
        try:
            return max(0.0, float(transitions[i] or 0.0))
        except Exception:
            return 0.0
    # EDL AUTO-DERIVE (crossfades + trims): when this workspace has an EDL
    # (edit_project.json) covering these clips, its timeline facts outrank the
    # raw files. Two facts matter for offsets:
    #   - CROSSFADES: a fade INTO a clip pulls it (and everything after)
    #     earlier than the plain duration sum (a real shipped lip-sync drift).
    #     Derived only when `transitions` was omitted; pass an explicit list
    #     (e.g. all zeros) to override.
    #   - TRIMS: a segment with in/out plays SHORTER than its source file, so
    #     every LATER clip lands earlier than the file-duration sum. Music-video
    #     flash coverage makes this routine (providers generate >=~3s clips,
    #     performance flashes are <=~2.5s, so mid-timeline trims are the norm)
    #     — ignoring trims would silently shift every later slice.
    # Fail-open: no EDL / unparseable -> raw file durations, as before.
    _win_by_base = {}
    try:
        import json as _json
        if os.path.exists("edit_project.json"):
            with open("edit_project.json") as _f:
                _segs = (_json.load(_f) or {}).get("segments") or []
            def _norm(name):
                # lip_sync renames sources '<clip>_lipsync.mp4'; ordered_clips
                # use the base pre-lipsync names — normalize both sides.
                b = os.path.basename(str(name or ""))
                root, ext = os.path.splitext(b)
                if root.endswith("_lipsync"):
                    root = root[: -len("_lipsync")]
                return root + ext
            _ov_by_base = {}
            for _i, _s in enumerate(_segs):
                _ov = 0.0
                if _i > 0 and (_s.get("transition") or "cut") != "cut":
                    try:
                        _ov = max(0.0, float(_s.get("transition_dur") or 0.5))
                    except Exception:
                        _ov = 0.5
                _ov_by_base[_norm(_s.get("source"))] = _ov
                try:
                    _in_v = max(0.0, float(_s.get("in") or 0.0))
                except Exception:
                    _in_v = 0.0
                _out_raw = _s.get("out")
                try:
                    _out_v = float(_out_raw) if _out_raw is not None else None
                except Exception:
                    _out_v = None
                _win_by_base[_norm(_s.get("source"))] = (_in_v, _out_v)
            if transitions is None:
                _derived = [_ov_by_base.get(_norm(_c), 0.0) for _c in ordered_clips]
                if any(_o > 0 for _o in _derived):
                    transitions = _derived
                    print("[slice_master_audio_for_lipsync] the EDL has CROSSFADES but no "
                          "`transitions` was passed — derived the overlap list from "
                          "edit_project.json: %s. Every clip after a crossfade lands earlier "
                          "than the plain duration sum; slicing without this drifts the "
                          "mouths. Pass transitions explicitly to override." %
                          ["%.2f" % _o for _o in _derived])
    except Exception:
        pass
    # HUM/MELISMA SCREEN: lip-syncing a window that carries no real LYRICS
    # (hums, melisma/vocalise, group chorus, instrumental) ALWAYS renders
    # broken mouths — the sync model articulates ANY voiced audio (a real
    # delivered music video shipped word-mouth movements through every hummed
    # bar). Word timestamps for the master track (the _transcript_words file
    # transcription saves) let each slice be screened BEFORE the lip-sync jobs
    # are paid for. Silent when no transcript exists. Thresholds mirror
    # app/lib/music_video_coverage.py (the sandbox can't import the backend).
    _MIN_SYNC_WORD_DENSITY = 0.8   # words/sec below this = hum/melisma window
    _MIN_HUM_WINDOW_S = 2.5        # shorter windows: too small to judge
    def _load_transcript_words(master):
        import json as _json, re as _re
        stem = _re.sub(r"[^A-Za-z0-9._-]+", "_",
                       os.path.splitext(os.path.basename(str(master)))[0])[:80]
        # Per-source file first: the fixed alias is most-recent-wins and a later
        # transcribe of a different file would poison the timings.
        for cand in ("_transcript_words_%s.json" % stem, "_transcript_words.json"):
            if os.path.exists(cand):
                try:
                    with open(cand) as f:
                        w = _json.load(f)
                    return w if isinstance(w, list) and w else None
                except Exception:
                    return None
        return None
    _tw = _load_transcript_words(master_audio)
    def _word_density(s, e):
        if _tw is None or (e - s) < _MIN_HUM_WINDOW_S:
            return None
        n, usable = 0, False
        for w in _tw:
            try:
                ws, we = float(w["start"]), float(w["end"])
            except Exception:
                continue
            usable = True
            if s <= (ws + we) / 2.0 < e:
                n += 1
        return (n / (e - s)) if usable else None
    perf = set(os.path.basename(c) for c in performance_clips)
    audio_dur = _dur(master_audio)
    out = {}
    timeline_pos = 0.0  # current rendered length (accounts for crossfade overlaps)
    for i, c in enumerate(ordered_clips):
        d_file = _dur(c)
        base = os.path.basename(c)
        # Effective PLAYED duration: the EDL's in/out trim when one exists,
        # else the raw file duration. Offsets must advance by what actually
        # PLAYS — a mid-timeline trim otherwise shifts every later slice.
        _in_w, _out_w = _win_by_base.get(base, (0.0, None))
        if _out_w is not None:
            d = max(0.0, _out_w - _in_w)
        else:
            d = max(0.0, d_file - _in_w)
        if abs(d - d_file) > 0.05:
            print("[slice_master_audio_for_lipsync] NOTE %s: EDL trims it to %.2fs "
                  "(file is %.2fs) — offsets use the trimmed length." % (base, d, d_file))
        # A crossfade INTO this clip starts t_in before the current end, so the
        # clip's own first frame (and its synced audio @0) lands at start.
        start = max(0.0, timeline_pos - _overlap(i))
        if base in perf:
            # The slice drives the WHOLE source file (lip_sync syncs the file,
            # the timeline then plays its [in,out) window): frame `in` must
            # land on the song at timeline `start`, so the slice begins `in`
            # earlier and runs the full file length — the trimmed-away head/
            # tail mouth motion simply never renders.
            slice_start = max(0.0, start - _in_w)
            length = d_file if d_file > 0 else d
            if audio_dur and slice_start >= audio_dur:
                print("[slice_master_audio_for_lipsync] WARN %s: offset %.2fs is PAST audio "
                      "end %.2fs — the master track is too short for this cut; extend it." %
                      (base, slice_start, audio_dur))
            elif audio_dur and slice_start + length > audio_dur:
                length = max(0.0, audio_dur - slice_start)
                print("[slice_master_audio_for_lipsync] WARN %s: clip (%.2fs) runs past audio "
                      "end; slice clamped to %.2fs — also TRIM this clip to %.2fs (video_edit "
                      "trim / -t) so it doesn't outlast its audio and shift later offsets." %
                      (base, d_file, length, length))
            # Hum screen judges the VISIBLE window (what actually plays).
            _dens = _word_density(start, start + d)
            if _dens is not None and _dens < _MIN_SYNC_WORD_DENSITY:
                print("[slice_master_audio_for_lipsync] HUM WARNING %s: window "
                      "%.1f-%.1fs has only ~%.1f words/sec in the transcript — this "
                      "is a hum/melisma/vocalise/instrumental passage, NOT sung "
                      "lyrics. Lip-syncing it WILL render broken word-mouth "
                      "movements (the sync model articulates any voiced audio). "
                      "Strongly consider DEMOTING this beat to performer b-roll "
                      "(mouth not the focus) or a cutaway and skipping its "
                      "lip_sync; only sync windows that carry real lyrics." %
                      (base, start, start + d, _dens))
            sp = os.path.join(out_dir, "%s%s.mp3" % (prefix, os.path.splitext(base)[0]))
            subprocess.run(["ffmpeg", "-y", "-ss", "%.3f" % slice_start, "-t", "%.3f" % max(0.05, length),
                            "-i", master_audio, "-c:a", "libmp3lame", "-q:a", "2", sp],
                           capture_output=True, text=True)
            out[base] = sp
            print("[slice_master_audio_for_lipsync] %s -> audio[%.2f->%.2f]s  %s" %
                  (base, slice_start, slice_start + length, sp))
        timeline_pos = start + d
    if audio_dur and timeline_pos > audio_dur + 0.05:
        print("[slice_master_audio_for_lipsync] NOTE total cut %.2fs > master audio %.2fs "
              "(by %.2fs) — extend the master track or trim the last scene so the audio covers "
              "the WHOLE cut (music_master + -shortest would otherwise cut the video to the audio)."
              % (timeline_pos, audio_dur, timeline_pos - audio_dur))
    return out


# Back-compat alias: same function, music-flavored name (kept so older guidance /
# code that calls slice_song_for_lipsync keeps working).
slice_song_for_lipsync = slice_master_audio_for_lipsync


def compose_overlays(video_in, overlays, output="composed.mp4",
                     has_captions=True, caption_band_frac=0.20,
                     safe_margin_frac=0.05, font_style="serif_elegant",
                     fill=(255, 255, 255), preset="veryfast", crf=20):
    """Overlay title cards / name supers / end-CTA cards onto a video WITHOUT
    colliding with burned-in captions or with each other.

    USE THIS for on-screen TEXT CARDS (opening title, name/role lower-third, end /
    call-to-action card). Do NOT hand-place overlay PNGs at arbitrary y positions:
    captions live in the bottom band (via burn_captions), so a hand-placed lower
    overlay collides with them (overlapping, unreadable text). This helper keeps
    every overlay inside the title-safe area, OUT of the caption band, and pushes
    time-overlapping overlays into separate vertical slots. Text WIDTH is also
    guaranteed: lines wider than the title-safe width are auto-shrunk (all lines
    proportionally, hierarchy preserved) so no letter is ever cut by the frame
    edge — this applies even to explicit per-line "sizes".

    Order of operations: assemble + mux audio + burn_captions FIRST, then
    compose_overlays LAST on the captioned video (pass has_captions=True so the
    bottom band is reserved). Captions themselves still go through burn_captions.

    Args:
      video_in: the assembled (and usually already-captioned) video.
      overlays: list of dicts, each:
         {"lines": ["Marlon Lawson", "City of Cuda"],  # 1+ text lines, top->bottom
          "start": 0.3, "end": 4.8,                     # seconds the card is visible
          "zone": "top"|"upper"|"center"|"lower",       # OPTIONAL; auto if omitted
          "sizes": [96, 58]}                            # OPTIONAL per-line px sizes
      output: output filename (workspace-relative).
      has_captions: True reserves the bottom caption_band_frac for captions so no
                    overlay is placed there. Set False only if the video has NO
                    burned captions.
      caption_band_frac: bottom fraction reserved for captions (default 0.20).
      safe_margin_frac: title-safe inset on all edges (default 0.05 = 5%).
      font_style: pick_font style for the card text (default 'serif_elegant').

    Returns dict {"output", "duration", "overlays"}.
    """
    import subprocess, os
    from PIL import Image, ImageDraw, ImageFont
    if not os.path.exists(video_in):
        raise FileNotFoundError("compose_overlays: video not found: " + str(video_in))
    if not overlays:
        raise ValueError("compose_overlays: no overlays given")

    def _probe_int(key, default):
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
             "stream=" + key, "-of", "default=nokey=1:noprint_wrappers=1", video_in],
            capture_output=True, text=True)
        try:
            return int(float(r.stdout.strip()))
        except Exception:
            return default

    W = _probe_int("width", 1080)
    H = _probe_int("height", 1920)
    rd = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nokey=1:noprint_wrappers=1", video_in],
        capture_output=True, text=True)
    try:
        VDUR = float(rd.stdout.strip())
    except Exception:
        VDUR = 0.0

    margin = int(round(safe_margin_frac * min(W, H)))
    safe_top = margin
    safe_bottom = H - margin
    if has_captions:
        safe_bottom = min(safe_bottom, int(round(H * (1.0 - caption_band_frac))))
    avail_h = max(1, safe_bottom - safe_top)
    base = max(28, int(round(H * 0.05)))  # ~96px on a 1920-tall frame

    fill = tuple(fill)[:3]

    # 1) Render each overlay to a transparent PNG cropped to its text-block height.
    items = []
    for i, ov in enumerate(overlays):
        lines = ov.get("lines") or ov.get("text") or []
        if isinstance(lines, str):
            lines = [lines]
        lines = [str(x) for x in lines if str(x).strip()]
        if not lines:
            continue
        sizes = ov.get("sizes") or [base if k == 0 else int(base * 0.62) for k in range(len(lines))]
        if len(sizes) < len(lines):
            sizes = list(sizes) + [sizes[-1]] * (len(lines) - len(sizes))
        fonts = [ImageFont.truetype(pick_font(font_style, "bold"), int(s)) for s in sizes]
        # HORIZONTAL FIT (guaranteed): this helper enforced vertical safety but
        # never width, so a line wider than the frame was centered into negative
        # x and painted OFF BOTH EDGES — shipped bug: 704px-wide i2v b-roll got a
        # 64px question overlay whose first line clipped at both sides, and QC
        # passed it four times as "crisp, centered". Shrink ALL lines by the same
        # ratio (preserving the size hierarchy) until the widest fits the
        # title-safe width. Never enlarges; floor keeps text legible rather than
        # silently vanishing.
        safe_w = max(1, W - 2 * margin)
        _meas = ImageDraw.Draw(Image.new("RGBA", (4, 4), (0, 0, 0, 0)))
        for _ in range(3):  # int truncation can leave a px or two; converge fast
            widest = 0
            for ln, fnt in zip(lines, fonts):
                bb = _meas.textbbox((0, 0), ln, font=fnt)
                widest = max(widest, bb[2] - bb[0])
            if widest <= safe_w:
                break
            shrink = safe_w / float(widest)
            sizes = [max(14, int(s * shrink)) for s in sizes]
            fonts = [ImageFont.truetype(pick_font(font_style, "bold"), int(s)) for s in sizes]
            print("[compose_overlays] overlay %d: text wider than frame — shrunk to %s "
                  "to fit %dpx safe width" % (i, sizes, safe_w))
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        widths, heights = [], []
        for ln, fnt in zip(lines, fonts):
            bb = d.textbbox((0, 0), ln, font=fnt)
            widths.append(bb[2] - bb[0])
            heights.append(bb[3] - bb[1])
        gap = int(round(base * 0.25))
        block_h = max(1, sum(heights) + gap * (len(lines) - 1))
        y = 0
        for ln, fnt, h_ in zip(lines, fonts, heights):
            bb = d.textbbox((0, 0), ln, font=fnt)
            w_ = bb[2] - bb[0]
            x = (W - w_) // 2
            for dx, dy in [(-3, -3), (3, 3), (-3, 3), (3, -3), (0, 4)]:
                d.text((x + dx, y + dy - bb[1]), ln, font=fnt, fill=(0, 0, 0, 200))
            d.text((x, y - bb[1]), ln, font=fnt, fill=fill + (255,))
            y += h_ + gap
        img = img.crop((0, 0, W, block_h))
        p = "_ov_%d.png" % i
        img.save(p)
        items.append({
            "path": p, "h": block_h,
            "start": float(ov.get("start", 0.0)),
            "end": float(ov.get("end", VDUR or 0.0)),
            "zone": ov.get("zone"),
        })

    if not items:
        raise ValueError("compose_overlays: no usable overlay text")

    # 2) Assign each overlay a vertical slot: respect an explicit zone, else default
    # to a lower-third look — but ALWAYS inside the safe area, NEVER in the caption
    # band, and never overlapping a time-concurrent overlay.
    zone_frac = {"top": 0.10, "upper": 0.30, "center": 0.50, "lower": 0.86}
    default_order = ["lower", "upper", "top", "center"]
    placed = []
    for ov in items:
        cands = []
        if ov["zone"] in zone_frac:
            cands.append(ov["zone"])
        cands += [z for z in default_order if z not in cands]
        chosen = None
        for z in cands:
            yc = safe_top + int(round(zone_frac[z] * avail_h))
            y0 = yc - ov["h"] // 2
            y0 = max(safe_top, min(y0, safe_bottom - ov["h"]))
            y1 = y0 + ov["h"]
            conflict = any(
                (not (ov["end"] <= q["start"] or ov["start"] >= q["end"]))
                and (not (y1 <= q["y0"] or y0 >= q["y1"]))
                for q in placed
            )
            if not conflict:
                chosen = y0
                break
        if chosen is None:  # everything conflicts — accept the top-of-safe slot
            chosen = max(safe_top, min(safe_top, safe_bottom - ov["h"]))
        ov["y"] = chosen
        placed.append({"y0": chosen, "y1": chosen + ov["h"],
                       "start": ov["start"], "end": ov["end"]})

    # 3) One ffmpeg pass: chain the overlays with per-card time windows.
    inputs = ["-i", video_in]
    for ov in items:
        inputs += ["-i", ov["path"]]
    cur = "0:v"
    filt = []
    for idx, ov in enumerate(items, start=1):
        nxt = "v%d" % idx
        filt.append("[%s][%d:v]overlay=0:%d:enable='between(t,%.3f,%.3f)'[%s]"
                    % (cur, idx, ov["y"], ov["start"], ov["end"], nxt))
        cur = nxt
    cmd = (["ffmpeg", "-y"] + inputs
           + ["-filter_complex", ";".join(filt), "-map", "[%s]" % cur, "-map", "0:a?",
              "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
              "-pix_fmt", "yuv420p", "-c:a", "copy", output])
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        # Retry re-encoding audio in case stream-copy refused the source.
        cmd2 = (["ffmpeg", "-y"] + inputs
                + ["-filter_complex", ";".join(filt), "-map", "[%s]" % cur, "-map", "0:a?",
                   "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
                   "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", output])
        r = subprocess.run(cmd2, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError("compose_overlays failed: " + (r.stderr or "")[-700:])

    for ov in items:
        try:
            os.unlink(ov["path"])
        except OSError:
            pass
    print("[compose_overlays] %d overlay(s) -> %s (%dx%d, caption_band=%s)"
          % (len(items), output, W, H, ("on" if has_captions else "off")))
    return {"output": output, "duration": round(VDUR, 3), "overlays": len(items)}


def _supercool_make_fpdf_unicode_safe():
    try:
        _F = globals().get("FPDF", None)
        if _F is None or getattr(_F, "_supercool_unicode_safe", False):
            return
        _orig_normalize = _F.normalize_text
        _MAP = {
            "\u2014": "--", "\u2013": "-", "\u2012": "-", "\u2015": "--",
            "\u2018": "'", "\u2019": "'", "\u201a": "'", "\u201b": "'",
            "\u201c": '"', "\u201d": '"', "\u201e": '"', "\u201f": '"',
            "\u2026": "...", "\u2022": "*", "\u00a0": " ", "\u00ad": "",
            "\u00ab": '"', "\u00bb": '"', "\u2039": "'", "\u203a": "'",
            "\u2032": "'", "\u2033": '"', "\u2212": "-", "\ufeff": "",
        }
        def _supercool_sanitize(text):
            if not isinstance(text, str):
                return text
            out = []
            for ch in text:
                if ch in _MAP:
                    out.append(_MAP[ch])
                elif ord(ch) < 256:
                    out.append(ch)
                else:
                    out.append("?")
            return "".join(out)
        def normalize_text(self, text):
            try:
                return _orig_normalize(self, text)
            except Exception:
                return _orig_normalize(self, _supercool_sanitize(text))
        _F.normalize_text = normalize_text
        _F._supercool_unicode_safe = True
    except Exception:
        pass
_supercool_make_fpdf_unicode_safe()


_sc_write_verify_failures = []

# QC-frame provenance: basename -> size (bytes) of each VIDEO a frame was
# extracted from via ffmpeg this call. The host compares this against the
# video files actually DELIVERED, so "I verified it frame-by-frame" can never
# describe a different file than the one the user receives (real incident:
# QC frames came from intermediate builds while the published master was
# stale — the agent told the user its fixes were verified when the delivered
# file didn't contain them).
_sc_qc_frame_reads = {}

# Output extensions worth verifying (bounds false positives: a trailing option
# VALUE like "-preset veryfast" has no known media extension).
_SC_VERIFY_OUT_EXTS = (
    ".mp4", ".mov", ".mkv", ".webm", ".m4v", ".ts", ".avi", ".mpg", ".mpeg",
    ".flv", ".wmv", ".3gp", ".gif", ".mp3", ".wav", ".m4a", ".aac", ".flac",
    ".ogg", ".oga", ".opus", ".jpg", ".jpeg", ".png", ".webp", ".tif",
    ".tiff", ".bmp", ".srt", ".ass", ".vtt", ".pdf",
)

_SC_QC_VIDEO_EXTS = (".mp4", ".mov", ".mkv", ".webm", ".m4v", ".ts", ".avi",
                     ".mpg", ".mpeg", ".flv", ".wmv", ".3gp")
_SC_QC_IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff")

def _sc_resolve_child_path(path, child_cwd):
    """Resolve a path the way the CHILD process saw it: relative paths are
    relative to the subprocess's cwd= (when given), not ours."""
    if child_cwd and not os.path.isabs(path):
        return os.path.join(str(child_cwd), path)
    return path

def _sc_record_qc_frame_read(argv, child_cwd=None):
    """If this ffmpeg call extracts image frame(s) from a video, record the
    video's basename and current size. Never raises."""
    try:
        if os.path.basename(str(argv[0])).lower() != "ffmpeg":
            return
        _out = str(argv[-1]).lower()
        # Frame grabs write images (possibly %-patterns for contact sheets).
        if not _out.endswith(_SC_QC_IMAGE_EXTS):
            return
        for _j, _a in enumerate(argv):
            if str(_a) == "-i" and _j + 1 < len(argv):
                _src = str(argv[_j + 1])
                if _src.lower().endswith(_SC_QC_VIDEO_EXTS):
                    _p = _sc_resolve_child_path(_src, child_cwd)
                    if os.path.exists(_p):
                        _sc_qc_frame_reads[os.path.basename(_src)] = os.path.getsize(_p)
    except Exception:
        pass

def _sc_subproc_output_target(argv):
    """Best-effort output path of a media-writer command, or None.

    ffmpeg/convert/magick/sox-style CLIs take the output as the LAST argument.
    Returns None for anything ambiguous: flags, pipes, /dev/null, %-pattern
    image sequences, or a last arg without a known output extension.
    """
    try:
        if not argv or len(argv) < 3:
            return None
        prog = os.path.basename(str(argv[0])).lower()
        if prog not in ("ffmpeg", "convert", "magick", "sox"):
            return None
        last = str(argv[-1])
        if not last or last.startswith("-") or last.startswith("pipe:"):
            return None
        if last in ("/dev/null", "null") or "%" in os.path.basename(last):
            return None
        if not last.lower().endswith(_SC_VERIFY_OUT_EXTS):
            return None
        return last
    except Exception:
        return None

def _sc_wv_try_reroute(argv, tgt, tgt_p, child_cwd):
    """Self-heal a vanished ffmpeg write: the S3-FUSE workspace mount drops
    ffmpeg's SEEKING writes (mp4 muxer header patching) with exit code 0,
    while plain sequential writes land (verified live — this is the mechanism
    behind the prod vanishing-master incident). Re-run the SAME command with
    the output redirected to local /tmp, then copy it back sequentially.
    Returns True when the target now exists non-empty. Never raises."""
    try:
        if os.path.basename(str(argv[0])).lower() != "ffmpeg":
            return False
        import shutil as _wv_shutil
        import uuid as _wv_uuid
        _tmp = os.path.join("/tmp", "_wv_reroute_" + _wv_uuid.uuid4().hex[:8]
                            + "_" + os.path.basename(str(tgt)))
        _argv2 = list(argv[:-1]) + [_tmp]
        _r2 = _sc_wv_real_run(_argv2, capture_output=True,
                              **({"cwd": child_cwd} if child_cwd else {}))
        if getattr(_r2, "returncode", 1) != 0:
            return False
        if (not os.path.exists(_tmp)) or os.path.getsize(_tmp) == 0:
            return False
        with open(_tmp, "rb") as _src, open(tgt_p, "wb") as _dst:
            _wv_shutil.copyfileobj(_src, _dst)
        try:
            os.remove(_tmp)
        except Exception:
            pass
        return os.path.exists(tgt_p) and os.path.getsize(tgt_p) > 0
    except Exception:
        return False

try:
    import subprocess as _sc_wv_sp
    _sc_wv_real_run = _sc_wv_sp.run
    def _sc_wv_verified_run(*args, **kwargs):
        _r = _sc_wv_real_run(*args, **kwargs)
        try:
            _argv = args[0] if args else kwargs.get("args")
            if (
                isinstance(_argv, (list, tuple))
                and not kwargs.get("shell")
                and getattr(_r, "returncode", 1) == 0
            ):
                # Relative paths must resolve against the CHILD's cwd= (when
                # given), not ours — otherwise a healthy `run([...], cwd=subdir)`
                # would be flagged as a phantom write (false positive).
                _child_cwd = kwargs.get("cwd")
                _sc_record_qc_frame_read(list(_argv), _child_cwd)
                _tgt = _sc_subproc_output_target(list(_argv))
                if _tgt is not None:
                    _tgt_p = _sc_resolve_child_path(_tgt, _child_cwd)
                    if (not os.path.exists(_tgt_p)) or os.path.getsize(_tgt_p) == 0:
                        _prog = os.path.basename(str(_argv[0]))
                        if _sc_wv_try_reroute(list(_argv), _tgt, _tgt_p, _child_cwd):
                            print(
                                "[WRITE RECOVERED] " + _prog + "'s direct write of '"
                                + _tgt + "' was dropped by the workspace mount, so it "
                                "was automatically re-rendered via local scratch and "
                                "copied back — the file now exists and is valid. No "
                                "action needed, but prefer rendering to /tmp and "
                                "copying into the workspace for large ffmpeg outputs."
                            )
                        else:
                            # (display, abspath): abspath is materialized NOW (cwd
                            # may change later) so the script tail can re-check it
                            # and DROP entries whose file exists by end of call — a
                            # failure the code later recovered must not fail the call.
                            _sc_write_verify_failures.append(
                                (_prog + " -> " + _tgt, os.path.abspath(_tgt_p))
                            )
                            print(
                                "[WRITE VERIFICATION FAILED] " + _prog + " exited 0 but its "
                                "output '" + _tgt + "' is MISSING or 0 bytes — the workspace "
                                "silently dropped the write, and the automatic /tmp reroute "
                                "also failed. This step DID NOT produce its file. Re-run the "
                                "render writing to /tmp first, then copy the file into the "
                                "workspace with plain Python I/O, and confirm it exists. Do "
                                "NOT claim this output exists or deliver from it."
                            )
        except Exception:
            pass
        return _r
    _sc_wv_sp.run = _sc_wv_verified_run
except Exception:
    pass


# PDF conversion requests (will be processed by host after sandbox execution)
_pdf_conversion_requests = []

# Template document requests (will be processed by host after sandbox execution)
_template_document_requests = []

# Edit document requests (will be processed by host after sandbox execution)
_edit_document_requests = []

# HTML -> PDF render requests (processed by host with Chromium after sandbox execution)
_html_pdf_requests = []

# Structured document render requests (processed by host after sandbox execution)
_render_document_requests = []

# EPUB build requests (processed by host after sandbox execution — never pandoc
# in the sandbox; the FUSE workspace rejects zip seek-on-write).
_epub_build_requests = []

# Host-processed doc-generation requests are also written to files under
# /workspace/_doc_requests/ so the host can recover them even if stdout (and its
# markers) get truncated/killed. The session sandbox is REUSED across calls, so
# clear any stale request files from a previous run before this run queues new
# ones - otherwise the host's recovery scan could reprocess an old request.
try:
    import shutil as _shutil_cleanup
    _shutil_cleanup.rmtree('/workspace/_doc_requests', ignore_errors=True)
except Exception:
    pass


def _write_doc_request(kind, index, request):
    """Persist a host-processed doc request to a file and return its workspace-
    relative path. Keeps large payloads (specs/HTML) OUT of stdout, where they
    were being truncated and silently dropped."""
    os.makedirs('/workspace/_doc_requests', exist_ok=True)
    rel = '_doc_requests/%s_%d.json' % (kind, index)
    with open('/workspace/' + rel, 'w') as _rf:
        json.dump(request, _rf)
    return rel


def convert_docx_to_pdf(docx_path):
    """
    Request DOCX to PDF conversion (processed by host after sandbox execution).

    Args:
        docx_path: Path to the DOCX file (can be string or Path)

    Returns:
        Expected PDF path (conversion happens after sandbox execution)

    Note: The actual conversion is done by LibreOffice on the host system.
    The PDF will be available after this script completes.
    """
    docx_path = str(docx_path)
    if not docx_path.startswith('/workspace/'):
        docx_path = f'/workspace/{docx_path}'

    # Calculate expected PDF path
    pdf_path = docx_path.rsplit('.', 1)[0] + '.pdf'

    # Add to conversion requests
    _pdf_conversion_requests.append(docx_path)

    print(f"[PDF Conversion queued] {docx_path} -> {pdf_path}")
    return pdf_path

def create_document_from_template(
    document_type: str,
    content: str,
    output_filename: str,
    title: str = None,
    convert_to_pdf: bool = True,
    image_paths: list = None,
    cover_image: str = None,
    must_contain: list = None,
    must_not_contain: list = None,
    include_epub: bool = None
):
    """
    Create a professional document using templates (processed by host after sandbox execution).

    This function queues a document creation request that will be processed by the host
    system using professional DOCX templates and LibreOffice for PDF conversion.

    Args:
        document_type: Type of document to create. Options include:
            - "report" - General report (business, technical, etc.)
            - "business_report" - Formal business report
            - "proposal" - Business or client proposal
            - "grant_proposal" - Grant funding proposal
            - "book" - Book or manuscript
            - "novel" - Fiction novel
            - "brochure" - Marketing brochure
            - "newsletter" - Newsletter
            - "resume" - Resume/CV
            - "cover_letter" - Cover letter
            - "article" - Academic article
            - "meeting_agenda" - Meeting agenda
            - "business_letter" - Formal business letter
            - "memo" - Business memo
        content: Markdown-formatted content for the document.
            Use # for main headings, ## for subheadings, - for bullet points, etc.
        output_filename: Base filename for output (without extension).
            Example: "quarterly_report" -> creates quarterly_report.docx and quarterly_report.pdf
        title: Optional document title. If not provided, uses first # heading from content.
        convert_to_pdf: Whether to also create PDF version (default: True)
        must_contain: FIX-LANDING VERIFICATION - when this render carries an edit,
            list short verbatim snippets of the NEW text; the RENDERED file is
            checked and a missing snippet is reported loudly, so a claimed fix
            can never silently not land. Use whenever re-rendering after an edit.
        must_not_contain: Removal counterpart - snippets that were supposedly
            REMOVED; if any is still in the rendered file it is reported as a
            failed fix.
        include_epub: Companion ebook control. None (default) = book document
            types (book/novel/storybook/children_book) automatically ship a
            companion .epub alongside the PDF (same stem, KDP print + ebook
            parity); False = print only (user explicitly wants no ebook);
            True = force a companion .epub for any document type.

    Returns:
        dict with expected output paths:
            {"docx": "/workspace/filename.docx", "pdf": "/workspace/filename.pdf",
              "epub": "/workspace/filename.epub" or None}

    Example:
        result = create_document_from_template(
            document_type="report",
            content="# Report Title\n\n## Summary\n- Point one\n- Point two",
            output_filename="my_report",
            title="My Report Title"
        )
        print("Document created:", result)
    """
    # Note: json is already imported at script top level

    # `content` takes TEXT, not a filename (a real session passed a .md
    # filename and typeset a 2-page book whose entire body was the name).
    _ct = (content or "").strip()
    if (
        _ct and len(_ct) <= 200
        and not any(c.isspace() for c in _ct)
        and _ct.lower().endswith(('.md', '.markdown', '.txt', '.doc', '.docx', '.html', '.htm', '.json', '.pdf', '.rtf', '.epub'))
    ):
        raise ValueError(
            "content must be the document TEXT, not a filename ('%s'). "
            "Read the file first (open('%s').read()) and pass its contents." % (_ct, _ct)
        )

    # Normalize filename
    if output_filename.endswith('.docx') or output_filename.endswith('.pdf'):
        output_filename = output_filename.rsplit('.', 1)[0]

    # Build paths
    docx_path = f"/workspace/{output_filename}.docx"
    pdf_path = f"/workspace/{output_filename}.pdf" if convert_to_pdf else None
    _inc_epub = include_epub
    if _inc_epub is None:
        _inc_epub = (document_type or "").lower() in ("book", "novel", "storybook", "children_book")
    epub_path = f"/workspace/{output_filename}.epub" if (_inc_epub and convert_to_pdf) else None

    # Queue the request
    request = {
        "document_type": document_type,
        "content": content,
        "output_filename": output_filename,
        "title": title,
        "convert_to_pdf": convert_to_pdf,
        "image_paths": image_paths,
        "cover_image": cover_image,
        "must_contain": must_contain,
        "must_not_contain": must_not_contain,
        "include_epub": include_epub
    }
    # File-backed request (robust against stdout truncation); marker carries path.
    _template_document_requests.append(_write_doc_request('template', len(_template_document_requests), request))

    print(f"[Template Document queued] Type: {document_type}, Output: {output_filename}")
    if convert_to_pdf and epub_path:
        print(f"  -> Will create: {docx_path}, {pdf_path} and {epub_path}")
    elif convert_to_pdf:
        print(f"  -> Will create: {docx_path} and {pdf_path}")
    else:
        print(f"  -> Will create: {docx_path}")

    return {"docx": docx_path, "pdf": pdf_path, "epub": epub_path}

def html_to_pdf(html, output_filename, page_size='Letter', landscape=False, margin=None, full_bleed=False):
    """
    Render fully designed HTML/CSS to a PDF via headless Chromium (processed by
    the host after sandbox execution). Use this for fully bespoke/branded
    documents needing exact custom layout. For standard designed docs (workbooks,
    journals, reports, brochures) prefer render_document(...).

    Print-safe by default: a 0.6in margin is applied and a baseline print
    stylesheet is injected if your HTML has no @page rule.

    Args:
        html: Raw HTML markup, OR the path to an existing .html file in /workspace.
        output_filename: Base filename (without extension).
        page_size: "Letter" | "A4" | "Legal" | "Tabloid".
        landscape: True for landscape orientation.
        margin: CSS margin on all sides (default 0.6in). Ignored if full_bleed=True.
        full_bleed: True ONLY for intentional edge-to-edge art (e.g. a cover).

    Returns:
        Expected PDF path ("/workspace/<output_filename>.pdf").
    """
    if output_filename.endswith('.pdf'):
        output_filename = output_filename.rsplit('.', 1)[0]

    # Determine whether html is an existing .html file path or raw markup.
    try:
        is_file = len(str(html)) < 1024 and str(html).lower().endswith(('.html', '.htm'))
    except Exception:
        is_file = False

    if is_file:
        src_name = str(html).split('/')[-1]
    else:
        # Write raw HTML into the workspace so relative asset paths resolve.
        src_name = output_filename + '.html'
        with open('/workspace/' + src_name, 'w', encoding='utf-8') as _f:
            _f.write(html)

    pdf_path = '/workspace/' + output_filename + '.pdf'
    request = {
        "html_file": src_name,
        "output_filename": output_filename,
        "page_size": page_size,
        "landscape": landscape,
        "margin": margin,
        "full_bleed": full_bleed
    }
    # File-backed request (robust against stdout truncation); marker carries path.
    _html_pdf_requests.append(_write_doc_request('html', len(_html_pdf_requests), request))

    print(f"[HTML PDF queued] -> {pdf_path}")
    return pdf_path

def render_document(spec, output_filename, theme="workbook"):
    """
    Render a STRUCTURED document spec to a print-correct PDF (processed by the
    host after sandbox execution). PREFERRED for designed/branded documents -
    pagination, margins, and form-field spacing are guaranteed by the renderer.

    Args:
        spec: dict {"title", "subtitle", "author", "blocks": [ {...}, ... ]}.
            Block types: cover, section_divider, heading, paragraph, callout,
            field, field_grid, lines, checkbox_grid, score_row, table,
            tracker_grid, declaration, image.
        output_filename: Base filename (without extension).
        theme: "workbook" | "journal" | "report" | "brochure".

    Returns:
        Expected PDF path ("/workspace/<output_filename>.pdf").
    """
    if output_filename.endswith('.pdf'):
        output_filename = output_filename.rsplit('.', 1)[0]
    pdf_path = '/workspace/' + output_filename + '.pdf'
    request = {
        "spec": spec,
        "output_filename": output_filename,
        "theme": theme
    }
    # Persist the request to a file and carry only the tiny path in stdout (large
    # specs printed to stdout were being truncated, silently dropping the render).
    _render_document_requests.append(_write_doc_request('render', len(_render_document_requests), request))
    print(f"[Render Document queued] -> {pdf_path}")
    return pdf_path

def pdf_to_images(pdf_path, dpi=110, max_pages=12):
    """
    Rasterize a PDF's pages to PNG files in /workspace and return their paths
    (useful when you need page images to embed elsewhere). For layout QA before
    delivering, use verify_document() instead - it checks pagination, bleed, and
    blank/sparse pages programmatically.

    Args:
        pdf_path: path to the PDF (absolute or /workspace-relative).
        dpi: rasterization DPI (110 is a good preview default).
        max_pages: cap the number of pages rendered.

    Returns:
        List of saved PNG paths (also surfaced as attachments to view).
    """
    from pathlib import Path as _P
    if convert_from_path is None:
        print("[pdf_to_images] pdf2image unavailable")
        return []
    p = _P(pdf_path)
    if not p.is_absolute():
        p = _P('/workspace') / p.name
    if not p.exists():
        print(f"[pdf_to_images] file not found: {p}")
        return []
    try:
        imgs = convert_from_path(str(p), dpi=dpi, first_page=1, last_page=max_pages)
    except Exception as e:
        print(f"[pdf_to_images] failed: {e}")
        return []
    out = []
    for i, im in enumerate(imgs, 1):
        op = _P('/workspace') / (p.stem + f"_page{i:02d}.png")
        try:
            im.save(str(op), "PNG")
            out.append(str(op))
        except Exception as e:
            print(f"[pdf_to_images] could not save page {i}: {e}")
    print(f"[pdf_to_images] {len(out)} page image(s) saved")
    return out

def edit_existing_document(
    source_filename: str,
    output_filename: str,
    insert_images: list = None,
    text_replacements: list = None,
    convert_to_pdf: bool = True
):
    """
    Edit an existing DOCX document by replacing text and/or inserting images.

    IMPORTANT: Use this function when the user asks to modify/edit an existing document
    (e.g., "change the title", "insert an image", "update the text", "add a picture").
    Do NOT recreate the document from scratch - use this to preserve existing content and styling.

    Args:
        source_filename: Filename of the existing DOCX document to edit (in /workspace)
        output_filename: Filename for the modified document (without extension)
        insert_images: List of image insertion specifications. Each item should be a dict:
            {
                "image_path": "/workspace/image.png",  # Path to the image
                "search_text": "Remember",  # Text to search for in the document
                "position": "before",  # "before" or "after" the found paragraph
                "caption": "Optional caption"  # Optional caption for the image
            }
        text_replacements: List of text replacement specifications. Each item should be a dict:
            {
                "old_text": "Original Title",  # Text to find
                "new_text": "New Title",  # Replacement text
                "replace_all": True  # Whether to replace all occurrences (default: True)
            }
        convert_to_pdf: Whether to also create PDF version (default: True)

    Returns:
        dict with expected output paths: {"docx": path, "pdf": path or None}

    Example:
        # Change title AND insert a new image
        result = edit_existing_document(
            source_filename="My_Story.docx",
            output_filename="My_Story_Updated",
            text_replacements=[
                {"old_text": "Old Title", "new_text": "New Amazing Title"}
            ],
            insert_images=[
                {
                    "image_path": "/workspace/new_image.png",
                    "search_text": "Conclusion",
                    "position": "before",
                    "caption": "A beautiful scene"
                }
            ]
        )
    """
    # Normalize source filename
    if not source_filename.startswith('/workspace/'):
        source_filename = f'/workspace/{source_filename}'

    # Auto-resolve PDF to DOCX: editing must be done on the DOCX source
    if source_filename.lower().endswith('.pdf'):
        docx_source = source_filename[:-4] + '.docx'
        print(f"[Edit] Note: Source is PDF, using DOCX version: {docx_source}")
        source_filename = docx_source

    # Normalize output filename
    if output_filename.endswith('.docx') or output_filename.endswith('.pdf'):
        output_filename = output_filename.rsplit('.', 1)[0]

    docx_path = f"/workspace/{output_filename}.docx"
    pdf_path = f"/workspace/{output_filename}.pdf" if convert_to_pdf else None

    # Queue the request
    request = {
        "action": "edit",
        "source_filename": source_filename,
        "output_filename": output_filename,
        "insert_images": insert_images or [],
        "text_replacements": text_replacements or [],
        "convert_to_pdf": convert_to_pdf
    }
    _edit_document_requests.append(json.dumps(request))

    print(f"[Edit Document queued] Source: {source_filename} -> Output: {output_filename}")
    if text_replacements:
        for repl in text_replacements:
            print(f"  -> Will replace '{repl.get('old_text', '')[:30]}...' with '{repl.get('new_text', '')[:30]}...'")
    if insert_images:
        for img in insert_images:
            print(f"  -> Will insert image {img.get('position', 'before')} '{img.get('search_text', '')}'")
    if convert_to_pdf:
        print(f"  -> Will create: {docx_path} and {pdf_path}")
    else:
        print(f"  -> Will create: {docx_path}")

    return {"docx": docx_path, "pdf": pdf_path}

def convert_to_epub(input_file, output_file=None, title=None, author=None,
                    publisher=None, isbn=None):
    """
    Convert a document to EPUB (processed by the host after sandbox execution).

    Prefer the create_document TOOL with formats=['epub'] when possible — it
    carries the full quality suite. This queues a host-side build using the
    first-class EPUB renderer (NOT pandoc in the sandbox).

    ASYNCHRONOUS like html_to_pdf: the .epub is created AFTER this call
    finishes and is delivered automatically — do NOT exists()-check, open,
    or verify it in the same call.

    Args:
        input_file: Path to source file (.md, .txt, .html, .docx)
        output_file: Output .epub path (default: same name with .epub extension)
        title, author, publisher, isbn: EPUB metadata (KDP)

    Returns:
        Expected EPUB path (created after sandbox execution).
    """
    from pathlib import Path as _P

    src = _P(input_file)
    if not src.is_absolute():
        src = _P("/workspace") / src
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")
    if output_file is None:
        dst = src.with_suffix(".epub")
    else:
        dst = _P(output_file)
        if not dst.is_absolute():
            dst = _P("/workspace") / dst

    request = {
        "source_file": str(src).replace("/workspace/", ""),
        "output_file": str(dst).replace("/workspace/", ""),
        "title": title,
        "author": author,
        "publisher": publisher,
        "isbn": isbn,
    }
    _epub_build_requests.append(_write_doc_request('epub', len(_epub_build_requests), request))
    print(f"[EPUB queued] {src.name} -> {dst.name}")
    return str(dst)

def html_interior_to_epub(section_files, output_filename, title=None, author=None,
                          cover_image=None, publisher=None, isbn=None):
    """
    Build a reflowable EPUB from HTML interior section files (companion to
    html_to_pdf bespoke book interiors). Processed by the host after execution:
    print CSS is stripped for reflow and workspace images are packaged in.

    ASYNCHRONOUS like html_to_pdf: the .epub is created AFTER this call
    finishes and is delivered automatically — do NOT exists()-check, open,
    or verify it in the same call.

    Args:
        section_files: list of workspace-relative .html paths, OR list of dicts
            {"title": "...", "html_file": "section1.html"}
        output_filename: base name (no extension) for the .epub
        title, author, cover_image, publisher, isbn: EPUB metadata

    Returns:
        Expected EPUB path.
    """
    from pathlib import Path as _P

    if output_filename.endswith('.epub'):
        output_filename = output_filename.rsplit('.', 1)[0]
    sections = []
    for i, entry in enumerate(section_files or []):
        if isinstance(entry, dict):
            href = entry.get("html_file") or entry.get("file") or ""
            sec_title = entry.get("title") or f"Section {i + 1}"
        else:
            href = str(entry)
            sec_title = f"Section {i + 1}"
        name = str(href).split('/')[-1]
        if not _P('/workspace/' + name).exists():
            raise FileNotFoundError(f"HTML section not found in workspace: {name}")
        sections.append({"title": sec_title, "html_file": name})
    request = {
        "mode": "html_sections",
        "sections": sections,
        "output_filename": output_filename,
        "title": title,
        "author": author,
        "cover_image": (str(cover_image).split('/')[-1] if cover_image else None),
        "publisher": publisher,
        "isbn": isbn,
    }
    _epub_build_requests.append(_write_doc_request('epub', len(_epub_build_requests), request))
    epub_path = '/workspace/' + output_filename + '.epub'
    print(f"[EPUB interior queued] {len(sections)} section(s) -> {epub_path}")
    return epub_path

def verify_document(path, expected_pages=None, check_blank=True, max_pages_to_scan=60):
    """Verify a generated document BEFORE delivering it.

    Catches missing pages and blank/near-uniform pages (solid white/black/color
    fills). Call this in the SAME python_execute that created the file and do NOT
    deliver the file if the returned 'ok' is False. Pass expected_pages whenever
    you know the count - it is the most reliable guard.
    """
    from pathlib import Path as _P

    if str(path).startswith('/workspace/'):
        p = _P('/workspace') / _P(path).name
    else:
        p = _P(path)
        if not p.is_absolute():
            p = _P('/workspace') / p

    result = {
        "path": str(p),
        "pages": None,
        "expected_pages": expected_pages,
        "blank_pages": [],
        "sparse_pages": [],
        "bleed_pages": [],
        "warnings": [],
        "ok": True,
        "message": "",
    }

    if not p.exists():
        result["ok"] = False
        result["message"] = f"File does not exist: {p}"
        print(f"[verify] FAIL: {result['message']}")
        return result

    suffix = p.suffix.lower()

    if suffix == ".pdf":
        if PdfReader is None:
            result["message"] = "PdfReader unavailable; skipped PDF verification."
            print(f"[verify] {result['message']}")
            return result
        try:
            reader = PdfReader(str(p))
            page_count = len(reader.pages)
            result["pages"] = page_count
        except Exception as e:
            result["ok"] = False
            result["message"] = f"Could not read PDF: {e}"
            print(f"[verify] FAIL: {result['message']}")
            return result

        if page_count == 0:
            result["ok"] = False
            result["message"] = "PDF has 0 pages."
            print(f"[verify] FAIL: {result['message']}")
            return result

        if expected_pages is not None and page_count != expected_pages:
            result["ok"] = False
            result["message"] = f"Page count mismatch: expected {expected_pages}, got {page_count}."

        if check_blank and convert_from_path is not None and np is not None:
            if page_count <= max_pages_to_scan:
                pages_to_scan = list(range(1, page_count + 1))
            else:
                step = page_count / float(max_pages_to_scan)
                pages_to_scan = sorted({int(i * step) + 1 for i in range(max_pages_to_scan)})
            for pno in pages_to_scan:
                try:
                    imgs = convert_from_path(str(p), first_page=pno, last_page=pno, dpi=50)
                except Exception:
                    continue
                if not imgs:
                    continue
                arr = np.asarray(imgs[0])
                gray = arr[..., :3].mean(axis=2) if arr.ndim == 3 else arr
                try:
                    txt = reader.pages[pno - 1].extract_text() or ""
                except Exception:
                    txt = ""
                if float(gray.std()) < 3.0:
                    if not txt.strip():
                        result["blank_pages"].append(pno)
                    continue
                ink = float((gray < 160).mean())
                if ink < 0.012 and len(txt.strip()) < 40:
                    result["sparse_pages"].append(pno)
                if float(gray.mean()) > 200:
                    h, w = gray.shape
                    b = max(3, int(min(h, w) * 0.02))
                    border = np.concatenate([
                        gray[:b, :].ravel(), gray[-b:, :].ravel(),
                        gray[:, :b].ravel(), gray[:, -b:].ravel(),
                    ])
                    if float((border < 160).mean()) > 0.02:
                        result["bleed_pages"].append(pno)
            if result["blank_pages"]:
                result["ok"] = False
                result["message"] = (result["message"] + f" Blank/near-empty pages detected: {result['blank_pages']}.").strip()
            if result["sparse_pages"]:
                result["warnings"].append(f"Sparse/near-empty pages (possible overflow or footer-only): {result['sparse_pages']}")
            if result["bleed_pages"]:
                result["warnings"].append(f"Content may bleed to the page edge (margins lost) on pages: {result['bleed_pages']}")

        if result["ok"] and not result["message"]:
            result["message"] = f"OK: {page_count} page(s), no blank pages detected."
        if result["warnings"]:
            result["message"] = (result["message"] + " WARNINGS: " + "; ".join(result["warnings"])).strip()

    elif suffix == ".docx":
        size = p.stat().st_size
        if size < 2000:
            result["ok"] = False
            result["message"] = f"DOCX looks too small ({size} bytes); may be empty."
        else:
            para = None
            if DocxDocument is not None:
                try:
                    doc = DocxDocument(str(p))
                    para = sum(1 for x in doc.paragraphs if x.text.strip())
                except Exception:
                    para = None
            result["message"] = (
                f"OK: DOCX present ({size} bytes"
                + (f", {para} non-empty paragraphs" if para is not None else "")
                + ")."
            )

    else:
        size = p.stat().st_size
        if size < 100:
            result["ok"] = False
            result["message"] = f"File looks too small ({size} bytes)."
        else:
            result["message"] = f"OK: file present ({size} bytes); no page-level check for {suffix or 'this type'}."

    print(f"[verify] {'OK' if result['ok'] else 'FAIL'}: {result['message']}")
    return result

# Alias for convenience
select_template = None  # Not available in sandbox - use create_document_from_template instead
DOCXManager = None  # Not available in sandbox - use create_document_from_template instead
get_template_path = None  # Not available in sandbox
TEMPLATE_METADATA = None  # Not available in sandbox

# Save original stdout
_original_stdout = sys.stdout

# Capture stdout
output_buffer = StringIO()
sys.stdout = output_buffer

# Crash fact for the host classifier. Success/failure must come from THIS
# flag (did the user code raise?), never from scanning the captured output
# for error-shaped strings — printing a script that happens to contain
# "Error:" (a build-script peek, a log grep) is a successful run.
_sb_crashed = False

# The agent's code is embedded as a string literal and exec'd here rather than
# being textually indented into this try-block. Naive line-by-line indentation
# (the old approach) corrupts multi-line string literals in the agent's code
# (e.g. triple-quoted file contents): every continuation line gains the wrapper
# indent, which silently mangled saved files and produced spurious
# IndentationErrors. compile() with a stable filename also yields tracebacks
# whose line numbers match the agent's own code. (Built by _embed_user_code so
# the exact embedding is unit-testable: tests/sandbox/test_python_exec_wrapper.py)
_USER_SOURCE = '\nd = json.loads(open(\'_trace2.json\').read())\nW, H = d[\'W\'], d[\'H\']\nG = {k: [(np.array(p[\'pts\'], float), p[\'hole\']) for p in v] for k, v in d[\'groups\'].items()}\ndef bbox(ps):\n    a = np.vstack([p for p,_ in ps]); return a[:,0].min(), a[:,1].min(), a[:,0].max(), a[:,1].max()\nbb = {k: bbox(v) for k, v in G.items()}\ndef path_d(ps):\n    return \'\'.join(\'M\'+\' \'.join(f\'{x:.1f},{y:.1f}\' for x,y in pts)+\'Z\' for pts,_ in ps)\nd_b, d_1, d_2 = path_d(G[\'badge\']), path_d(G[\'l1\']), path_d(G[\'l2\'])\nbx0,by0,bx1,by1 = bb[\'badge\']; cx, cy = (bx0+bx1)/2, (by0+by1)/2\nx1a,y1a,x1b,y1b = bb[\'l1\']; x2a,y2a,x2b,y2b = bb[\'l2\']\nPAD, SLIDE = 6, 14.0\nT = dict(bb_=0.00, bd=0.70, ob=0.05, od=0.35, l1b=0.60, l1d=0.50, l2b=0.85, l2d=0.60,\n         sb=1.70, sd=0.85, total=3.00)\nSH_X0, SH_X1, SH_W, SK = -650.0, 1780.0, 260.0, 18.0\n\ndef svg(color):\n    return f\'\'\'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Mark Wholesale Inc.">\n<title>Mark Wholesale Inc. \\u2014 animated logo intro</title>\n<defs>\n<path id="mwB" fill-rule="evenodd" d="{d_b}"/>\n<path id="mwT1" fill-rule="evenodd" d="{d_1}"/>\n<path id="mwT2" fill-rule="evenodd" d="{d_2}"/>\n<clipPath id="mwC1" clipPathUnits="userSpaceOnUse"><rect x="{x1a-PAD:.1f}" y="{y1a-PAD-SLIDE:.1f}" width="0" height="{(y1b-y1a)+2*PAD+2*SLIDE:.1f}"><animate attributeName="width" from="0" to="{(x1b-x1a)+2*PAD:.1f}" begin="{T[\'l1b\']}s" dur="{T[\'l1d\']}s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.16 0.84 0.24 1"/></rect></clipPath>\n<clipPath id="mwC2" clipPathUnits="userSpaceOnUse"><rect x="{x2a-PAD:.1f}" y="{y2a-PAD-SLIDE:.1f}" width="0" height="{(y2b-y2a)+2*PAD+2*SLIDE:.1f}"><animate attributeName="width" from="0" to="{(x2b-x2a)+2*PAD:.1f}" begin="{T[\'l2b\']}s" dur="{T[\'l2d\']}s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.16 0.84 0.24 1"/></rect></clipPath>\n<linearGradient id="mwSG" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.5" stop-color="#fff" stop-opacity="0.72"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>\n<mask id="mwSM" maskUnits="userSpaceOnUse" x="-900" y="-300" width="3400" height="1000"><g fill="#fff"><use href="#mwB"/><use href="#mwT1"/><use href="#mwT2"/></g></mask>\n</defs>\n<g style="fill:var(--mw-logo-color, {color})">\n<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin="{T[\'ob\']}s" dur="{T[\'od\']}s" fill="freeze"/>\n<g transform="translate({cx:.1f} {cy:.1f}) scale(0.62) translate({-cx:.1f} {-cy:.1f})">\n<animateTransform attributeName="transform" type="translate" values="0 0" begin="{T[\'bb_\']}s" dur="0.001s" fill="freeze"/>\n<use href="#mwB"/></g></g>\n<g opacity="0" transform="translate(0 {SLIDE:.0f})"><animate attributeName="opacity" from="0" to="1" begin="{T[\'l1b\']}s" dur="0.25s" fill="freeze"/>\n<animateTransform attributeName="transform" type="translate" values="0 {SLIDE:.0f};0 0" begin="{T[\'l1b\']}s" dur="{T[\'l1d\']}s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.16 0.84 0.24 1"/>\n<g clip-path="url(#mwC1)"><use href="#mwT1"/></g></g>\n<g opacity="0" transform="translate(0 {SLIDE:.0f})"><animate attributeName="opacity" from="0" to="1" begin="{T[\'l2b\']}s" dur="0.25s" fill="freeze"/>\n<animateTransform attributeName="transform" type="translate" values="0 {SLIDE:.0f};0 0" begin="{T[\'l2b\']}s" dur="{T[\'l2d\']}s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.16 0.84 0.24 1"/>\n<g clip-path="url(#mwC2)"><use href="#mwT2"/></g></g>\n</g>\n<g mask="url(#mwSM)" style="pointer-events:none"><rect x="{SH_X0:.0f}" y="-120" width="{SH_W:.0f}" height="620" fill="url(#mwSG)" transform="skewX(-{SK:.0f})"><animate attributeName="x" from="{SH_X0:.0f}" to="{SH_X1:.0f}" begin="{T[\'sb\']}s" dur="{T[\'sd\']}s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.45 0 0.55 1"/></rect></g>\n</svg>\n\'\'\'\n# proper pop-in on badge: nested group so scale animates around its own centre\ndef svg_fixed(color):\n    s = svg(color)\n    old = f\'\'\'<g transform="translate({cx:.1f} {cy:.1f}) scale(0.62) translate({-cx:.1f} {-cy:.1f})">\n<animateTransform attributeName="transform" type="translate" values="0 0" begin="{T[\'bb_\']}s" dur="0.001s" fill="freeze"/>\n<use href="#mwB"/></g>\'\'\'\n    new = f\'\'\'<g transform="translate({cx:.1f} {cy:.1f})"><g transform="scale(0.62)"><animateTransform attributeName="transform" type="scale" values="0.62;1.05;1" keyTimes="0;0.7;1" begin="{T[\'bb_\']}s" dur="{T[\'bd\']}s" fill="freeze" calcMode="spline" keySplines="0.14 0.9 0.2 1;0.4 0 0.6 1"/><g transform="translate({-cx:.1f} {-cy:.1f})"><use href="#mwB"/></g></g></g>\'\'\'\n    assert old in s, \'patch anchor missing\'\n    return s.replace(old, new)\n\nfor fn, col in [(\'MarkWholesale_logo_intro.svg\',\'#000\'), (\'MarkWholesale_logo_intro_white.svg\',\'#fff\')]:\n    out = svg_fixed(col); open(fn,\'w\').write(out); print(fn, len(out), \'bytes\')\n\ns = open(\'MarkWholesale_logo_intro.svg\').read()\nstack, ok = [], True\nfor m in re.finditer(r\'<(/?)([a-zA-Z][\\w:-]*)([^>]*?)(/?)>\', s):\n    c, tg, _, sc = m.groups()\n    if c:\n        if not stack or stack.pop() != tg: ok = False\n    elif not sc: stack.append(tg)\nprint(\'balanced:\', ok, \'leftover:\', stack, \'| animate:\', s.count(\'<animate\'), \'| animateTransform:\', s.count(\'<animateTransform\'))\n\n# ---------------- re-render preview frames from refined vectors ----------------\nfor f in glob.glob(\'_afr_*.png\') + glob.glob(\'_wfr_*.png\'): os.remove(f)\nFPS = 30; nfr = int(round(FPS*T[\'total\'])); CW, CH = 1600, 420\nOX, OY = (CW-W)/2.0, (CH-H)/2.0; SS = 2\neo  = lambda t: 1-(1-t)**3\neio = lambda t: 4*t**3 if t < .5 else 1-((-2*t+2)**3)/2\nseg = lambda n,b,dd: min(max((n-b)/dd,0.0),1.0)\ndef fill(cv_, ps, ox, oy, sc=1.0, ct=None, dy=0.0):\n    O,Hl = [],[]\n    for pts, hole in ps:\n        q = pts.copy()\n        if sc != 1.0 and ct is not None: q = (q-np.array(ct))*sc+np.array(ct)\n        q[:,1] += dy\n        q = np.round((q+np.array([ox,oy]))*SS).astype(np.int32)\n        (Hl if hole else O).append(q)\n    if O: cv2.fillPoly(cv_, O, 255)\n    if Hl: cv2.fillPoly(cv_, Hl, 0)\nXX, YY = np.meshgrid(np.arange(CW)+0.5, np.arange(CH)+0.5)\nsk = math.tan(math.radians(SK))\nwf = []\nfor i in range(nfr):\n    t = i/FPS; big = np.zeros((CH*SS, CW*SS), np.uint8)\n    p = seg(t, T[\'bb_\'], T[\'bd\'])\n    if p > 0:\n        sc = 0.62+(1.05-0.62)*eo(p/0.7) if p <= 0.7 else 1.05+(1.0-1.05)*eio((p-0.7)/0.3)\n        lay = np.zeros_like(big); fill(lay, G[\'badge\'], OX, OY, sc, (cx, cy))\n        big = np.maximum(big, (lay.astype(np.float32)*seg(t, T[\'ob\'], T[\'od\'])).astype(np.uint8))\n    for k, b, dd, xa, xb in ((\'l1\', T[\'l1b\'], T[\'l1d\'], x1a-PAD, x1b+PAD),\n                             (\'l2\', T[\'l2b\'], T[\'l2d\'], x2a-PAD, x2b+PAD)):\n        pr = seg(t, b, dd)\n        if pr <= 0: continue\n        e = eo(pr); lay = np.zeros_like(big)\n        fill(lay, G[k], OX, OY, 1.0, None, SLIDE*(1-e))\n        lay[:, int(round((xa+(xb-xa)*e+OX)*SS)):] = 0\n        big = np.maximum(big, (lay.astype(np.float32)*min(max((t-b)/0.25,0),1)).astype(np.uint8))\n    cov = cv2.resize(big, (CW, CH), interpolation=cv2.INTER_AREA).astype(np.float32)/255.0\n    rgb = np.zeros((CH, CW, 3), np.float32)\n    ps_ = seg(t, T[\'sb\'], T[\'sd\'])\n    if 0 < ps_ < 1:\n        bxp = SH_X0+(SH_X1-SH_X0)*ps_+OX\n        u = XX - sk*(YY-CH/2.0)\n        band = np.clip(1-np.abs((u-(bxp+SH_W/2))/(SH_W/2)), 0, 1)\n        rgb += ((np.sin(band*math.pi/2)**2)*0.72)[:, :, None]\n    c = (np.clip(rgb,0,1)*255).astype(np.uint8)\n    white = (255*(1-cov[:,:,None]) + c.astype(np.float32)*cov[:,:,None]).astype(np.uint8)\n    fn = f\'_wfr_{i:04d}.png\'; Image.fromarray(white,\'RGB\').save(fn); wf.append(fn)\n    Image.fromarray(np.dstack([c,(cov*255).astype(np.uint8)]),\'RGBA\').save(f\'_afr_{i:04d}.png\')\nprint(\'frames:\', nfr)\n\nGWid = 800\nims = []\nfor f in wf:\n    im = Image.open(f).convert(\'RGB\')\n    im = im.resize((GWid, int(round(im.height*GWid/im.width))), Image.LANCZOS)\n    ims.append(im.convert(\'P\', palette=Image.ADAPTIVE, colors=64))\nims[0].save(\'MarkWholesale_logo_intro_preview.gif\', save_all=True,\n            append_images=ims[1:]+[ims[-1].copy()], duration=[33]*len(ims)+[1400],\n            loop=0, optimize=True, disposal=2)\nprint(\'gif bytes:\', os.path.getsize(\'MarkWholesale_logo_intro_preview.gif\'))\nImage.open(wf[-1]).convert(\'RGB\').save(\'_qc_end2.png\')\nprint(\'qc still saved\')\n'
try:
    exec(compile(_USER_SOURCE, "<user_code>", "exec"), globals())
except BaseException as e:
    # Catch BaseException (not just Exception) so a user/helper `raise SystemExit`
    # / sys.exit(1) is reported as an error instead of silently aborting before
    # the END marker prints (which made a failed run look like success). A CLEAN
    # exit (sys.exit() or sys.exit(0), i.e. a falsy code) is NOT an error — let it
    # fall through to the markers so it's still reported as success.
    import traceback as _sb_tb
    if not (isinstance(e, SystemExit) and not e.code):
        _sb_crashed = True
        print(f"Error: {type(e).__name__}: {e}")
        _sb_tb.print_exc(file=output_buffer)

# IMPORTANT: Restore stdout before printing results
sys.stdout = _original_stdout

# Output the captured content
print("__SANDBOX_OUTPUT_START__")
print(output_buffer.getvalue())
print("__SANDBOX_OUTPUT_END__")
# Emitted AFTER the END marker so user-printed text (always between START and
# END) can never spoof or suppress it: this line is the ONLY thing the host
# may treat as "the code raised".
if _sb_crashed:
    print("__SANDBOX_EXC__")

# List created files for syncing (with error handling). Walk recursively so a
# deliverable the agent wrote into a SUBDIR (e.g. /workspace/<sid>/file.docx) is
# reported and synced instead of silently vanishing — the host flattens these to
# the workspace root on copy-back. Heavy/irrelevant dirs are pruned and depth is
# capped so the listing can't explode.
print("__SANDBOX_FILES_START__")
try:
    _skip_dirs = ("node_modules", ".git", "__pycache__", "venv", ".venv", "site-packages", ".cache")
    for _root, _dirs, _fnames in os.walk("/workspace"):
        _dirs[:] = [_d for _d in _dirs if _d not in _skip_dirs]
        for _fn in _fnames:
            if _fn.startswith("_"):
                continue
            _full = os.path.join(_root, _fn)
            if not os.path.isfile(_full):
                continue
            _rel = os.path.relpath(_full, "/workspace")
            if _rel.count("/") > 2:  # cap subdir depth
                continue
            print(_rel)
except Exception as files_err:
    print(f"FILES_ERROR: {files_err}")
print("__SANDBOX_FILES_END__")

# Silent write failures detected by the subprocess wrapper (a command exited 0
# but its output file never landed). The host turns a non-empty section into a
# hard error so a phantom write can never be reported as success.
print("__SANDBOX_WRITE_FAILURES_START__")
try:
    # Fail SILENT on listing errors: a non-empty section forces success=False
    # on the host, so only real, positively-recorded failures may appear here.
    # The isinstance guards keep user code that shadowed the name (e.g. with a
    # string, which would iterate per-character) from fabricating failures.
    # END-OF-CALL RE-CHECK: report only entries whose file is STILL missing —
    # a write the code retried and recovered must not fail a healthy call.
    _wv_ls = globals().get("_sc_write_verify_failures")
    for _wv_item in (_wv_ls if isinstance(_wv_ls, list) else []):
        try:
            _wv_disp, _wv_ap = _wv_item
            if (not os.path.exists(_wv_ap)) or os.path.getsize(_wv_ap) == 0:
                print(_wv_disp)
        except Exception:
            pass
except Exception:
    pass
print("__SANDBOX_WRITE_FAILURES_END__")

# QC-frame provenance: which VIDEO files ffmpeg extracted image frames from
# this call (basename|size). The host compares these against the videos
# actually delivered so a "frame-verified" claim can't describe a stale file.
print("__SANDBOX_QC_READS_START__")
try:
    _qc_ds = globals().get("_sc_qc_frame_reads")
    for _qn, _qs in (_qc_ds if isinstance(_qc_ds, dict) else {}).items():
        print(str(_qn) + "|" + str(_qs))
except Exception:
    pass
print("__SANDBOX_QC_READS_END__")

# List scratch (underscore-prefixed) files. These PERSIST across calls (synced
# back to the session workspace) but are HIDDEN from the user — never surfaced
# as attachments/deliverables.
print("__SANDBOX_SCRATCH_FILES_START__")
try:
    for f in os.listdir("/workspace"):
        if f.startswith("_") and os.path.isfile(f"/workspace/{f}"):
            print(f)
except Exception as scratch_err:
    print(f"SCRATCH_ERROR: {scratch_err}")
print("__SANDBOX_SCRATCH_FILES_END__")

# List PDF conversion requests
print("__SANDBOX_PDF_CONVERSIONS_START__")
try:
    for docx_path in _pdf_conversion_requests:
        print(docx_path)
except Exception as pdf_err:
    print(f"PDF_ERROR: {pdf_err}")
print("__SANDBOX_PDF_CONVERSIONS_END__")

# List template document requests
print("__SANDBOX_TEMPLATE_DOCS_START__")
try:
    for request_json in _template_document_requests:
        print(request_json)
except Exception as tpl_err:
    print(f"TEMPLATE_ERROR: {tpl_err}")
print("__SANDBOX_TEMPLATE_DOCS_END__")

# List edit document requests
print("__SANDBOX_EDIT_DOCS_START__")
try:
    for request_json in _edit_document_requests:
        print(request_json)
except Exception as edit_err:
    print(f"EDIT_ERROR: {edit_err}")
print("__SANDBOX_EDIT_DOCS_END__")

# List HTML -> PDF render requests
print("__SANDBOX_HTML_PDFS_START__")
try:
    for request_json in _html_pdf_requests:
        print(request_json)
except Exception as html_err:
    print(f"HTML_PDF_ERROR: {html_err}")
print("__SANDBOX_HTML_PDFS_END__")

# List structured document render requests
print("__SANDBOX_RENDER_DOCS_START__")
try:
    for request_json in _render_document_requests:
        print(request_json)
except Exception as rdoc_err:
    print(f"RENDER_DOC_ERROR: {rdoc_err}")
print("__SANDBOX_RENDER_DOCS_END__")

# List EPUB build requests
print("__SANDBOX_EPUB_BUILDS_START__")
try:
    for request_json in _epub_build_requests:
        print(request_json)
except Exception as epub_err:
    print(f"EPUB_BUILD_ERROR: {epub_err}")
print("__SANDBOX_EPUB_BUILDS_END__")
