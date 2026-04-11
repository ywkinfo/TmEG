from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from .common import (
    load_config,
    load_generated_json,
    load_page_texts,
    make_excerpt,
    open_pdf,
    print_json_summary,
    text_to_html,
    write_json,
)


def build_code_to_page_map(
    inventory: dict[str, Any], toc_pages: set[int] | None = None
) -> dict[str, int]:
    toc_page_set = toc_pages or set()
    mapping: dict[str, int] = {}
    for page in inventory["pages"]:
        page_code = page.get("pageCode")
        page_number = page["pageNumber"]
        if not page_code:
            continue
        if page_code not in mapping:
            mapping[page_code] = page_number
            continue
        current_page_number = mapping[page_code]
        if current_page_number in toc_page_set and page_number not in toc_page_set:
            mapping[page_code] = page_number
    return mapping


def resolve_page_start(
    page_code_map: dict[str, int],
    primary_page_code: str | None,
    fallback_page_codes: list[str] | None = None,
    fallback_page_start: int | None = None,
) -> tuple[int | None, bool]:
    if primary_page_code and primary_page_code in page_code_map:
        return page_code_map[primary_page_code], False
    if fallback_page_codes:
        for page_code in fallback_page_codes:
            if page_code in page_code_map:
                return page_code_map[page_code], True
    if fallback_page_start is not None:
        return fallback_page_start, True
    return None, False


def assign_ranges(entries: list[dict[str, Any]], default_end_page: int) -> list[dict[str, Any]]:
    resolved = [entry for entry in entries if entry.get("pageStart") is not None]

    for index, entry in enumerate(resolved):
        current_start = entry["pageStart"]
        next_start = resolved[index + 1]["pageStart"] if index + 1 < len(resolved) else None
        if next_start is None:
            entry["pageEnd"] = default_end_page
            continue
        entry["pageEnd"] = max(current_start, next_start - 1)

    return entries


def join_page_range(
    page_texts: dict[int, str],
    start_page: int | None,
    end_page: int | None,
    excluded_pages: set[int] | None = None,
) -> str:
    if start_page is None or end_page is None:
        return ""
    excluded_page_set = excluded_pages or set()
    chunks: list[str] = []
    for page_number in range(start_page, end_page + 1):
        if page_number in excluded_page_set:
            continue
        text = page_texts.get(page_number, "").strip()
        if text:
            chunks.append(text)
    return "\n\n".join(chunks).strip()


def classify_entry(entry: dict[str, Any]) -> list[str]:
    title = entry["sectionTitle"]
    categories: list[str] = []
    rules = {
        "related-law": ["관련 법령"],
        "requirements": ["적용요건", "요건"],
        "caution": ["판단시 유의사항", "유의사항"],
        "timing": ["판단시점"],
        "case": ["사례", "예시"],
        "supplement": ["보충기준"],
        "procedure": ["출원", "보정", "분할", "변경", "심사"],
        "non-traditional-mark": ["입체상표", "색채만으로 된 상표", "홀로그램상표", "동작상표", "냄새상표"],
    }
    for label, needles in rules.items():
        if any(needle in title for needle in needles):
            categories.append(label)
    return categories


def build_headings(chapter: dict[str, Any]) -> list[dict[str, Any]]:
    headings: list[dict[str, Any]] = []
    for item in chapter["items"]:
        headings.append(
            {
                "id": item["id"],
                "depth": 3,
                "title": item["fullTitle"],
                "children": [],
            }
        )
    for supplement in chapter["supplements"]:
        children = [
            {
                "id": item["id"],
                "depth": 4,
                "title": item["fullTitle"],
                "children": [],
            }
            for item in supplement["items"]
        ]
        headings.append(
            {
                "id": supplement["id"],
                "depth": 3,
                "title": supplement["fullTitle"],
                "children": children,
            }
        )
    return headings


def main() -> None:
    config = load_config()
    inventory = load_generated_json("pdf-inventory.json")
    toc = load_generated_json("toc.json")
    reader = open_pdf(config)
    page_texts = load_page_texts(reader)
    toc_pages = set(toc["meta"].get("tocPages", []))
    page_code_map = build_code_to_page_map(inventory, toc_pages)
    default_end_page = inventory["meta"]["pageCount"]

    chapters_in_order: list[dict[str, Any]] = []
    section_entries: list[dict[str, Any]] = []
    missing_page_codes: list[str] = []

    for part in toc["parts"]:
        for chapter in part["chapters"]:
            chapter_start, chapter_used_fallback = resolve_page_start(page_code_map, chapter["pageCode"])
            if chapter_start is None:
                missing_page_codes.append(chapter["pageCode"])
            chapter_record = {
                "id": chapter["id"],
                "slug": chapter["id"],
                "title": chapter["fullTitle"],
                "partTitle": part["fullTitle"],
                "pageCode": chapter["pageCode"],
                "pageStart": chapter_start,
                "pageEnd": None,
                "raw": chapter,
                "usedFallbackPageStart": chapter_used_fallback,
            }
            chapters_in_order.append(chapter_record)

            section_entries.append(
                {
                    "id": f"{chapter['id']}-overview",
                    "chapterSlug": chapter["id"],
                    "chapterTitle": chapter["fullTitle"],
                    "sectionId": "overview",
                    "sectionTitle": "개요",
                    "entryType": "overview",
                    "partTitle": part["fullTitle"],
                    "pageCode": chapter["pageCode"],
                    "pageStart": chapter_start,
                    "pageEnd": None,
                    "usedFallbackPageStart": chapter_used_fallback,
                }
            )

            for item in chapter["items"]:
                item_start, item_used_fallback = resolve_page_start(page_code_map, item["pageCode"])
                if item_start is None:
                    missing_page_codes.append(item["pageCode"])
                section_entries.append(
                    {
                        "id": item["id"],
                        "chapterSlug": chapter["id"],
                        "chapterTitle": chapter["fullTitle"],
                        "sectionId": item["id"],
                        "sectionTitle": item["fullTitle"],
                        "entryType": "item",
                        "partTitle": part["fullTitle"],
                        "pageCode": item["pageCode"],
                        "pageStart": item_start,
                        "pageEnd": None,
                        "usedFallbackPageStart": item_used_fallback,
                    }
                )

            for supplement in chapter["supplements"]:
                supplement_fallback_codes = [item["pageCode"] for item in supplement["items"]]
                supplement_start, supplement_used_fallback = resolve_page_start(
                    page_code_map,
                    supplement["pageCode"],
                    fallback_page_codes=supplement_fallback_codes,
                    fallback_page_start=chapter_start,
                )
                if supplement_start is None:
                    missing_page_codes.append(supplement["pageCode"])
                section_entries.append(
                    {
                        "id": supplement["id"],
                        "chapterSlug": chapter["id"],
                        "chapterTitle": chapter["fullTitle"],
                        "sectionId": supplement["id"],
                        "sectionTitle": supplement["fullTitle"],
                        "entryType": "supplement",
                        "partTitle": part["fullTitle"],
                        "pageCode": supplement["pageCode"],
                        "pageStart": supplement_start,
                        "pageEnd": None,
                        "usedFallbackPageStart": supplement_used_fallback,
                    }
                )
                for item in supplement["items"]:
                    item_start, item_used_fallback = resolve_page_start(page_code_map, item["pageCode"])
                    if item_start is None:
                        missing_page_codes.append(item["pageCode"])
                    section_entries.append(
                        {
                            "id": item["id"],
                            "chapterSlug": chapter["id"],
                            "chapterTitle": chapter["fullTitle"],
                            "sectionId": item["id"],
                            "sectionTitle": item["fullTitle"],
                            "entryType": "item",
                            "partTitle": part["fullTitle"],
                            "pageCode": item["pageCode"],
                            "pageStart": item_start,
                            "pageEnd": None,
                            "usedFallbackPageStart": item_used_fallback,
                        }
                    )

    chapters_in_order = assign_ranges(chapters_in_order, default_end_page)
    section_entries = assign_ranges(section_entries, default_end_page)
    section_entries_by_chapter: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in section_entries:
        entry_text = join_page_range(
            page_texts,
            entry["pageStart"],
            entry["pageEnd"],
            excluded_pages=toc_pages,
        )
        entry["text"] = entry_text
        entry["excerpt"] = make_excerpt(entry_text)
        entry["categories"] = classify_entry(entry)
        section_entries_by_chapter[entry["chapterSlug"]].append(entry)

    built_chapters: list[dict[str, Any]] = []
    for chapter_record in chapters_in_order:
        chapter_sections = section_entries_by_chapter[chapter_record["slug"]]
        chapter_text = join_page_range(
            page_texts,
            chapter_record["pageStart"],
            chapter_record["pageEnd"],
            excluded_pages=toc_pages,
        )
        html_parts = [
            "<section id=\"overview\">",
            f"<h2>{chapter_record['title']}</h2>",
            text_to_html(chapter_text),
            "</section>",
        ]
        for entry in chapter_sections:
            if entry["entryType"] == "overview":
                continue
            heading_tag = "h3" if entry["entryType"] != "item" or "보충기준" in entry["sectionTitle"] else "h3"
            html_parts.extend(
                [
                    f"<section id=\"{entry['sectionId']}\">",
                    f"<{heading_tag}>{entry['sectionTitle']}</{heading_tag}>",
                    text_to_html(entry["text"]),
                    "</section>",
                ]
            )
        built_chapters.append(
            {
                "id": chapter_record["id"],
                "slug": chapter_record["slug"],
                "title": chapter_record["title"],
                "summary": make_excerpt(chapter_text),
                "html": "\n".join(html_parts),
                "headings": build_headings(chapter_record["raw"]),
                "partTitle": chapter_record["partTitle"],
                "pageCode": chapter_record["pageCode"],
                "pageStart": chapter_record["pageStart"],
                "pageEnd": chapter_record["pageEnd"],
            }
        )

    search_index = [
        {
            "id": entry["id"],
            "chapterSlug": entry["chapterSlug"],
            "chapterTitle": entry["chapterTitle"],
            "sectionId": entry["sectionId"],
            "sectionTitle": entry["sectionTitle"],
            "text": entry["text"],
            "excerpt": entry["excerpt"],
            "entryType": entry["entryType"],
            "partTitle": entry["partTitle"],
            "pageCode": entry["pageCode"],
            "pageStart": entry["pageStart"],
            "pageEnd": entry["pageEnd"],
            "categories": entry["categories"],
        }
        for entry in section_entries
        if entry["text"]
    ]

    exploration_index = [
        {
            "id": entry["id"],
            "title": entry["sectionTitle"],
            "chapterTitle": entry["chapterTitle"],
            "partTitle": entry["partTitle"],
            "categories": entry["categories"],
            "pageCode": entry["pageCode"],
            "pageStart": entry["pageStart"],
            "pageEnd": entry["pageEnd"],
            "excerpt": entry["excerpt"],
        }
        for entry in search_index
        if entry["categories"]
    ]

    document_data = {
        "meta": {
            "title": config["documentTitle"],
            "builtAt": datetime.now(UTC).isoformat(),
            "chapterCount": len(built_chapters),
            "pageCount": inventory["meta"]["pageCount"],
            "partCount": toc["meta"]["partCount"],
        },
        "chapters": built_chapters,
    }

    coverage_report = {
        "meta": {
            "title": config["documentTitle"],
        },
        "inventoryPageCount": inventory["meta"]["pageCount"],
        "tocPartCount": toc["meta"]["partCount"],
        "tocChapterCount": toc["meta"]["chapterCount"],
        "tocItemCount": toc["meta"]["itemCount"],
        "tocSupplementCount": toc["meta"]["supplementCount"],
        "mappedChapterCount": sum(1 for chapter in built_chapters if chapter["pageStart"] is not None),
        "unmappedChapterCount": sum(1 for chapter in built_chapters if chapter["pageStart"] is None),
        "mappedSectionCount": sum(1 for entry in section_entries if entry["pageStart"] is not None),
        "unmappedSectionCount": sum(1 for entry in section_entries if entry["pageStart"] is None),
        "fallbackPageStartCount": sum(1 for entry in section_entries if entry["usedFallbackPageStart"]),
        "missingPageCodes": sorted(set(code for code in missing_page_codes if code)),
    }

    write_json("document-data.json", document_data)
    write_json("search-index.json", search_index)
    write_json("exploration-index.json", exploration_index)
    target = write_json("coverage-report.json", coverage_report)
    print_json_summary(
        "content",
        {
            "target": str(target),
            "chapterCount": len(built_chapters),
            "searchEntryCount": len(search_index),
            "explorationEntryCount": len(exploration_index),
            "missingPageCodes": len(coverage_report["missingPageCodes"]),
        },
    )


if __name__ == "__main__":
    main()
