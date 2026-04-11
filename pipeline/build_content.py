from __future__ import annotations

import hashlib
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from .build_images import match_inline_image_block, normalize_image_bytes
from .common import (
    blocks_to_html,
    blocks_to_text,
    extract_page_blocks,
    load_config,
    load_generated_json,
    make_excerpt,
    open_pdf,
    print_json_summary,
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


def trim_overview_ranges(
    chapters: list[dict[str, Any]], section_entries: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    chapters_by_slug = {chapter["slug"]: chapter for chapter in chapters}
    section_entries_by_chapter: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for entry in section_entries:
        section_entries_by_chapter[entry["chapterSlug"]].append(entry)

    for chapter_slug, chapter_entries in section_entries_by_chapter.items():
        overview_entry = next(
            (entry for entry in chapter_entries if entry["entryType"] == "overview"),
            None,
        )
        if overview_entry is None:
            continue

        chapter = chapters_by_slug.get(chapter_slug)
        if chapter is None:
            continue

        child_page_starts = sorted(
            entry["pageStart"]
            for entry in chapter_entries
            if entry["entryType"] != "overview" and entry.get("pageStart") is not None
        )
        first_child_start = child_page_starts[0] if child_page_starts else None

        overview_entry["pageStart"] = chapter.get("pageStart")
        overview_entry["pageEnd"] = (
            chapter.get("pageEnd") if first_child_start is None else first_child_start - 1
        )

    return section_entries


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


def join_page_blocks(
    page_blocks: dict[int, list[dict[str, Any]]],
    start_page: int | None,
    end_page: int | None,
    excluded_pages: set[int] | None = None,
) -> list[dict[str, Any]]:
    if start_page is None or end_page is None:
        return []
    excluded_page_set = excluded_pages or set()
    blocks: list[dict[str, Any]] = []
    for page_number in range(start_page, end_page + 1):
        if page_number in excluded_page_set:
            continue
        blocks.extend(page_blocks.get(page_number, []))
    return blocks


def count_content_images(blocks: list[dict[str, Any]]) -> int:
    return sum(1 for block in blocks if block.get("type") == 1)


def build_image_manifest_lookup(image_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {image["id"]: image for image in image_manifest.get("images", [])}


def build_page_blocks(
    reader: Any,
    inventory: dict[str, Any],
    image_manifest: dict[str, Any],
) -> dict[int, list[dict[str, Any]]]:
    image_lookup = build_image_manifest_lookup(image_manifest)
    page_blocks: dict[int, list[dict[str, Any]]] = {}

    for page_meta in inventory["pages"]:
        page_number = page_meta["pageNumber"]
        page_code = page_meta.get("pageCode")
        page = reader.load_page(page_number - 1)
        raw_blocks = extract_page_blocks(page)
        raw_image_blocks = [
            (index, block) for index, block in enumerate(raw_blocks) if block.get("type") == 1
        ]
        image_blocks = [block for _, block in raw_image_blocks]
        used_indices: set[int] = set()
        matched_assets: dict[int, dict[str, Any]] = {}

        for info in page.get_image_info(hashes=True, xrefs=True):
            matched_block = match_inline_image_block(info, image_blocks, used_indices)
            if matched_block is None:
                continue

            raw_index = next(
                index for index, candidate in raw_image_blocks if candidate is matched_block
            )
            xref = int(info.get("xref") or 0)
            if xref > 0:
                extracted = reader.extract_image(xref)
                mask_bytes = None
                smask = int(extracted.get("smask") or 0)
                if smask > 0:
                    mask_bytes = reader.extract_image(smask)["image"]
                image_bytes, _ = normalize_image_bytes(
                    extracted["image"],
                    str(extracted.get("ext") or "png"),
                    mask_bytes,
                )
            else:
                image_bytes, _ = normalize_image_bytes(
                    matched_block["image"],
                    str(matched_block.get("ext") or "png"),
                    matched_block.get("mask"),
                )

            image_id = hashlib.sha1(image_bytes).hexdigest()[:12]
            manifest_image = image_lookup.get(image_id)
            if manifest_image is None:
                continue
            matched_assets[raw_index] = manifest_image

        enriched_blocks: list[dict[str, Any]] = []
        for index, block in enumerate(raw_blocks):
            if block.get("type") == 0:
                enriched_blocks.append(
                    {
                        **block,
                        "_pageNumber": page_number,
                        "_pageCode": page_code,
                    }
                )
                continue

            if block.get("type") != 1:
                continue

            manifest_image = matched_assets.get(index)
            if manifest_image is None:
                continue

            enriched_blocks.append(
                {
                    **block,
                    "_pageNumber": page_number,
                    "_pageCode": page_code,
                    "_imageId": manifest_image["id"],
                    "_relativePath": f"public/generated/{manifest_image['relativePath']}",
                }
            )

        page_blocks[page_number] = enriched_blocks

    return page_blocks


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
    image_manifest = load_generated_json("image-manifest.json")
    reader = open_pdf(config)
    page_blocks = build_page_blocks(reader, inventory, image_manifest)
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
    section_entries = trim_overview_ranges(chapters_in_order, section_entries)
    section_entries_by_chapter: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in section_entries:
        entry_blocks = join_page_blocks(
            page_blocks,
            entry["pageStart"],
            entry["pageEnd"],
            excluded_pages=toc_pages,
        )
        entry_text = blocks_to_text(entry_blocks)
        entry["text"] = entry_text
        entry["html"] = blocks_to_html(entry_blocks)
        entry["excerpt"] = make_excerpt(entry_text)
        entry["categories"] = classify_entry(entry)
        entry["imageCount"] = count_content_images(entry_blocks)
        entry["hasImage"] = entry["imageCount"] > 0
        section_entries_by_chapter[entry["chapterSlug"]].append(entry)

    built_chapters: list[dict[str, Any]] = []
    for chapter_record in chapters_in_order:
        chapter_sections = section_entries_by_chapter[chapter_record["slug"]]
        overview_entry = next(
            (entry for entry in chapter_sections if entry["entryType"] == "overview"),
            None,
        )
        chapter_blocks = join_page_blocks(
            page_blocks,
            chapter_record["pageStart"],
            chapter_record["pageEnd"],
            excluded_pages=toc_pages,
        )
        chapter_text = blocks_to_text(chapter_blocks)
        chapter_image_count = sum(entry["imageCount"] for entry in chapter_sections)
        html_parts = [
            "<section id=\"overview\">",
            f"<h2>{chapter_record['title']}</h2>",
        ]
        if overview_entry and (overview_entry["text"] or overview_entry["hasImage"]):
            html_parts.append(overview_entry["html"])
        html_parts.append("</section>")
        for entry in chapter_sections:
            if entry["entryType"] == "overview":
                continue
            heading_tag = "h3" if entry["entryType"] != "item" or "보충기준" in entry["sectionTitle"] else "h3"
            html_parts.extend(
                [
                    f"<section id=\"{entry['sectionId']}\">",
                    f"<{heading_tag}>{entry['sectionTitle']}</{heading_tag}>",
                    entry["html"],
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
                "hasImage": chapter_image_count > 0,
                "imageCount": chapter_image_count,
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
            "hasImage": entry["hasImage"],
            "imageCount": entry["imageCount"],
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
            "hasImage": entry["hasImage"],
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
        "imageFileCount": len(image_manifest.get("images", [])),
        "excludedImageCount": max(
            sum(int(page.get("imageCount", 0)) for page in inventory["pages"])
            - sum(entry["imageCount"] for entry in section_entries),
            0,
        ),
        "totalImageBytes": sum(int(image.get("byteSize", 0)) for image in image_manifest.get("images", [])),
        "chaptersWithImages": sum(1 for chapter in built_chapters if chapter["hasImage"]),
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
