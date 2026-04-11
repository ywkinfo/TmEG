import { describe, expect, it } from "vitest";

import { adaptGeneratedData, resolveCanonicalChapterRoute } from "../lib/generated-data";

describe("adaptGeneratedData", () => {
  it("synthesizes overview entries and resolves exploration links with chapter-aware composite keys", () => {
    const data = adaptGeneratedData({
      manifest: {
        title: "상표심사기준",
        syncedAt: "2026-04-11T00:00:00.000Z",
        fileCount: 5,
        imageFileCount: 0,
      },
      toc: {
        meta: {
          title: "상표심사기준",
          partCount: 1,
          chapterCount: 2,
          itemCount: 2,
          supplementCount: 0,
        },
        parts: [
          {
            id: "part-1",
            label: "제1부",
            title: "총 칙",
            fullTitle: "제1부 총 칙",
            chapters: [
              {
                id: "chapter-a",
                label: "제1장",
                title: "제1장 목적",
                fullTitle: "제1장 목적",
                pageCode: "10101",
                items: [{ id: "shared-section" }],
                supplements: [],
              },
              {
                id: "chapter-b",
                label: "제2장",
                title: "제2장 심사",
                fullTitle: "제2장 심사",
                pageCode: "10201",
                items: [{ id: "shared-section" }],
                supplements: [],
              },
            ],
          },
        ],
      },
      documentData: {
        meta: {
          title: "상표심사기준",
          builtAt: "2026-04-11T00:00:00.000Z",
          chapterCount: 2,
          pageCount: 4,
          partCount: 1,
        },
        chapters: [
          {
            id: "chapter-a",
            slug: "chapter-a",
            title: "제1장 목적",
            summary: "첫 번째 장 요약",
            html: '<section id="overview"><h2>제1장 목적</h2></section><section id="shared-section"><h3>공통 항목</h3></section>',
            hasImage: false,
            imageCount: 0,
            headings: [{ id: "shared-section", depth: 3, title: "공통 항목" }],
            partTitle: "제1부 총 칙",
            pageCode: "10101",
            pageStart: 1,
            pageEnd: 2,
          },
          {
            id: "chapter-b",
            slug: "chapter-b",
            title: "제2장 심사",
            summary: "두 번째 장 요약",
            html: '<section id="overview"><h2>제2장 심사</h2></section><section id="shared-section"><h3>공통 항목</h3></section>',
            hasImage: false,
            imageCount: 0,
            headings: [{ id: "shared-section", depth: 3, title: "공통 항목" }],
            partTitle: "제1부 총 칙",
            pageCode: "10201",
            pageStart: 3,
            pageEnd: 4,
          },
        ],
      },
      searchIndex: [
        {
          id: "shared-section",
          chapterSlug: "chapter-a",
          chapterTitle: "제1장 목적",
          sectionId: "shared-section",
          sectionTitle: "공통 항목",
          text: "alpha",
          excerpt: "alpha excerpt",
          entryType: "item",
          partTitle: "제1부 총 칙",
          pageCode: "10101",
          pageStart: 2,
          pageEnd: 2,
          hasImage: false,
          imageCount: 0,
          categories: [],
        },
        {
          id: "shared-section",
          chapterSlug: "chapter-b",
          chapterTitle: "제2장 심사",
          sectionId: "shared-section",
          sectionTitle: "공통 항목",
          text: "beta",
          excerpt: "beta excerpt",
          entryType: "item",
          partTitle: "제1부 총 칙",
          pageCode: "10201",
          pageStart: 4,
          pageEnd: 4,
          hasImage: false,
          imageCount: 0,
          categories: ["procedure"],
        },
      ],
      explorationIndex: [
        {
          id: "shared-section",
          title: "공통 항목",
          chapterTitle: "제2장 심사",
          partTitle: "제1부 총 칙",
          categories: ["procedure"],
          pageCode: "10201",
          pageStart: 4,
          pageEnd: 4,
          hasImage: false,
          excerpt: "beta excerpt",
        },
      ],
    });

    expect(data.chapterMap.get("chapter-a")?.sectionCatalog[0]?.sectionId).toBe("overview");
    expect(data.chapterMap.get("chapter-b")?.sectionCatalog[0]?.sectionId).toBe("overview");
    expect(data.explorationEntries[0]?.routePath).toBe("/chapter/chapter-b/shared-section");
  });

  it("normalizes invalid section routes back to the canonical chapter route", () => {
    const data = adaptGeneratedData({
      manifest: {
        title: "상표심사기준",
        syncedAt: "2026-04-11T00:00:00.000Z",
        fileCount: 5,
        imageFileCount: 0,
      },
      toc: {
        meta: {
          title: "상표심사기준",
          partCount: 1,
          chapterCount: 1,
          itemCount: 1,
          supplementCount: 0,
        },
        parts: [
          {
            id: "part-1",
            label: "제1부",
            title: "총 칙",
            fullTitle: "제1부 총 칙",
            chapters: [
              {
                id: "chapter-a",
                label: "제1장",
                title: "제1장 목적",
                fullTitle: "제1장 목적",
                pageCode: "10101",
                items: [{ id: "section-1" }],
                supplements: [],
              },
            ],
          },
        ],
      },
      documentData: {
        meta: {
          title: "상표심사기준",
          builtAt: "2026-04-11T00:00:00.000Z",
          chapterCount: 1,
          pageCount: 2,
          partCount: 1,
        },
        chapters: [
          {
            id: "chapter-a",
            slug: "chapter-a",
            title: "제1장 목적",
            summary: "첫 번째 장 요약",
            html: '<section id="overview"><h2>제1장 목적</h2></section><section id="section-1"><h3>첫 항목</h3></section>',
            hasImage: false,
            imageCount: 0,
            headings: [{ id: "section-1", depth: 3, title: "첫 항목" }],
            partTitle: "제1부 총 칙",
            pageCode: "10101",
            pageStart: 1,
            pageEnd: 2,
          },
        ],
      },
      searchIndex: [
        {
          id: "section-1",
          chapterSlug: "chapter-a",
          chapterTitle: "제1장 목적",
          sectionId: "section-1",
          sectionTitle: "첫 항목",
          text: "alpha",
          excerpt: "alpha excerpt",
          entryType: "item",
          partTitle: "제1부 총 칙",
          pageCode: "10101",
          pageStart: 2,
          pageEnd: 2,
          hasImage: false,
          imageCount: 0,
          categories: [],
        },
      ],
      explorationIndex: [],
    });

    const chapter = data.chapterMap.get("chapter-a");
    expect(chapter).toBeDefined();

    const invalidSection = resolveCanonicalChapterRoute(chapter!, "does-not-exist");
    expect(invalidSection.activeSectionId).toBe("overview");
    expect(invalidSection.canonicalPath).toBe("/chapter/chapter-a");

    const overviewSection = resolveCanonicalChapterRoute(chapter!, "overview");
    expect(overviewSection.canonicalPath).toBe("/chapter/chapter-a");
  });
});
