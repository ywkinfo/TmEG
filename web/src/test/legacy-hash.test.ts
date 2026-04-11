import { describe, expect, it, vi } from "vitest";

import { applyLegacyHashRedirect, getLegacyRedirectHash } from "../lib/legacy-hash";

describe("legacy hash support", () => {
  it("rewrites old chapter and section params into hash-router paths", () => {
    expect(getLegacyRedirectHash("#chapter=제1장-목적&section=1-심사기준의-목적")).toBe(
      "#/chapter/%EC%A0%9C1%EC%9E%A5-%EB%AA%A9%EC%A0%81/1-%EC%8B%AC%EC%82%AC%EA%B8%B0%EC%A4%80%EC%9D%98-%EB%AA%A9%EC%A0%81"
    );
  });

  it("ignores already-normalized hash-router paths", () => {
    expect(getLegacyRedirectHash("#/chapter/제1장-목적")).toBeNull();
  });

  it("replaces the current location with the canonical hash-router URL", () => {
    const replaceState = vi.fn();

    const redirected = applyLegacyHashRedirect(
      {
        hash: "#chapter=제1장-목적&section=1-심사기준의-목적",
        pathname: "/TmEG/web/",
        search: "?preview=1",
      },
      { replaceState }
    );

    expect(redirected).toBe(true);
    expect(replaceState).toHaveBeenCalledWith(
      null,
      "",
      "/TmEG/web/?preview=1#/chapter/%EC%A0%9C1%EC%9E%A5-%EB%AA%A9%EC%A0%81/1-%EC%8B%AC%EC%82%AC%EA%B8%B0%EC%A4%80%EC%9D%98-%EB%AA%A9%EC%A0%81"
    );
  });
});
