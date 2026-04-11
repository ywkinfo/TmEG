from __future__ import annotations

import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from .common import GENERATED_DIR, load_config, load_generated_json, print_json_summary


NOTEBOOKLM_DIR = GENERATED_DIR / "notebooklm"
PROVENANCE_DERIVED = "search-index.json, toc.json, image-manifest.json"

PART_OUTPUT_SPECS = (
    {"index": 1, "title": "제1부 총칙", "filename": "03-제1부-총칙.md"},
    {"index": 2, "title": "제2부 상표등록출원", "filename": "04-제2부-상표등록출원.md"},
    {"index": 3, "title": "제3부 출원의 보정·분할·변경", "filename": "05-제3부-출원의-보정·분할·변경.md"},
    {"index": 4, "title": "제4부 상표등록의 요건", "filename": "06-제4부-상표등록의-요건.md"},
    {"index": 5, "title": "제5부(상)", "filename": "07-제5부(상).md", "endBeforeLabel": "제13장"},
    {"index": 5, "title": "제5부(하)", "filename": "08-제5부(하).md", "startLabel": "제13장"},
    {"index": 6, "title": "제6부 심사일반", "filename": "09-제6부-심사일반.md"},
    {"index": 7, "title": "제7부 상표 이외의 권리", "filename": "10-제7부-상표-이외의-권리.md"},
    {"index": 8, "title": "제8부 비전형상표", "filename": "11-제8부-비전형상표.md"},
    {"index": 9, "title": "제9부 국제상표 특례", "filename": "12-제9부-국제상표-특례.md"},
    {"index": 10, "title": "제10부 보칙", "filename": "13-제10부-보칙.md"},
)

DOT_LEADER_RE = re.compile(r"[·ㆍ.]{2,}.*$")
WHITESPACE_RE = re.compile(r"\s+")
ARTICLE_REF_RE = re.compile(r"제\s*\d+\s*조(?:\s*의\s*\d+)?(?:\s*제\s*\d+\s*항)?(?:\s*제\s*\d+\s*호)?")
INLINE_LAW_REF_RE = re.compile(
    r"법\s*제\s*\d+\s*조(?:\s*의\s*\d+)?(?:\s*제\s*\d+\s*항)?(?:\s*제\s*\d+\s*호)?"
)
SECTION_STYLE_LAW_REF_RE = re.compile(
    r"법\s*§\s*(\d+)(?:\s*의\s*(\d+))?(?:\s*([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]))?(?:\s*(\d+))?"
)
LAW_BLOCK_RE = re.compile(r"^【([^】]+)】$")

CIRCLED_DIGITS = {
    "①": 1,
    "②": 2,
    "③": 3,
    "④": 4,
    "⑤": 5,
    "⑥": 6,
    "⑦": 7,
    "⑧": 8,
    "⑨": 9,
    "⑩": 10,
    "⑪": 11,
    "⑫": 12,
    "⑬": 13,
    "⑭": 14,
    "⑮": 15,
    "⑯": 16,
    "⑰": 17,
    "⑱": 18,
    "⑲": 19,
    "⑳": 20,
}


def normalize_line(value: str) -> str:
    return WHITESPACE_RE.sub(" ", value.replace("\x00", " ")).strip()


def collapse_spaced_syllables(value: str) -> str:
    tokens = value.split(" ")
    collapsed: list[str] = []
    buffer: list[str] = []

    for token in tokens:
        if re.fullmatch(r"[가-힣]", token):
            buffer.append(token)
            continue

        if buffer:
            collapsed.append("".join(buffer))
            buffer = []
        collapsed.append(token)

    if buffer:
        collapsed.append("".join(buffer))

    return " ".join(part for part in collapsed if part)


def clean_title(value: str) -> str:
    stripped = DOT_LEADER_RE.sub("", value).strip()
    normalized = normalize_line(stripped)
    return collapse_spaced_syllables(normalized)


def normalize_outline_title(value: str) -> str:
    return normalize_line(DOT_LEADER_RE.sub("", value).strip())


def normalize_article_ref(value: str) -> str:
    return re.sub(r"\s+", "", value)


def is_trademark_law_label(label: str | None) -> bool:
    return bool(label) and normalize_line(label).startswith("상표법")


def convert_section_style_ref(match: re.Match[str]) -> str:
    article = f"제{match.group(1)}조"
    if match.group(2):
        article += f"의{match.group(2)}"

    paragraph = match.group(3)
    if paragraph:
        article += f"제{CIRCLED_DIGITS[paragraph]}항"

    item = match.group(4)
    if item:
        article += f"제{item}호"

    return article


def article_sort_key(value: str) -> tuple[int, int, int, int]:
    normalized = normalize_article_ref(value)
    match = re.fullmatch(r"제(\d+)조(?:의(\d+))?(?:제(\d+)항)?(?:제(\d+)호)?", normalized)
    if match is None:
        return (10**9, 0, 0, 0)
    return tuple(int(part or 0) for part in match.groups(default="0"))


def build_provenance_lines(source_pdf: str, generated_date: str) -> list[str]:
    return [
        f"> 출처 PDF: {source_pdf}",
        f"> 생성일: {generated_date}",
        f"> 파생 문서: {PROVENANCE_DERIVED}",
        "",
    ]


def strip_running_header(
    text: str,
    part_title: str,
    chapter_title: str,
    page_code: str | None,
    section_title: str,
) -> str:
    lines = [normalize_line(line) for line in text.splitlines()]
    lines = [line for line in lines if line]
    header_titles = {
        clean_title(part_title),
        clean_title(chapter_title),
    }
    compact_page_code = (page_code or "").replace(" ", "")

    while lines:
        current = lines[0]
        if clean_title(current) in header_titles:
            lines.pop(0)
            continue
        if compact_page_code and current.replace(" ", "") == compact_page_code:
            lines.pop(0)
            continue
        break

    if lines and clean_title(lines[0]) == clean_title(section_title):
        lines.pop(0)

    return "\n".join(lines).strip()


def render_section_body(entry: dict[str, Any]) -> str:
    return strip_running_header(
        text=str(entry.get("text", "")),
        part_title=str(entry.get("partTitle", "")),
        chapter_title=str(entry.get("chapterTitle", "")),
        page_code=str(entry.get("pageCode") or ""),
        section_title=str(entry.get("sectionTitle", "")),
    )


def build_image_page_index(image_manifest: dict[str, Any]) -> list[int]:
    pages = {
        int(page_number)
        for image in image_manifest.get("images", [])
        for page_number in image.get("pageNumbers", [])
    }
    return sorted(pages)


def collect_image_pages(image_pages: list[int], start_page: int | None, end_page: int | None) -> list[int]:
    if start_page is None or end_page is None:
        return []
    return [page_number for page_number in image_pages if start_page <= page_number <= end_page]


def format_page_list(page_numbers: list[int]) -> str:
    return ", ".join(str(page_number) for page_number in page_numbers)


def build_document_guide(
    config: dict[str, Any],
    search_index: list[dict[str, Any]],
    toc: dict[str, Any],
    generated_date: str,
) -> str:
    lines = build_provenance_lines(config["sourcePdf"], generated_date)
    lines.extend(
        [
            "# 문서안내",
            "",
            "이 문서는 NotebookLM 최종 입력을 위한 중간 산출물(로컬 생성본)입니다.",
            "실제 Google Docs 반영 전 단계 산출물이며, 이미지 블록은 PDF 페이지 참조만 제공합니다.",
            "",
            "## 기준",
            f"- 원문 기준: {config['documentTitle']}",
            (
                "- 부/장/항 구조: "
                f"{toc['meta']['partCount']}부 / {toc['meta']['chapterCount']}장 / {toc['meta']['itemCount']}항"
            ),
            f"- 검색 항목 수: {len(search_index)}",
            "- 구성: 00 문서안내 / 01 구조맵 / 02 법령참조표 / 03~13 부별 문서 / 99 원본 PDF",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_structure_map(config: dict[str, Any], toc: dict[str, Any], generated_date: str) -> str:
    lines = build_provenance_lines(config["sourcePdf"], generated_date)
    lines.extend(["# 구조맵", ""])

    for part in toc["parts"]:
        lines.append(f"- {normalize_outline_title(part['fullTitle'])}")
        for chapter in part["chapters"]:
            lines.append(f"  - {clean_title(chapter['fullTitle'])}")
            for item in chapter.get("items", []):
                lines.append(f"    - {clean_title(item['fullTitle'])} ({item['pageCode']})")
            for supplement in chapter.get("supplements", []):
                lines.append(f"    - {clean_title(supplement['fullTitle'])}")
                for item in supplement.get("items", []):
                    lines.append(f"      - {clean_title(item['fullTitle'])} ({item['pageCode']})")

    return "\n".join(lines).rstrip() + "\n"


def extract_law_refs(text: str) -> list[str]:
    refs: list[str] = []
    current_law_label: str | None = None

    for raw_line in text.splitlines():
        line = normalize_line(raw_line)
        if not line:
            continue

        law_block_match = LAW_BLOCK_RE.match(line)
        if law_block_match:
            current_law_label = law_block_match.group(1)
            continue

        if is_trademark_law_label(current_law_label):
            refs.extend(normalize_article_ref(match.group(0)) for match in ARTICLE_REF_RE.finditer(line))

        if current_law_label is None or is_trademark_law_label(current_law_label):
            refs.extend(
                normalize_article_ref(match.group(0).replace("법", "", 1))
                for match in INLINE_LAW_REF_RE.finditer(line)
            )
            refs.extend(convert_section_style_ref(match) for match in SECTION_STYLE_LAW_REF_RE.finditer(line))

    deduped: list[str] = []
    seen: set[str] = set()
    for ref in refs:
        if ref in seen:
            continue
        seen.add(ref)
        deduped.append(ref)
    return deduped


def build_law_reference_rows(search_index: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str, str, str, str]] = set()

    for order, entry in enumerate(search_index):
        section_title = "개요" if entry.get("entryType") == "overview" else clean_title(entry["sectionTitle"])
        for ref in extract_law_refs(str(entry.get("text", ""))):
            row_key = (
                ref,
                normalize_outline_title(str(entry.get("partTitle", ""))),
                clean_title(str(entry.get("chapterTitle", ""))),
                section_title,
                str(entry.get("pageCode") or ""),
            )
            if row_key in seen:
                continue
            seen.add(row_key)
            rows.append(
                {
                    "lawRef": ref,
                    "partTitle": row_key[1],
                    "chapterTitle": row_key[2],
                    "sectionTitle": row_key[3],
                    "pageCode": row_key[4],
                    "order": order,
                }
            )

    rows.sort(key=lambda row: (article_sort_key(row["lawRef"]), row["order"]))
    return rows


def build_law_reference_table(
    config: dict[str, Any], search_index: list[dict[str, Any]], generated_date: str
) -> str:
    lines = build_provenance_lines(config["sourcePdf"], generated_date)
    lines.extend(["# 법령참조표", "", "| 법령조문 | 부 | 장 | 항 | pageCode |", "| --- | --- | --- | --- | --- |"])

    for row in build_law_reference_rows(search_index):
        lines.append(
            "| {lawRef} | {partTitle} | {chapterTitle} | {sectionTitle} | {pageCode} |".format(**row)
        )

    return "\n".join(lines).rstrip() + "\n"


def build_pdf_pointer(config: dict[str, Any], generated_date: str) -> str:
    lines = build_provenance_lines(config["sourcePdf"], generated_date)
    lines.extend(
        [
            "# 원본 PDF",
            "",
            "노트북LM 본문 품질 보완용으로 PDF 직접 참조가 필요할 때 사용할 대조 자료입니다.",
            f"- 경로: {config['sourcePdf']}",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def slice_chapters(
    chapters: list[dict[str, Any]],
    start_label: str | None = None,
    end_before_label: str | None = None,
) -> list[dict[str, Any]]:
    start_index = 0
    if start_label is not None:
        start_index = next(
            index for index, chapter in enumerate(chapters) if str(chapter.get("label")) == start_label
        )

    end_index = len(chapters)
    if end_before_label is not None:
        end_index = next(
            index for index, chapter in enumerate(chapters) if str(chapter.get("label")) == end_before_label
        )

    return chapters[start_index:end_index]


def build_part_documents(
    config: dict[str, Any],
    search_index: list[dict[str, Any]],
    toc: dict[str, Any],
    image_manifest: dict[str, Any],
    generated_date: str,
) -> dict[str, str]:
    image_pages = build_image_page_index(image_manifest)
    entries_by_chapter: dict[str, list[dict[str, Any]]] = {}

    for entry in search_index:
        if entry.get("entryType") == "overview":
            continue
        chapter_slug = str(entry["chapterSlug"])
        entries_by_chapter.setdefault(chapter_slug, []).append(entry)

    documents: dict[str, str] = {}
    for spec in PART_OUTPUT_SPECS:
        toc_part = toc["parts"][spec["index"] - 1]
        chapters = toc_part["chapters"]
        chapters = slice_chapters(
            chapters=chapters,
            start_label=spec.get("startLabel"),
            end_before_label=spec.get("endBeforeLabel"),
        )

        lines = build_provenance_lines(config["sourcePdf"], generated_date)
        lines.extend([f"# {spec['title']}", ""])

        for chapter in chapters:
            chapter_entries = entries_by_chapter.get(chapter["id"], [])
            if not chapter_entries:
                continue

            chapter_start = min(int(entry["pageStart"]) for entry in chapter_entries if entry.get("pageStart") is not None)
            chapter_end = max(
                int(entry.get("pageEnd") or entry["pageStart"])
                for entry in chapter_entries
                if entry.get("pageStart") is not None
            )

            lines.append(
                f"## {clean_title(chapter['fullTitle'])} ({chapter['pageCode']}, pp. {chapter_start}-{chapter_end})"
            )

            for entry in chapter_entries:
                section_title = clean_title(entry["sectionTitle"])
                lines.extend([f"### {section_title}", ""])

                body = render_section_body(entry)
                if body:
                    lines.extend(body.splitlines())

                section_image_pages = collect_image_pages(
                    image_pages,
                    int(entry.get("pageStart") or 0) or None,
                    int(entry.get("pageEnd") or entry.get("pageStart") or 0) or None,
                )
                if section_image_pages:
                    lines.extend(
                        [
                            "",
                            "#### 이미지 참고",
                            (
                                "이 섹션에는 시각 자료가 있으며 원본 PDF의 "
                                f"{format_page_list(section_image_pages)} 페이지를 참고하라."
                            ),
                        ]
                    )

                lines.append("")

            chapter_image_pages = collect_image_pages(image_pages, chapter_start, chapter_end)
            if chapter_image_pages:
                lines.append(f"- 섹션 이미지 참고 페이지: {format_page_list(chapter_image_pages)}")
                lines.append("")

        documents[spec["filename"]] = "\n".join(lines).rstrip() + "\n"

    return documents


def prepare_output_dir(output_dir: Path = NOTEBOOKLM_DIR) -> Path:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def export_notebooklm(
    config: dict[str, Any],
    search_index: list[dict[str, Any]],
    toc: dict[str, Any],
    image_manifest: dict[str, Any],
    output_dir: Path = NOTEBOOKLM_DIR,
    generated_date: str | None = None,
) -> dict[str, Any]:
    output_path = prepare_output_dir(output_dir)
    export_date = generated_date or os.environ.get("NOTEBOOKLM_EXPORT_DATE") or datetime.now().date().isoformat()

    documents: dict[str, str] = {
        "00-문서안내.md": build_document_guide(config, search_index, toc, export_date),
        "01-구조맵.md": build_structure_map(config, toc, export_date),
        "02-법령참조표.md": build_law_reference_table(config, search_index, export_date),
        **build_part_documents(config, search_index, toc, image_manifest, export_date),
        "99-원본-PDF.md": build_pdf_pointer(config, export_date),
    }

    for filename, content in documents.items():
        (output_path / filename).write_text(content, encoding="utf-8")

    law_row_count = max(len(documents["02-법령참조표.md"].splitlines()) - 8, 0)
    return {
        "outputDir": str(output_path),
        "fileCount": len(documents),
        "lawRowCount": law_row_count,
    }


def main() -> None:
    config = load_config()
    search_index = load_generated_json("search-index.json")
    toc = load_generated_json("toc.json")
    image_manifest = load_generated_json("image-manifest.json")
    summary = export_notebooklm(
        config=config,
        search_index=search_index,
        toc=toc,
        image_manifest=image_manifest,
    )
    print_json_summary("notebooklm-export", summary)


if __name__ == "__main__":
    main()
