from __future__ import annotations

import re
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .common import GENERATED_DIR, clean_title, load_config, load_generated_json, normalize_space


PART_FILENAME = {
    1: "03-제1부-총칙.md",
    2: "04-제2부-상표등록출원.md",
    3: "05-제3부-출원의-보정·분할·변경.md",
    4: "06-제4부-상표등록의-요건.md",
    6: "09-제6부-심사일반.md",
    7: "10-제7부-상표-이외의-권리.md",
    8: "11-제8부-비전형상표.md",
    9: "12-제9부-국제상표-특례.md",
    10: "13-제10부-보칙.md",
}


DOC_TITLE = {
    1: "제1부 총칙",
    2: "제2부 상표등록출원",
    3: "제3부 출원의 보정·분할·변경",
    4: "제4부 상표등록의 요건",
    5: "제5부",
    6: "제6부 심사일반",
    7: "제7부 상표 이외의 권리",
    8: "제8부 비전형상표",
    9: "제9부 국제상표 특례",
    10: "제10부 보칙",
}


CHAPTER_PREFIX_RE = re.compile(r"제\s*(\d+)\s*장")
PART_PREFIX_RE = re.compile(r"제\s*(\d+)\s*부")
LAW_REF_RE = re.compile(
    r"제\s*\d+\s*조(?:의\d+)?(?:제\d+항(?:의[가-하]목)?(?:제\d+호)?)?"
)
DROPPABLE_HEADER_RE = re.compile(r"\.{3,}|···|…")


def _normalize_markdown_title(value: str) -> str:
    return clean_title(DROPPABLE_HEADER_RE.sub("", value or ""))


def _provenance(config: dict[str, Any]) -> str:
    return (
        f"> 출처 PDF: {config.get('sourcePdf', '알 수 없음')}\n"
        f"> 생성일: {datetime.now(UTC).strftime('%Y-%m-%d')}\n"
        "> 파생 문서: search-index.json, toc.json, image-manifest.json"
    )


def _page_span(start: int | None, end: int | None) -> str:
    if start is None:
        return ""
    if end is None or start == end:
        return str(start)
    return f"{start}-{end}"


def _page_index_from_images(image_manifest: dict[str, Any]) -> dict[int, set[int]]:
    pages: dict[int, set[int]] = defaultdict(set)
    for image in image_manifest.get("images", []):
        for page in image.get("pageNumbers", []):
            if isinstance(page, int):
                pages[page].add(page)
    return pages


def _find_section_image_pages(
    image_page_index: dict[int, set[int]],
    start: int | None,
    end: int | None,
) -> list[int]:
    if start is None or end is None:
        return []

    if start > end:
        start, end = end, start

    pages: set[int] = set()
    for page in range(start, end + 1):
        if page in image_page_index:
            pages.update(image_page_index[page])
    return sorted(pages)


def _format_pages(pages: list[int]) -> str:
    if not pages:
        return ""
    return ", ".join(str(page) for page in pages)


def _strip_running_text(text: str, chapter_title: str, section_title: str, page_code: str | None) -> str:
    from .common import strip_running_header

    if not text:
        return ""

    cleaned = strip_running_header(
        text,
        chapter_title=_normalize_markdown_title(chapter_title),
        section_title=_normalize_markdown_title(section_title),
        page_code=page_code,
    )

    lines = [line.strip() for line in cleaned.splitlines()]
    filtered: list[str] = []
    for line in lines:
        if not line:
            if filtered and filtered[-1] == "":
                continue
            filtered.append("")
            continue
        filtered.append(line)

    while filtered and filtered[0] == "":
        filtered.pop(0)
    while filtered and filtered[-1] == "":
        filtered.pop()
    return "\n".join(filtered)


def _to_paragraphs(text: str) -> list[str]:
    chunks = [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]
    return [normalize_space(chunk) if "\n" not in chunk else chunk for chunk in chunks]


def _build_section_text(entry: dict[str, Any], chapter_title: str) -> list[str]:
    section_title = _normalize_markdown_title(entry.get("sectionTitle", ""))
    page_code = entry.get("pageCode")

    heading = f"### {section_title}"
    if page_code:
        heading += f" ({page_code})"

    lines = [heading]

    body = _strip_running_text(
        entry.get("text", ""),
        chapter_title=chapter_title,
        section_title=section_title,
        page_code=page_code,
    )
    if body:
        lines.extend("", _to_paragraphs(body))

    return lines


def _build_chapter_text(
    chapter: dict[str, Any],
    chapter_entries: list[dict[str, Any]],
    image_page_index: dict[int, set[int]],
) -> tuple[str, list[int]]:
    chapter_title = _normalize_markdown_title(chapter.get("fullTitle", ""))
    if chapter_entries:
        start = min(entry.get("pageStart", 0) for entry in chapter_entries if entry.get("pageStart") is not None)
        end = max(entry.get("pageEnd", 0) for entry in chapter_entries if entry.get("pageEnd") is not None)
    else:
        start = chapter.get("pageStart")
        end = chapter.get("pageEnd")

    chapter_heading = f"## {chapter_title}"
    chapter_page_code = chapter.get("pageCode")
    if chapter_page_code:
        chapter_heading += f" ({chapter_page_code}, pp. {_page_span(start, end)})"
    elif start is not None:
        chapter_heading += f" (pp. {_page_span(start, end)})"

    lines = [chapter_heading]
    chapter_image_pages: list[int] = []

    for entry in chapter_entries:
        if entry.get("text", "") is None:
            continue
        lines.extend(_build_section_text(entry, chapter_title))
        image_pages = _find_section_image_pages(
            image_page_index,
            entry.get("pageStart"),
            entry.get("pageEnd"),
        )
        chapter_image_pages.extend(image_pages)

        if image_pages:
            lines.append("")
            lines.append("#### 이미지 참고")
            lines.append(
                f"이 섹션에는 시각 자료가 있으며 원본 PDF의 {_format_pages(image_pages)} 페이지를 참고하라."
            )

    return "\n".join(lines) + "\n", sorted(set(chapter_image_pages))


def _build_part_document(
    title: str,
    chapters: list[dict[str, Any]],
    section_map: dict[str, list[dict[str, Any]]],
    image_page_index: dict[int, set[int]],
    provenance: str,
) -> str:
    parts: list[str] = [provenance, "", f"# {title}"]
    any_written = False

    for chapter in chapters:
        entries = section_map.get(chapter.get("id"), [])
        if not entries:
            continue

        any_written = True
        chapter_text, chapter_image_pages = _build_chapter_text(
            chapter,
            entries,
            image_page_index,
        )
        parts.append("")
        parts.append(chapter_text.rstrip("\n"))

        if chapter_image_pages:
            parts.append(f"- 섹션 이미지 참고 페이지: {_format_pages(chapter_image_pages)}")

    if not any_written:
        parts.append("")
        parts.append("- 본문 항목이 없습니다.")

    return "\n".join(parts) + "\n"


def _parse_chapter_no(chapter: dict[str, Any]) -> int | None:
    full_title = chapter.get("fullTitle", "") or ""
    match = CHAPTER_PREFIX_RE.search(full_title)
    if not match:
        return None
    return int(match.group(1))


def _split_part_5(chapters: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    upper: list[dict[str, Any]] = []
    lower: list[dict[str, Any]] = []

    for chapter in chapters:
        number = _parse_chapter_no(chapter)
        if number is None:
            lower.append(chapter)
            continue
        if number <= 12:
            upper.append(chapter)
        else:
            lower.append(chapter)

    return upper, lower


def _build_structure_map(toc: dict[str, Any]) -> str:
    lines = ["# 구조맵", ""]
    for part in toc.get("parts", []):
        lines.append(f"- {part.get('fullTitle', part.get('label', ''))}")
        for chapter in part.get("chapters", []):
            lines.append(f"  - {_normalize_markdown_title(chapter.get('fullTitle', ''))}")
            for item in chapter.get("items", []):
                lines.append(f"    - {_normalize_markdown_title(item.get('fullTitle', ''))} ({item.get('pageCode', '')})")
            for supplement in chapter.get("supplements", []):
                lines.append(
                    f"    - {clean_title(supplement.get('fullTitle', ''))} ({supplement.get('pageCode', '')})"
                )
                for item in supplement.get("items", []):
                    lines.append(
                        f"      - {_normalize_markdown_title(item.get('fullTitle', ''))} ({item.get('pageCode', '')})"
                    )
    return "\n".join(lines) + "\n"


def _extract_law_refs(text: str) -> list[str]:
    if not text or "【상표법】" not in text:
        return []

    refs: list[str] = []
    seen: set[str] = set()
    for match in LAW_REF_RE.findall(text):
        ref = clean_title(match)
        if not ref or ref in seen:
            continue
        seen.add(ref)
        refs.append(ref)
    return refs


def _build_law_reference_table(search_index: list[dict[str, Any]]) -> str:
    rows: list[tuple[str, str, str, str, str | None]] = []
    seen: set[tuple[str, str, str, str | None, str | None]] = set()

    for entry in search_index:
        refs = _extract_law_refs(entry.get("text", ""))
        if not refs:
            continue
        part_title = entry.get("partTitle", "")
        chapter_title = _normalize_markdown_title(entry.get("chapterTitle", ""))
        section_title = _normalize_markdown_title(entry.get("sectionTitle", ""))
        page_code = entry.get("pageCode")

        for ref in refs:
            key = (ref, part_title, chapter_title, section_title, page_code)
            if key in seen:
                continue
            seen.add(key)
            rows.append(key)

    rows.sort(key=lambda row: (int(re.search(r"\d+", row[0]).group()) if re.search(r"\d+", row[0]) else 10_000, row[1]))

    lines = [
        "| 법령조문 | 부 | 장 | 항 | pageCode |",
        "| --- | --- | --- | --- | --- |",
    ]
    for law_ref, part_title, chapter_title, section_title, page_code in rows:
        lines.append(
            f"| {law_ref} | {part_title} | {chapter_title} | {section_title} | {page_code or ''} |"
        )

    if not rows:
        lines.append("| - | - | - | - | - |")

    return "\n".join(lines) + "\n"


def _build_guidance_document(config: dict[str, Any], toc: dict[str, Any], search_index: list[dict[str, Any]]) -> str:
    part_count = toc.get("meta", {}).get("partCount", 0)
    chapter_count = toc.get("meta", {}).get("chapterCount", 0)
    item_count = toc.get("meta", {}).get("itemCount", 0)

    return (
        f"{_provenance(config)}\n\n"
        + "# 문서안내\n\n"
        + "이 문서는 NotebookLM 최종 입력을 위한 중간 산출물(로컬 생성본)입니다.\n"
        + "실제 Google Docs 반영 전 단계 산출물이며, 이미지 블록은 PDF 페이지 참조만 제공합니다.\n\n"
        + "## 기준\n"
        + f"- 원문 기준: {config.get('documentTitle', '상표심사기준')}\n"
        + f"- 부/장/항 구조: {part_count}부 / {chapter_count}장 / {item_count}항\n"
        + f"- 검색 항목 수: {len(search_index)}\n"
        + "- 구성: 00 문서안내 / 01 구조맵 / 02 법령참조표 / 03~13 부별 문서 / 99 원본 PDF"
    )


def _build_section_map(search_index: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    section_map: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for entry in search_index:
        if entry.get("entryType") == "overview":
            continue
        section_map[entry["chapterSlug"]].append(entry)

    for entries in section_map.values():
        entries.sort(
            key=lambda item: (
                item.get("pageStart") or 0,
                item.get("sectionId") or "",
            )
        )

    return section_map


def main() -> None:
    config = load_config()
    toc = load_generated_json("toc.json")
    search_index = load_generated_json("search-index.json")
    image_manifest = load_generated_json("image-manifest.json")

    output_dir = GENERATED_DIR / "notebooklm"
    output_dir.mkdir(parents=True, exist_ok=True)

    provenance = _provenance(config)
    image_page_index = _page_index_from_images(image_manifest)
    section_map = _build_section_map(search_index)

    (output_dir / "00-문서안내.md").write_text(
        _build_guidance_document(config, toc, search_index) + "\n",
        encoding="utf-8",
    )
    (output_dir / "01-구조맵.md").write_text(
        f"{provenance}\n\n{_build_structure_map(toc)}\n",
        encoding="utf-8",
    )
    (output_dir / "02-법령참조표.md").write_text(
        f"{provenance}\n\n# 법령참조표\n\n{_build_law_reference_table(search_index)}",
        encoding="utf-8",
    )

    for part in toc.get("parts", []):
        part_title = part.get("fullTitle", "")
        part_no_match = PART_PREFIX_RE.match(part_title)
        if not part_no_match:
            continue
        part_no = int(part_no_match.group(1))

        if part_no == 5:
            upper, lower = _split_part_5(part.get("chapters", []))
            if upper:
                upper_text = _build_part_document(
                    "제5부(상)",
                    upper,
                    section_map,
                    image_page_index,
                    provenance,
                )
                (output_dir / "07-제5부(상).md").write_text(upper_text, encoding="utf-8")
            if lower:
                lower_text = _build_part_document(
                    "제5부(하)",
                    lower,
                    section_map,
                    image_page_index,
                    provenance,
                )
                (output_dir / "08-제5부(하).md").write_text(lower_text, encoding="utf-8")
            continue

        if part_no not in PART_FILENAME:
            continue

        doc_title = DOC_TITLE.get(part_no, part_title)
        chapters = part.get("chapters", [])
        part_text = _build_part_document(
            doc_title,
            chapters,
            section_map,
            image_page_index,
            provenance,
        )
        (output_dir / PART_FILENAME[part_no]).write_text(part_text, encoding="utf-8")

    source_pdf = Path(config.get("sourcePdf", ""))
    if source_pdf.exists():
        source_pdf_lines = [
            provenance,
            "",
            "# 원본 PDF",
            "",
            "노트북LM 본문 품질 보완용으로 PDF 직접 참조가 필요할 때 사용할 대조 자료입니다.",
            f"- 경로: {source_pdf.as_posix()}",
        ]
    else:
        source_pdf_lines = [
            provenance,
            "",
            "# 원본 PDF",
            "",
            "원본 PDF가 워크스페이스에 없어 로컬 참조가 불가합니다.",
            "- 필요 시 Google Docs 동기화 단계에서 원본 PDF를 별도 업로드합니다.",
        ]
    (output_dir / "99-원본-PDF.md").write_text("\n".join(source_pdf_lines) + "\n", encoding="utf-8")

    print(f"notebooklm export: output={output_dir}")


if __name__ == "__main__":
    main()
