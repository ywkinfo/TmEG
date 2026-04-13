import {
  buildChapterCompositeKey,
  buildChapterPath,
  buildCompositeKey,
  buildSectionPath,
  normalizeText,
  stripGuideDots,
} from "./formatters";

type GeneratedManifest = {
  title: string;
  syncedAt: string;
  fileCount: number;
  imageFileCount: number;
};

type GeneratedToc = {
  meta: {
    title: string;
    partCount: number;
    chapterCount: number;
    itemCount: number;
    supplementCount: number;
  };
  parts: GeneratedPart[];
};

type GeneratedPart = {
  id: string;
  label: string;
  title: string;
  fullTitle: string;
  chapters: GeneratedChapterToc[];
};

type GeneratedChapterToc = {
  id: string;
  label: string;
  title: string;
  fullTitle: string;
  pageCode: string;
  items: Array<{ id: string }>;
  supplements: Array<{ id: string }>;
};

type GeneratedDocumentData = {
  meta: {
    title: string;
    builtAt: string;
    chapterCount: number;
    pageCount: number;
    partCount: number;
  };
  chapters: GeneratedDocumentChapter[];
};

type GeneratedDocumentChapter = {
  id: string;
  slug: string;
  title: string;
  summary: string;
  html: string;
  hasImage: boolean;
  imageCount: number;
  headings: GeneratedHeading[];
  partTitle: string;
  pageCode: string;
  pageStart: number;
  pageEnd: number;
};

type GeneratedHeading = {
  id: string;
  depth: number;
  title: string;
};

type GeneratedSearchEntry = {
  id: string;
  chapterSlug: string;
  chapterTitle: string;
  sectionId: string;
  sectionTitle: string;
  text: string;
  excerpt: string;
  entryType: string;
  partTitle: string;
  pageCode: string | null;
  pageStart: number;
  pageEnd: number;
  hasImage: boolean;
  imageCount: number;
  categories?: string[];
};

type GeneratedExplorationEntry = {
  id: string;
  title: string;
  chapterTitle: string;
  partTitle: string;
  categories?: string[];
  pageCode: string | null;
  pageStart: number;
  pageEnd: number;
  hasImage: boolean;
  excerpt: string;
};

export type ReaderSectionEntry = {
  id: string;
  chapterSlug: string;
  chapterTitle: string;
  partTitle: string;
  sectionId: string;
  sectionTitle: string;
  text: string;
  excerpt: string;
  entryType: string;
  pageCode: string | null;
  pageStart: number;
  pageEnd: number;
  hasImage: boolean;
  imageCount: number;
  categories: string[];
  routePath: string;
  compositeKey: string;
};

export type ReaderChapter = {
  id: string;
  slug: string;
  title: string;
  displayTitle: string;
  partTitle: string;
  summary: string;
  html: string;
  pageCode: string;
  pageStart: number;
  pageEnd: number;
  hasImage: boolean;
  imageCount: number;
  headings: Array<{
    id: string;
    depth: number;
    title: string;
    displayTitle: string;
  }>;
  sectionCatalog: ReaderSectionEntry[];
  tocItemCount: number;
};

export type ReaderPart = {
  id: string;
  label: string;
  title: string;
  fullTitle: string;
  chapters: ReaderChapter[];
};

export type ReaderExplorationEntry = {
  id: string;
  title: string;
  displayTitle: string;
  chapterTitle: string;
  chapterDisplayTitle: string;
  partTitle: string;
  categories: string[];
  pageCode: string | null;
  pageStart: number;
  pageEnd: number;
  hasImage: boolean;
  imageCount: number;
  excerpt: string;
  routePath: string;
  chapterSlug: string | null;
  sectionId: string;
};

export type ReaderData = {
  manifest: GeneratedManifest;
  meta: GeneratedDocumentData["meta"];
  tocMeta: GeneratedToc["meta"];
  parts: ReaderPart[];
  chapters: ReaderChapter[];
  chapterMap: Map<string, ReaderChapter>;
  searchEntries: ReaderSectionEntry[];
  explorationEntries: ReaderExplorationEntry[];
  explorationCounts: Array<{ category: string; count: number }>;
};

export function resolveCanonicalChapterRoute(
  chapter: ReaderChapter,
  requestedSectionId: string | undefined
): { activeSectionId: string; canonicalPath: string } {
  const normalizedSectionId = requestedSectionId ?? chapter.sectionCatalog[0]?.sectionId ?? "overview";
  const matchingEntry = chapter.sectionCatalog.find((entry) => entry.sectionId === normalizedSectionId);

  if (matchingEntry) {
    return {
      activeSectionId: matchingEntry.sectionId,
      canonicalPath: matchingEntry.routePath,
    };
  }

  const fallbackEntry = chapter.sectionCatalog.find((entry) => entry.sectionId === "overview") ?? chapter.sectionCatalog[0];

  return {
    activeSectionId: fallbackEntry?.sectionId ?? "overview",
    canonicalPath: fallbackEntry?.routePath ?? buildChapterPath(chapter.slug),
  };
}

function generatedUrl(fileName: string): string {
  return new URL(`./generated/${fileName}`, document.baseURI).toString();
}

async function fetchJson<T>(fileName: string): Promise<T> {
  const response = await fetch(generatedUrl(fileName));
  if (!response.ok) {
    throw new Error(`Unable to load ${fileName} (${response.status}).`);
  }

  return (await response.json()) as T;
}

function toReaderSearchEntry(entry: GeneratedSearchEntry): ReaderSectionEntry {
  return {
    ...entry,
    categories: entry.categories ?? [],
    routePath: buildSectionPath(entry.chapterSlug, entry.sectionId),
    compositeKey: buildCompositeKey({
      partTitle: entry.partTitle,
      chapterTitle: entry.chapterTitle,
      pageCode: entry.pageCode,
      pageStart: entry.pageStart,
      pageEnd: entry.pageEnd,
      title: entry.sectionTitle,
    }),
  };
}

function synthesizeOverviewEntry(chapter: GeneratedDocumentChapter): ReaderSectionEntry {
  return {
    id: `${chapter.slug}-overview`,
    chapterSlug: chapter.slug,
    chapterTitle: chapter.title,
    partTitle: chapter.partTitle,
    sectionId: "overview",
    sectionTitle: "개요",
    text: chapter.summary,
    excerpt: chapter.summary,
    entryType: "overview",
    pageCode: chapter.pageCode,
    pageStart: chapter.pageStart,
    pageEnd: chapter.pageStart,
    hasImage: chapter.hasImage,
    imageCount: chapter.imageCount,
    categories: [],
    routePath: buildChapterPath(chapter.slug),
    compositeKey: buildCompositeKey({
      partTitle: chapter.partTitle,
      chapterTitle: chapter.title,
      pageCode: chapter.pageCode,
      pageStart: chapter.pageStart,
      pageEnd: chapter.pageStart,
      title: "개요",
    }),
  };
}

function countCategories(entries: ReaderExplorationEntry[]): Array<{ category: string; count: number }> {
  const counts = new Map<string, number>();

  for (const entry of entries) {
    for (const category of entry.categories) {
      counts.set(category, (counts.get(category) ?? 0) + 1);
    }
  }

  return [...counts.entries()]
    .map(([category, count]) => ({ category, count }))
    .sort((left, right) => {
      if (right.count !== left.count) {
        return right.count - left.count;
      }

      return left.category.localeCompare(right.category, "ko");
    });
}

export function adaptGeneratedData(input: {
  manifest: GeneratedManifest;
  toc: GeneratedToc;
  documentData: GeneratedDocumentData;
  searchIndex: GeneratedSearchEntry[];
  explorationIndex: GeneratedExplorationEntry[];
}): ReaderData {
  const chapterSourceMap = new Map(input.documentData.chapters.map((chapter) => [chapter.slug, chapter]));
  const rawSearchEntries = input.searchIndex.map(toReaderSearchEntry);
  const searchEntriesByChapter = new Map<string, ReaderSectionEntry[]>();

  for (const entry of rawSearchEntries) {
    const chapterEntries = searchEntriesByChapter.get(entry.chapterSlug) ?? [];
    chapterEntries.push(entry);
    searchEntriesByChapter.set(entry.chapterSlug, chapterEntries);
  }

  const parts: ReaderPart[] = input.toc.parts.map((part) => {
    const chapters = part.chapters.map((tocChapter) => {
      const chapter = chapterSourceMap.get(tocChapter.id);
      if (!chapter) {
        throw new Error(`toc.json chapter ${tocChapter.id} is missing from document-data.json.`);
      }

      const rawEntries = [...(searchEntriesByChapter.get(chapter.slug) ?? [])];
      if (!rawEntries.some((entry) => entry.sectionId === "overview")) {
        rawEntries.unshift(synthesizeOverviewEntry(chapter));
      }

      rawEntries.sort((left, right) => {
        const order = (entry: ReaderSectionEntry): number => {
          if (entry.entryType === "part-intro") {
            return 0;
          }
          if (entry.sectionId === "overview") {
            return 1;
          }
          return 2;
        };

        const leftOrder = order(left);
        const rightOrder = order(right);
        if (leftOrder !== rightOrder) {
          return leftOrder - rightOrder;
        }

        if (left.pageStart !== right.pageStart) {
          return (left.pageStart ?? 0) - (right.pageStart ?? 0);
        }

        return (left.pageStart ?? 0) - (right.pageStart ?? 0);
      });

      return {
        id: chapter.id,
        slug: chapter.slug,
        title: chapter.title,
        displayTitle: stripGuideDots(chapter.title),
        partTitle: chapter.partTitle,
        summary: chapter.summary,
        html: chapter.html,
        pageCode: chapter.pageCode,
        pageStart: chapter.pageStart,
        pageEnd: chapter.pageEnd,
        hasImage: chapter.hasImage,
        imageCount: chapter.imageCount,
        headings: chapter.headings.map((heading) => ({
          ...heading,
          displayTitle: stripGuideDots(heading.title),
        })),
        sectionCatalog: rawEntries,
        tocItemCount: tocChapter.items.length + tocChapter.supplements.length,
      } satisfies ReaderChapter;
    });

    return {
      id: part.id,
      label: part.label,
      title: part.title,
      fullTitle: part.fullTitle,
      chapters,
    } satisfies ReaderPart;
  });

  const chapters = parts.flatMap((part) => part.chapters);
  const chapterMap = new Map(chapters.map((chapter) => [chapter.slug, chapter]));
  const searchEntries = chapters.flatMap((chapter) => chapter.sectionCatalog);

  const searchKeyMap = new Map(searchEntries.map((entry) => [entry.compositeKey, entry]));
  const relaxedSearchKeyMap = new Map(
    searchEntries.map((entry) => [
      [normalizeText(entry.partTitle), normalizeText(entry.chapterTitle), normalizeText(entry.sectionTitle)].join("::"),
      entry,
    ])
  );

  const chapterKeyMap = new Map(
    chapters.map((chapter) => [
      buildChapterCompositeKey({
        partTitle: chapter.partTitle,
        chapterTitle: chapter.title,
        pageCode: chapter.pageCode,
      }),
      chapter,
    ])
  );

  const explorationEntries = input.explorationIndex.map((entry) => {
    const searchMatch =
      searchKeyMap.get(
        buildCompositeKey({
          partTitle: entry.partTitle,
          chapterTitle: entry.chapterTitle,
          pageCode: entry.pageCode,
          pageStart: entry.pageStart,
          pageEnd: entry.pageEnd,
          title: entry.title,
        })
      ) ??
      relaxedSearchKeyMap.get(
        [normalizeText(entry.partTitle), normalizeText(entry.chapterTitle), normalizeText(entry.title)].join("::")
      );

    const chapterMatch =
      searchMatch?.chapterSlug != null
        ? chapterMap.get(searchMatch.chapterSlug) ?? null
        : chapterKeyMap.get(
            buildChapterCompositeKey({
              partTitle: entry.partTitle,
              chapterTitle: entry.chapterTitle,
              pageCode: entry.pageCode,
            })
          ) ?? null;

    const chapterSlug = chapterMatch?.slug ?? searchMatch?.chapterSlug ?? null;
    const sectionId = searchMatch?.sectionId ?? "overview";

    return {
      id: entry.id,
      title: entry.title,
      displayTitle: stripGuideDots(entry.title),
      chapterTitle: entry.chapterTitle,
      chapterDisplayTitle: stripGuideDots(entry.chapterTitle),
      partTitle: entry.partTitle,
      categories: entry.categories ?? [],
      pageCode: entry.pageCode,
      pageStart: entry.pageStart,
      pageEnd: entry.pageEnd,
      hasImage: entry.hasImage,
      imageCount: searchMatch?.imageCount ?? (entry.hasImage ? 1 : 0),
      excerpt: entry.excerpt,
      routePath: chapterSlug ? buildSectionPath(chapterSlug, sectionId) : "/",
      chapterSlug,
      sectionId,
    } satisfies ReaderExplorationEntry;
  });

  return {
    manifest: input.manifest,
    meta: input.documentData.meta,
    tocMeta: input.toc.meta,
    parts,
    chapters,
    chapterMap,
    searchEntries,
    explorationEntries,
    explorationCounts: countCategories(explorationEntries),
  };
}

let cachedReaderData: Promise<ReaderData> | null = null;

export async function loadGeneratedData(): Promise<ReaderData> {
  if (!cachedReaderData) {
    cachedReaderData = Promise.all([
      fetchJson<GeneratedManifest>("manifest.json"),
      fetchJson<GeneratedToc>("toc.json"),
      fetchJson<GeneratedDocumentData>("document-data.json"),
      fetchJson<GeneratedSearchEntry[]>("search-index.json"),
      fetchJson<GeneratedExplorationEntry[]>("exploration-index.json"),
    ]).then(([manifest, toc, documentData, searchIndex, explorationIndex]) =>
      adaptGeneratedData({ manifest, toc, documentData, searchIndex, explorationIndex })
    );
  }

  return cachedReaderData;
}
