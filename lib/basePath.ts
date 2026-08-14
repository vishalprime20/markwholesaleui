/** Repo name used as GitHub Pages project path. */
export const REPO_NAME = "markwholesaleui";

export function getBasePath() {
  return process.env.NEXT_PUBLIC_BASE_PATH ?? "";
}

export function withBase(path: string) {
  if (!path.startsWith("/") || path.startsWith("//")) return path;
  return `${getBasePath()}${path}`;
}
