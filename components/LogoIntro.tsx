"use client";

import { withBase } from "@/lib/basePath";
import { motion, useReducedMotion } from "framer-motion";
import { useEffect, useState } from "react";

export const LOGO_WHITE = withBase("/media/logos/MarkWholesale_logo_transparent_white.png");
export const LOGO_DARK = withBase("/media/logos/MarkWholesale_logo_transparent.png");
export const LOGO_INTRO_DURATION_MS = 3400;

const FRAME_COUNT = 90;
const FRAME_FPS = 30;

function frameSrc(index: number) {
  return withBase(`/media/logos/anim-alpha/_afr_${String(index).padStart(4, "0")}.png`);
}

type LogoIntroProps = {
  onComplete: () => void;
};

export function LogoIntro({ onComplete }: LogoIntroProps) {
  const reduceMotion = useReducedMotion();
  const [frame, setFrame] = useState(0);
  const [ready, setReady] = useState(false);
  const [exiting, setExiting] = useState(false);

  useEffect(() => {
    if (reduceMotion) return;
    let cancelled = false;
    let loaded = 0;

    for (let i = 0; i < FRAME_COUNT; i++) {
      const img = new Image();
      img.onload = img.onerror = () => {
        loaded += 1;
        if (!cancelled && loaded >= FRAME_COUNT) setReady(true);
      };
      img.src = frameSrc(i);
    }

    const fallback = window.setTimeout(() => {
      if (!cancelled) setReady(true);
    }, 1500);

    return () => {
      cancelled = true;
      window.clearTimeout(fallback);
    };
  }, [reduceMotion]);

  useEffect(() => {
    if (reduceMotion) {
      onComplete();
      return;
    }
    if (!ready) return;

    let raf = 0;
    let start = 0;
    const tick = (t: number) => {
      if (!start) start = t;
      const elapsed = t - start;
      const next = Math.min(FRAME_COUNT - 1, Math.floor((elapsed / 1000) * FRAME_FPS));
      setFrame(next);
      if (next < FRAME_COUNT - 1) {
        raf = requestAnimationFrame(tick);
      }
    };
    raf = requestAnimationFrame(tick);

    const hold = window.setTimeout(() => {
      setExiting(true);
      window.setTimeout(onComplete, 180);
    }, LOGO_INTRO_DURATION_MS);

    return () => {
      cancelAnimationFrame(raf);
      window.clearTimeout(hold);
    };
  }, [onComplete, ready, reduceMotion]);

  if (reduceMotion) return null;

  return (
    <motion.div
      className="pointer-events-none fixed inset-0 z-[100] flex items-center justify-center bg-transparent"
      initial={{ opacity: 1 }}
      animate={{ opacity: exiting ? 0 : 1 }}
      transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
      aria-hidden
    >
      <motion.div
        className="relative flex w-full max-w-4xl flex-col items-center px-6 sm:px-10"
        initial={{ opacity: 0 }}
        animate={{ opacity: ready ? 1 : 0 }}
        transition={{ duration: 0.35 }}
      >
        {/* Alpha frames are black-on-transparent; invert for white logo over hero */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={ready ? frameSrc(frame) : LOGO_WHITE}
          alt=""
          className={`h-auto w-[min(88vw,640px)] ${ready ? "invert" : ""}`}
          draggable={false}
        />
      </motion.div>
    </motion.div>
  );
}

export function BrandMark({
  className = "h-9",
  variant = "white",
}: {
  className?: string;
  variant?: "white" | "dark";
}) {
  const src = variant === "white" ? LOGO_WHITE : LOGO_DARK;
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt="Mark Wholesale" className={`w-auto object-contain ${className}`} />
  );
}
