/** Repo name used as GitHub Pages project path. */
export const REPO_NAME = "markwholesaleui";

export function getBasePath() {
  return process.env.NEXT_PUBLIC_BASE_PATH ?? "";
}

export function withBase(path: string) {
  const base = getBasePath();
  if (!path.startsWith("/") || path.startsWith("//")) return path;
  if (base && (path === base || path.startsWith(`${base}/`))) return path;
  return `${base}${path}`;
}
