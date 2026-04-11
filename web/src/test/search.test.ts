import { describe, expect, it } from "vitest";

import type { ReaderChapter } from "../lib/generated-data";
import { buildWarmedSearchState, resolveSearchNavigation, warmSearchEntries } from "../lib/search";

describe("search helpers", () => {
  it("falls back to a chapter route when section results are empty", () => {
    const chapters = [
      {
        id: "chapter-1",
        slug: "chapter-1",
        title: "제1장 목적",
        displayTitle: "제1장 목적",
        partTitle: "제1부 총 칙",
        summary: "요약",
        html: "",
        pageCode: "10101",
        pageStart: 1,
        pageEnd: 2,
        hasImage: false,
        imageCount: 0,
        headings: [],
        sectionCatalog: [
          {
            id: "chapter-1-overview",
            chapterSlug: "chapter-1",
            chapterTitle: "제1장 목적",
            partTitle: "제1부 총 칙",
            sectionId: "overview",
            sectionTitle: "개요",
            text: "요약",
            excerpt: "요약",
            entryType: "overview",
            pageCode: "10101",
            pageStart: 1,
            pageEnd: 1,
            hasImage: false,
            imageCount: 0,
            categories: [],
            routePath: "/chapter/chapter-1",
            compositeKey: "chapter-1-overview",
          },
        ],
        tocItemCount: 1,
      } satisfies ReaderChapter,
    ];

    const routePath = resolveSearchNavigation({
      query: "목적",
      results: [],
      activeIndex: 0,
      chapters,
    });

    expect(routePath).toBe("/chapter/chapter-1");
  });

  it("warms search entries with normalized haystacks", () => {
    const warmedEntries = warmSearchEntries([
      {
        id: "entry-1",
        chapterSlug: "chapter-1",
        chapterTitle: "제1장 목적",
        partTitle: "제1부 총 칙",
        sectionId: "overview",
        sectionTitle: "개요",
        text: "검색용 본문",
        excerpt: "요약",
        entryType: "overview",
        pageCode: "10101",
        pageStart: 1,
        pageEnd: 1,
        hasImage: false,
        imageCount: 0,
        categories: [],
        routePath: "/chapter/chapter-1",
        compositeKey: "entry-1",
      },
    ]);

    expect(warmedEntries[0]?.normalizedHaystack).toContain("검색용 본문");
  });

  it("returns explicit ready and empty warm states", () => {
    expect(
      buildWarmedSearchState([
        {
          id: "entry-1",
          chapterSlug: "chapter-1",
          chapterTitle: "제1장 목적",
          partTitle: "제1부 총 칙",
          sectionId: "overview",
          sectionTitle: "개요",
          text: "검색용 본문",
          excerpt: "요약",
          entryType: "overview",
          pageCode: "10101",
          pageStart: 1,
          pageEnd: 1,
          hasImage: false,
          imageCount: 0,
          categories: [],
          routePath: "/chapter/chapter-1",
          compositeKey: "entry-1",
        },
      ]).status
    ).toBe("ready");

    expect(buildWarmedSearchState([]).status).toBe("empty");
  });
});
