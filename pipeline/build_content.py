from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from .build_images import match_inline_image_block, normalize_image_bytes
from .common import (
    blocks_to_html,
    blocks_to_text,
    clean_title,
    extract_page_blocks,
    load_config,
    load_generated_json,
    make_excerpt,
    open_pdf,
    print_json_summary,
    strip_running_header_lines,
    text_block_to_text,
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


def build_inventory_page_map(inventory: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {page["pageNumber"]: page for page in inventory["pages"]}


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


def count_html_images(html: str) -> int:
    return len(re.findall(r"<img\b", html or ""))


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
                    "_relativePath": f"generated/{manifest_image['relativePath']}",
                }
            )

        page_blocks[page_number] = enriched_blocks

    return page_blocks


def page_text_lines(
    page_blocks: list[dict[str, Any]],
    *,
    part_title: str = "",
    chapter_title: str = "",
    page_code: str | None = None,
) -> list[str]:
    lines: list[str] = []
    for block in sort_blocks_in_reading_order(page_blocks):
        if block.get("type") != 0:
            continue
        text = text_block_to_text(block)
        if not text:
            continue
        lines.extend(line.strip() for line in text.splitlines() if line.strip())
    return strip_running_header_lines(
        lines,
        part_title=part_title,
        chapter_title=chapter_title,
        page_code=page_code,
    )


def looks_like_supplement_preamble_page(
    page_blocks: list[dict[str, Any]],
    *,
    part_title: str,
    chapter_title: str,
    page_code: str | None,
) -> bool:
    lines = page_text_lines(
        page_blocks,
        part_title=part_title,
        chapter_title=chapter_title,
        page_code=page_code,
    )
    if not lines:
        return False

    first = clean_title(lines[0])
    second = clean_title(lines[1]) if len(lines) > 1 else ""
    reference_labels = {
        "관련 법령 및 취지",
        "관련 법령",
        "관련 법령(조약)",
        "관련 판례",
        "참조조문",
        "참조판례",
    }

    if first in reference_labels:
        return True
    if re.fullmatch(r"^[【<].+[】>]$", first):
        return True
    if re.match(r"^제\s*\d+조", first):
        return True
    if re.fullmatch(r"^[【<].+[】>]$", second):
        return True
    if re.match(r"^제\s*\d+조", second):
        return True
    return False


def page_contains_supplement_heading(
    page_blocks: list[dict[str, Any]],
    supplement: dict[str, Any],
    *,
    part_title: str,
    chapter_title: str,
    page_code: str | None,
) -> bool:
    lines = page_text_lines(
        page_blocks,
        part_title=part_title,
        chapter_title=chapter_title,
        page_code=page_code,
    )
    if not lines:
        return False

    title_variants = {
        clean_title(supplement["fullTitle"]),
        clean_title(f"{supplement['label']}: {supplement['title']}"),
        clean_title(supplement["title"]),
    }
    title_variants.discard("")

    for line in lines[:3]:
        normalized_line = clean_title(line)
        if any(variant in normalized_line for variant in title_variants):
            return True
    return False


def resolve_supplement_start(
    page_code_map: dict[str, int],
    page_blocks: dict[int, list[dict[str, Any]]],
    supplement: dict[str, Any],
    *,
    part_title: str,
    chapter_title: str,
    chapter_start: int | None,
) -> tuple[int | None, bool]:
    supplement_page_code = supplement.get("pageCode")
    if supplement_page_code and supplement_page_code in page_code_map:
        return page_code_map[supplement_page_code], False

    child_page_codes = [item["pageCode"] for item in supplement["items"]]
    child_start, used_fallback = resolve_page_start(
        page_code_map,
        None,
        fallback_page_codes=child_page_codes,
        fallback_page_start=chapter_start,
    )
    if child_start is None or chapter_start is None:
        return child_start, used_fallback

    heading_page: int | None = None
    for page_number in range(child_start, chapter_start - 1, -1):
        page_entries = page_blocks.get(page_number, [])
        page_code = next((block.get("_pageCode") for block in page_entries if block.get("_pageCode")), None)
        if page_contains_supplement_heading(
            page_entries,
            supplement,
            part_title=part_title,
            chapter_title=chapter_title,
            page_code=page_code,
        ):
            heading_page = page_number
            break

    if heading_page is None:
        return child_start, used_fallback

    supplement_start = heading_page
    for page_number in range(heading_page - 1, chapter_start - 1, -1):
        page_entries = page_blocks.get(page_number, [])
        page_code = next((block.get("_pageCode") for block in page_entries if block.get("_pageCode")), None)
        if not looks_like_supplement_preamble_page(
            page_entries,
            part_title=part_title,
            chapter_title=chapter_title,
            page_code=page_code,
        ):
            break
        supplement_start = page_number

    return supplement_start, True


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


def block_sort_key(block: dict[str, Any]) -> tuple[int, float, float]:
    bbox = block.get("bbox")
    top = float(bbox[1]) if isinstance(bbox, (tuple, list)) and len(bbox) == 4 else 10**9
    left = float(bbox[0]) if isinstance(bbox, (tuple, list)) and len(bbox) == 4 else 10**9
    return (int(block.get("_pageNumber") or 0), top, left)


def sort_blocks_in_reading_order(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(blocks, key=block_sort_key)


def extract_section_number_prefix(title: str) -> str | None:
    match = re.match(r"^(\d+)\.", clean_title(title))
    if match is None:
        return None
    return f"{match.group(1)}."


def find_title_block_index(
    blocks: list[dict[str, Any]],
    title: str,
    *,
    start_index: int = 0,
) -> int | None:
    normalized_title = clean_title(title)
    if not normalized_title:
        return None

    for index in range(start_index, len(blocks)):
        block = blocks[index]
        if block.get("type") != 0:
            continue
        block_text = clean_title(blocks_to_text([block]))
        if block_text == normalized_title:
            return index
    return None


def find_numbered_subheading_index(
    blocks: list[dict[str, Any]],
    title: str,
    *,
    start_index: int = 0,
) -> int | None:
    section_prefix = extract_section_number_prefix(title)
    if section_prefix is None:
        return None

    for index in range(start_index, len(blocks)):
        block = blocks[index]
        if block.get("type") != 0:
            continue
        block_text = clean_title(blocks_to_text([block]))
        if re.match(rf"^{re.escape(section_prefix)}\d+", block_text):
            return index
    return None


def slice_entry_blocks(
    blocks: list[dict[str, Any]],
    entry: dict[str, Any],
    following_entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not blocks:
        return []

    blocks = sort_blocks_in_reading_order(blocks)

    start_index = 0
    if entry["entryType"] != "overview":
        title_index = find_title_block_index(blocks, entry["sectionTitle"])
        if title_index is not None:
            start_index = title_index + 1
        else:
            subheading_index = find_numbered_subheading_index(blocks, entry["sectionTitle"])
            if subheading_index is not None:
                start_index = subheading_index

    end_index = len(blocks)
    for following_entry in following_entries:
        next_title_index = find_title_block_index(
            blocks,
            following_entry["sectionTitle"],
            start_index=start_index,
        )
        if next_title_index is not None:
            end_index = next_title_index
            break

    return blocks[start_index:end_index]


def build_next_chapter_start_map(chapters: list[dict[str, Any]]) -> dict[str, int | None]:
    resolved = [chapter for chapter in chapters if chapter.get("pageStart") is not None]
    next_start_by_slug: dict[str, int | None] = {chapter["slug"]: None for chapter in chapters}

    for index, chapter in enumerate(resolved):
        next_start = resolved[index + 1]["pageStart"] if index + 1 < len(resolved) else None
        next_start_by_slug[chapter["slug"]] = next_start

    return next_start_by_slug


def extract_part_number(label: str) -> str | None:
    match = re.match(r"^제\s*(\d+)\s*부$", label)
    if match is None:
        return None
    return match.group(1)


def build_next_part_map(parts: list[dict[str, Any]]) -> dict[str, dict[str, Any] | None]:
    next_part_by_title: dict[str, dict[str, Any] | None] = {part["fullTitle"]: None for part in parts}
    for index, part in enumerate(parts):
        next_part_by_title[part["fullTitle"]] = parts[index + 1] if index + 1 < len(parts) else None
    return next_part_by_title


def is_appendix_boundary_page(page_meta: dict[str, Any]) -> bool:
    if page_meta.get("pageCode") is not None:
        return False
    top_lines = page_meta.get("topLines") or []
    for line in top_lines:
        stripped = line.strip()
        if not stripped:
            continue
        return clean_title(stripped) in {"부칙", "별첨"}
    return False


def find_appendix_boundary_page(
    inventory_page_map: dict[int, dict[str, Any]],
    start_page: int | None,
    end_page: int | None,
) -> int | None:
    if start_page is None or end_page is None:
        return None
    for page_number in range(start_page + 1, end_page + 1):
        page_meta = inventory_page_map.get(page_number)
        if page_meta is None:
            continue
        if is_appendix_boundary_page(page_meta):
            return page_number
    return None


def is_part_boundary_marker_page(page_blocks: list[dict[str, Any]], next_part: dict[str, Any]) -> bool:
    text_blocks = [text_block_to_text(block) for block in sort_blocks_in_reading_order(page_blocks) if block.get("type") == 0]
    text_blocks = [clean_title(text) for text in text_blocks if text]
    text_blocks = [text for text in text_blocks if text]
    if not text_blocks:
        return False

    next_part_number = extract_part_number(next_part["label"])
    next_part_title = clean_title(next_part["title"])
    next_part_full_title = clean_title(next_part["fullTitle"])

    if text_blocks[0] == next_part_full_title:
        return True
    if next_part_number and len(text_blocks) >= 2 and text_blocks[0] == next_part_number and text_blocks[1] == next_part_title:
        return True
    return False


def find_next_part_boundary_page(
    page_blocks: dict[int, list[dict[str, Any]]],
    start_page: int | None,
    end_page: int | None,
    next_part: dict[str, Any] | None,
    *,
    excluded_pages: set[int] | None = None,
) -> int | None:
    if start_page is None or end_page is None or next_part is None:
        return None

    excluded_page_set = excluded_pages or set()
    for page_number in range(start_page + 1, end_page + 1):
        if page_number in excluded_page_set:
            continue
        page_entries = page_blocks.get(page_number, [])
        if is_part_boundary_marker_page(page_entries, next_part):
            return page_number
    return None


def cap_entry_end_page(
    entry: dict[str, Any],
    next_chapter_start: int | None,
    next_part_boundary_page: int | None = None,
) -> int | None:
    page_start = entry.get("pageStart")
    page_end = entry.get("pageEnd")
    if page_start is None or page_end is None:
        return page_end

    candidates = [page_end]
    if next_chapter_start is not None and next_chapter_start > page_start:
        candidates.append(max(page_start, next_chapter_start - 1))
    if next_part_boundary_page is not None and next_part_boundary_page > page_start:
        candidates.append(max(page_start, next_part_boundary_page - 1))
    return min(candidates)


def extend_end_page_for_next_sibling(
    entry: dict[str, Any],
    following_entry: dict[str, Any] | None,
    structural_end_page: int | None,
) -> int | None:
    if structural_end_page is None:
        return None
    if entry["entryType"] == "overview" or following_entry is None:
        return structural_end_page

    nominal_end_page = entry.get("pageEnd")
    following_start_page = following_entry.get("pageStart")
    if nominal_end_page is None or following_start_page is None:
        return structural_end_page
    if structural_end_page != nominal_end_page:
        return structural_end_page
    if following_start_page <= structural_end_page:
        return structural_end_page
    return following_start_page


def page_has_meaningful_leading_content_before_title(
    blocks: list[dict[str, Any]],
    title: str,
    *,
    part_title: str = "",
    chapter_title: str = "",
) -> bool:
    if not blocks:
        return False

    ordered_blocks = sort_blocks_in_reading_order(blocks)
    title_index = find_title_block_index(ordered_blocks, title)
    if title_index is None:
        title_index = find_numbered_subheading_index(ordered_blocks, title)
    if title_index is None or title_index <= 0:
        return False

    normalized_part_title = clean_title(part_title)
    normalized_chapter_title = clean_title(chapter_title)
    for block in ordered_blocks[:title_index]:
        if block.get("type") != 0:
            return True
        text = text_block_to_text(block)
        normalized = clean_title(text)
        if not normalized:
            continue
        if re.fullmatch(r"\d{5,6}", normalized):
            continue
        if normalized in {normalized_part_title, normalized_chapter_title}:
            continue
        if not strip_running_header_lines([text], page_code=block.get("_pageCode")):
            continue
        return True
    return False


def extend_overview_end_page_for_leading_content(
    entry: dict[str, Any],
    following_entry: dict[str, Any] | None,
    structural_end_page: int | None,
    page_blocks: dict[int, list[dict[str, Any]]],
) -> int | None:
    if structural_end_page is None:
        return None
    if entry["entryType"] != "overview" or following_entry is None:
        return structural_end_page

    nominal_end_page = entry.get("pageEnd")
    following_start_page = following_entry.get("pageStart")
    if nominal_end_page is None or following_start_page is None:
        return structural_end_page
    if structural_end_page != nominal_end_page:
        return structural_end_page
    if following_start_page <= structural_end_page:
        return structural_end_page
    if not page_has_meaningful_leading_content_before_title(
        page_blocks.get(following_start_page, []),
        following_entry["sectionTitle"],
        part_title=entry.get("partTitle", ""),
        chapter_title=entry.get("chapterTitle", ""),
    ):
        return structural_end_page
    return following_start_page


def main() -> None:
    config = load_config()
    inventory = load_generated_json("pdf-inventory.json")
    inventory_page_map = build_inventory_page_map(inventory)
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
                supplement_start, supplement_used_fallback = resolve_supplement_start(
                    page_code_map,
                    page_blocks,
                    supplement,
                    part_title=part["fullTitle"],
                    chapter_title=chapter["fullTitle"],
                    chapter_start=chapter_start,
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
    next_chapter_start_by_slug = build_next_chapter_start_map(chapters_in_order)
    next_part_by_title = build_next_part_map(toc["parts"])
    section_entries_by_chapter: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in section_entries:
        section_entries_by_chapter[entry["chapterSlug"]].append(entry)

    for chapter_slug, chapter_entries in section_entries_by_chapter.items():
        for index, entry in enumerate(chapter_entries):
            following_entry = chapter_entries[index + 1] if index + 1 < len(chapter_entries) else None
            next_part_boundary_page = find_next_part_boundary_page(
                page_blocks,
                entry["pageStart"],
                entry["pageEnd"],
                next_part_by_title.get(entry["partTitle"]),
                excluded_pages=toc_pages,
            )
            effective_end_page = cap_entry_end_page(
                entry,
                next_chapter_start_by_slug.get(chapter_slug),
                next_part_boundary_page,
            )
            effective_end_page = extend_end_page_for_next_sibling(
                entry,
                following_entry,
                effective_end_page,
            )
            effective_end_page = extend_overview_end_page_for_leading_content(
                entry,
                following_entry,
                effective_end_page,
                page_blocks,
            )
            if entry["entryType"] == "overview" and len(chapter_entries) == 1:
                appendix_boundary_page = find_appendix_boundary_page(
                    inventory_page_map,
                    entry["pageStart"],
                    effective_end_page,
                )
                if appendix_boundary_page is not None:
                    effective_end_page = max(entry["pageStart"], appendix_boundary_page - 1)
            entry["pageEnd"] = effective_end_page
            entry_blocks = join_page_blocks(
                page_blocks,
                entry["pageStart"],
                effective_end_page,
                excluded_pages=toc_pages,
            )
            entry_blocks = slice_entry_blocks(entry_blocks, entry, chapter_entries[index + 1 :])
            entry_text = blocks_to_text(
                entry_blocks,
                part_title=entry["partTitle"],
                chapter_title=entry["chapterTitle"],
                section_title="" if entry["entryType"] == "overview" else entry["sectionTitle"],
            )
            entry["text"] = entry_text
            entry["html"] = blocks_to_html(
                entry_blocks,
                part_title=entry["partTitle"],
                chapter_title=entry["chapterTitle"],
                section_title="" if entry["entryType"] == "overview" else entry["sectionTitle"],
            )
            entry["excerpt"] = make_excerpt(entry_text)
            entry["categories"] = classify_entry(entry)
            entry["imageCount"] = count_html_images(entry["html"])
            entry["hasImage"] = entry["imageCount"] > 0

    built_chapters: list[dict[str, Any]] = []
    for chapter_record in chapters_in_order:
        chapter_sections = section_entries_by_chapter[chapter_record["slug"]]
        overview_entry = next(
            (entry for entry in chapter_sections if entry["entryType"] == "overview"),
            None,
        )
        chapter_text = "\n\n".join(
            entry["text"] for entry in chapter_sections if entry.get("text")
        ).strip()
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
                "pageEnd": overview_entry["pageEnd"] if overview_entry and len(chapter_sections) == 1 else chapter_record["pageEnd"],
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
