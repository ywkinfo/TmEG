export const CATEGORY_LABELS: Record<string, string> = {
  "related-law": "관련 법령",
  requirements: "적용 요건",
  caution: "유의사항",
  timing: "판단 시점",
  case: "사례·예시",
  supplement: "보충기준",
  procedure: "절차",
  "non-traditional-mark": "비전통 상표",
};

export function stripGuideDots(value: string | null | undefined): string {
  return String(value ?? "")
    .replace(/·+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function normalizeText(value: string | null | undefined): string {
  return stripGuideDots(value).toLowerCase();
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "미상";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(parsed);
}

export function formatPageRange(start: number | null | undefined, end: number | null | undefined): string {
  if (!start && !end) {
    return "페이지 미상";
  }

  if (!end || start === end) {
    return `p.${start}`;
  }

  return `p.${start}-${end}`;
}

export function getCategoryLabel(category: string): string {
  return CATEGORY_LABELS[category] ?? category;
}

export function buildChapterPath(chapterSlug: string): string {
  return `/chapter/${encodeURIComponent(chapterSlug)}`;
}

export function buildSectionPath(chapterSlug: string, sectionId: string): string {
  if (!sectionId || sectionId === "overview") {
    return buildChapterPath(chapterSlug);
  }

  return `${buildChapterPath(chapterSlug)}/${encodeURIComponent(sectionId)}`;
}

export function buildCompositeKey(input: {
  partTitle: string;
  chapterTitle: string;
  pageCode: string | null | undefined;
  pageStart: number | null | undefined;
  pageEnd: number | null | undefined;
  title: string;
}): string {
  return [
    normalizeText(input.partTitle),
    normalizeText(input.chapterTitle),
    String(input.pageCode ?? ""),
    String(input.pageStart ?? ""),
    String(input.pageEnd ?? ""),
    normalizeText(input.title),
  ].join("::");
}

export function buildChapterCompositeKey(input: {
  partTitle: string;
  chapterTitle: string;
  pageCode: string | null | undefined;
}): string {
  return [normalizeText(input.partTitle), normalizeText(input.chapterTitle), String(input.pageCode ?? "")].join(
    "::"
  );
}
