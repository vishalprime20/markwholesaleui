const REPO_BASE = "/markwholesaleui";

function normalizeBase(value: string | undefined): string {
  if (!value) return "";
  return value.replace(/\/$/, "");
}

/**
 * GitHub Pages project URL is /markwholesaleui/.
 * Prefer Next's inlined router basePath — NEXT_PUBLIC_* set inside
 * next.config.ts is too late and stays empty, so /media 404s at github.io.
 */
export function getBasePath(): string {
  const fromNext = normalizeBase(process.env.__NEXT_ROUTER_BASEPATH);
  if (fromNext) return fromNext;

  const fromEnv = normalizeBase(process.env.NEXT_PUBLIC_BASE_PATH);
  if (fromEnv) return fromEnv;

  if (typeof window !== "undefined") {
    const path = window.location.pathname;
    if (path === REPO_BASE || path.startsWith(`${REPO_BASE}/`)) return REPO_BASE;
  }

  return "";
}

export function withBase(path: string): string {
  if (!path.startsWith("/") || path.startsWith("//")) return path;
  const base = getBasePath();
  if (!base) return path;
  if (path === base || path.startsWith(`${base}/`)) return path;
  return `${base}${path}`;
}
