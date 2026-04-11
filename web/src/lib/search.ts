import type { ReaderChapter, ReaderSectionEntry } from "./generated-data";
import { normalizeText } from "./formatters";

export type WarmedSearchEntry = ReaderSectionEntry & {
  normalizedSectionTitle: string;
  normalizedChapterTitle: string;
  normalizedExcerpt: string;
  normalizedText: string;
  normalizedHaystack: string;
};

export type SearchWarmStatus = "ready" | "empty";

export function warmSearchEntries(entries: ReaderSectionEntry[]): WarmedSearchEntry[] {
  return entries.map((entry) => ({
    ...entry,
    normalizedSectionTitle: normalizeText(entry.sectionTitle),
    normalizedChapterTitle: normalizeText(entry.chapterTitle),
    normalizedExcerpt: normalizeText(entry.excerpt),
    normalizedText: normalizeText(entry.text),
    normalizedHaystack: normalizeText(
      `${entry.sectionTitle} ${entry.chapterTitle} ${entry.partTitle} ${entry.excerpt} ${entry.text}`
    ),
  }));
}

export function buildWarmedSearchState(entries: ReaderSectionEntry[]): {
  status: SearchWarmStatus;
  entries: WarmedSearchEntry[];
} {
  const warmedEntries = warmSearchEntries(entries);

  return {
    status: warmedEntries.length > 0 ? "ready" : "empty",
    entries: warmedEntries,
  };
}

export function rankSearchResults(entries: WarmedSearchEntry[], query: string, limit = 10): WarmedSearchEntry[] {
  const normalizedQuery = normalizeText(query);
  if (!normalizedQuery) {
    return [];
  }

  return entries
    .map((entry) => {
      let score = 0;

      if (entry.normalizedSectionTitle.includes(normalizedQuery)) {
        score += 6;
      }
      if (entry.normalizedChapterTitle.includes(normalizedQuery)) {
        score += 4;
      }
      if (entry.normalizedExcerpt.includes(normalizedQuery)) {
        score += 2;
      }
      if (entry.normalizedText.includes(normalizedQuery)) {
        score += 1;
      }
      if (entry.entryType === "overview") {
        score += 1;
      }

      return score > 0 ? { entry, score } : null;
    })
    .filter((value): value is { entry: WarmedSearchEntry; score: number } => value !== null)
    .sort((left, right) => {
      if (right.score !== left.score) {
        return right.score - left.score;
      }

      return (left.entry.pageStart ?? 0) - (right.entry.pageStart ?? 0);
    })
    .slice(0, limit)
    .map(({ entry }) => entry);
}

export function resolveSearchNavigation(input: {
  query: string;
  results: Array<Pick<ReaderSectionEntry, "routePath">>;
  activeIndex: number;
  chapters: ReaderChapter[];
}): string | null {
  const normalizedQuery = normalizeText(input.query);
  if (!normalizedQuery) {
    return null;
  }

  const selectedResult = input.results[input.activeIndex];
  if (selectedResult) {
    return selectedResult.routePath;
  }

  if (input.results[0]) {
    return input.results[0].routePath;
  }

  const matchingChapter = input.chapters.find((chapter) => {
    const chapterHaystack = normalizeText(`${chapter.displayTitle} ${chapter.partTitle}`);
    return chapterHaystack.includes(normalizedQuery);
  });

  return matchingChapter?.sectionCatalog[0]?.routePath ?? null;
}
