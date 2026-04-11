import { buildChapterPath, buildSectionPath } from "./formatters";

type RedirectLocation = Pick<Location, "hash" | "pathname" | "search">;
type RedirectHistory = Pick<History, "replaceState">;

export function getLegacyRedirectHash(hash: string): string | null {
  const normalizedHash = hash.startsWith("#") ? hash.slice(1) : hash;

  if (!normalizedHash || normalizedHash.startsWith("/")) {
    return null;
  }

  const params = new URLSearchParams(normalizedHash);
  const chapter = params.get("chapter");
  if (!chapter) {
    return null;
  }

  const section = params.get("section");
  const nextPath = section ? buildSectionPath(chapter, section) : buildChapterPath(chapter);
  return `#${nextPath}`;
}

export function redirectLegacyHash(hash: string): boolean {
  const redirectHash = getLegacyRedirectHash(hash);
  if (!redirectHash || redirectHash === window.location.hash) {
    return false;
  }

  window.location.hash = redirectHash.slice(1);
  return true;
}

export function applyLegacyHashRedirect(locationLike: RedirectLocation, historyLike: RedirectHistory): boolean {
  const redirectHash = getLegacyRedirectHash(locationLike.hash);
  if (!redirectHash || redirectHash === locationLike.hash) {
    return false;
  }

  historyLike.replaceState(null, "", `${locationLike.pathname}${locationLike.search}${redirectHash}`);
  return true;
}
