from __future__ import annotations

import re
from typing import Any

from .common import (
    extract_page_text,
    load_config,
    open_pdf,
    print_json_summary,
    slugify,
    write_json,
)


ROMAN_NUMERAL_RE = re.compile(r"^[ivxlcdm]+$", re.IGNORECASE)
TOC_MARKER_RE = re.compile(r"목\s*차")
REVISION_MARKER_ONLY_RE = re.compile(r"^\([^)]*추록\)$")
LEADING_REVISION_RE = re.compile(r"^\([^)]*추록\)\s*")
DOCUMENT_TITLE_RE = re.compile(r"^상표심사기준$")
PART_RE = re.compile(r"^(제\s*\d+\s*부)\s*(.+)$")
CHAPTER_RE = re.compile(r"^(제\s*\d+\s*장)\s*(.+?)\s*(\d{5,6})$")
SUPPLEMENT_RE = re.compile(r"^(보충기준\s*\d+)\s*:\s*(.+?)\s*(\d{5,6})$")
ITEM_RE = re.compile(r"^(\d+)\s*\.?\s+(.+?)\s*(\d{5,6})$")

SYNTHETIC_PART_SPECS: list[dict[str, Any]] = [
    {
        "id": "전문",
        "label": "전문",
        "title": "전문",
        "fullTitle": "전문",
        "chapters": [
            {
                "id": "전문-표지",
                "label": "표지",
                "title": "표지",
                "fullTitle": "표지",
                "pageCode": None,
                "fallbackPageStart": 1,
                "fixedPageEnd": 1,
                "synthetic": True,
                "items": [],
                "supplements": [],
            },
            {
                "id": "전문-제개정연혁",
                "label": "제·개정 연혁",
                "title": "제·개정 연혁",
                "fullTitle": "제·개정 연혁",
                "pageCode": None,
                "fallbackPageStart": 3,
                "fixedPageEnd": 3,
                "synthetic": True,
                "items": [],
                "supplements": [],
            },
            {
                "id": "전문-범례",
                "label": "범례",
                "title": "범례",
                "fullTitle": "범례",
                "pageCode": None,
                "fallbackPageStart": 5,
                "fixedPageEnd": 5,
                "synthetic": True,
                "items": [],
                "supplements": [],
            },
        ],
    },
    {
        "id": "부록",
        "label": "부록",
        "title": "부록",
        "fullTitle": "부록",
        "chapters": [
            {
                "id": "부록-부칙",
                "label": "부칙",
                "title": "부칙",
                "fullTitle": "부칙",
                "pageCode": None,
                "fallbackPageStart": 541,
                "fixedPageEnd": 542,
                "synthetic": True,
                "items": [],
                "supplements": [],
            },
            {
                "id": "부록-별첨",
                "label": "별첨",
                "title": "별첨",
                "fullTitle": "별첨",
                "pageCode": None,
                "fallbackPageStart": 545,
                "fixedPageEnd": 574,
                "synthetic": True,
                "items": [],
                "supplements": [],
            },
            {
                "id": "부록-판권",
                "label": "판권",
                "title": "판권",
                "fullTitle": "판권",
                "pageCode": None,
                "fallbackPageStart": 575,
                "fixedPageEnd": 575,
                "synthetic": True,
                "items": [],
                "supplements": [],
            },
        ],
    },
]


def normalize_toc_line(value: str) -> str:
    normalized = " ".join(value.split()).strip()
    return LEADING_REVISION_RE.sub("", normalized).strip()


def should_skip_line(line: str) -> bool:
    return (
        not line
        or TOC_MARKER_RE.fullmatch(line) is not None
        or ROMAN_NUMERAL_RE.fullmatch(line) is not None
        or REVISION_MARKER_ONLY_RE.fullmatch(line) is not None
        or DOCUMENT_TITLE_RE.fullmatch(line) is not None
    )


def looks_like_toc_page(lines: list[str]) -> bool:
    if not lines:
        return False
    entry_like_count = 0
    for line in lines[:40]:
        has_page_code = re.search(r"\d{5,6}$", line) is not None
        has_toc_shape = "···" in line or PART_RE.match(line) or CHAPTER_RE.match(line) or ITEM_RE.match(line)
        if has_page_code and has_toc_shape:
            entry_like_count += 1
    return entry_like_count >= 3


def collect_toc_lines(max_scan_page_limit: int) -> tuple[list[int], list[str]]:
    config = load_config()
    reader = open_pdf(config)
    toc_pages: list[int] = []
    collected_lines: list[str] = []

    for page_number in range(1, min(reader.page_count, max_scan_page_limit) + 1):
        text = extract_page_text(reader.load_page(page_number - 1))
        raw_lines = [normalize_toc_line(raw_line) for raw_line in text.splitlines()]
        if TOC_MARKER_RE.search(text) is None and not (toc_pages and looks_like_toc_page(raw_lines)):
            continue
        toc_pages.append(page_number)
        for line in raw_lines:
            if should_skip_line(line):
                continue
            if TOC_MARKER_RE.match(line):
                continue
            collected_lines.append(line)

    return toc_pages, collected_lines


def coalesce_toc_entries(lines: list[str]) -> list[str]:
    entries: list[str] = []
    buffer: list[str] = []

    for line in lines:
        buffer.append(line)
        combined = " ".join(buffer).strip()
        has_trailing_page_code = re.search(r"\d{5,6}$", combined) is not None
        if PART_RE.match(combined) and not has_trailing_page_code:
            entries.append(combined)
            buffer = []
            continue
        if has_trailing_page_code:
            entries.append(combined)
            buffer = []

    if buffer:
        entries.append(" ".join(buffer).strip())

    return entries


def parse_entries(entry_lines: list[str]) -> dict[str, Any]:
    parts: list[dict[str, Any]] = []
    current_part: dict[str, Any] | None = None
    current_chapter: dict[str, Any] | None = None
    current_supplement: dict[str, Any] | None = None

    flat_entries: list[dict[str, Any]] = []
    chapter_count = 0
    item_count = 0
    supplement_count = 0

    for raw_entry in entry_lines:
        part_match = PART_RE.match(raw_entry)
        if part_match:
            label, title = part_match.groups()
            current_part = {
                "id": slugify(f"{label} {title}"),
                "label": label,
                "title": title,
                "fullTitle": f"{label} {title}",
                "chapters": [],
            }
            parts.append(current_part)
            current_chapter = None
            current_supplement = None
            flat_entries.append(
                {
                    "kind": "part",
                    "label": label,
                    "title": title,
                    "fullTitle": f"{label} {title}",
                    "pageCode": None,
                }
            )
            continue

        chapter_match = CHAPTER_RE.match(raw_entry)
        if chapter_match:
            if current_part is None:
                continue
            label, title, page_code = chapter_match.groups()
            current_chapter = {
                "id": slugify(f"{label} {title}"),
                "label": label,
                "title": title,
                "fullTitle": f"{label} {title}",
                "pageCode": page_code,
                "items": [],
                "supplements": [],
            }
            current_part["chapters"].append(current_chapter)
            current_supplement = None
            chapter_count += 1
            flat_entries.append(
                {
                    "kind": "chapter",
                    "label": label,
                    "title": title,
                    "fullTitle": f"{label} {title}",
                    "pageCode": page_code,
                    "partTitle": current_part["fullTitle"],
                }
            )
            continue

        supplement_match = SUPPLEMENT_RE.match(raw_entry)
        if supplement_match:
            if current_chapter is None:
                continue
            label, title, page_code = supplement_match.groups()
            current_supplement = {
                "id": slugify(f"{label} {title}"),
                "label": label,
                "title": title,
                "fullTitle": f"{label}: {title}",
                "pageCode": page_code,
                "items": [],
            }
            current_chapter["supplements"].append(current_supplement)
            supplement_count += 1
            flat_entries.append(
                {
                    "kind": "supplement",
                    "label": label,
                    "title": title,
                    "fullTitle": f"{label}: {title}",
                    "pageCode": page_code,
                    "partTitle": current_part["fullTitle"] if current_part else None,
                    "chapterTitle": current_chapter["fullTitle"],
                }
            )
            continue

        item_match = ITEM_RE.match(raw_entry)
        if item_match and current_chapter is not None:
            label_number, title, page_code = item_match.groups()
            item = {
                "id": slugify(f"{label_number}. {title}"),
                "label": f"{label_number}.",
                "title": title,
                "fullTitle": f"{label_number}. {title}",
                "pageCode": page_code,
            }
            if current_supplement is not None:
                current_supplement["items"].append(item)
            else:
                current_chapter["items"].append(item)
            item_count += 1
            flat_entries.append(
                {
                    "kind": "item",
                    "label": f"{label_number}.",
                    "title": title,
                    "fullTitle": f"{label_number}. {title}",
                    "pageCode": page_code,
                    "partTitle": current_part["fullTitle"] if current_part else None,
                    "chapterTitle": current_chapter["fullTitle"],
                    "supplementTitle": current_supplement["fullTitle"] if current_supplement else None,
                }
            )

    return {
        "parts": parts,
        "flatEntries": flat_entries,
        "counts": {
            "partCount": len(parts),
            "chapterCount": chapter_count,
            "itemCount": item_count,
            "supplementCount": supplement_count,
        },
    }


def clone_synthetic_part(part_spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": part_spec["id"],
        "label": part_spec["label"],
        "title": part_spec["title"],
        "fullTitle": part_spec["fullTitle"],
        "chapters": [
            {
                **chapter_spec,
                "items": list(chapter_spec.get("items", [])),
                "supplements": list(chapter_spec.get("supplements", [])),
            }
            for chapter_spec in part_spec["chapters"]
        ],
    }


def build_synthetic_flat_entries(part_spec: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = [
        {
            "kind": "part",
            "label": part_spec["label"],
            "title": part_spec["title"],
            "fullTitle": part_spec["fullTitle"],
            "pageCode": None,
        }
    ]
    for chapter_spec in part_spec["chapters"]:
        entries.append(
            {
                "kind": "chapter",
                "label": chapter_spec["label"],
                "title": chapter_spec["title"],
                "fullTitle": chapter_spec["fullTitle"],
                "pageCode": None,
                "partTitle": part_spec["fullTitle"],
                "fallbackPageStart": chapter_spec["fallbackPageStart"],
                "fixedPageEnd": chapter_spec["fixedPageEnd"],
                "synthetic": True,
            }
        )
    return entries


def recalculate_counts(parts: list[dict[str, Any]]) -> dict[str, int]:
    chapter_count = 0
    item_count = 0
    supplement_count = 0
    for part in parts:
        chapters = part.get("chapters", [])
        chapter_count += len(chapters)
        for chapter in chapters:
            item_count += len(chapter.get("items", []))
            supplements = chapter.get("supplements", [])
            supplement_count += len(supplements)
            for supplement in supplements:
                item_count += len(supplement.get("items", []))
    return {
        "partCount": len(parts),
        "chapterCount": chapter_count,
        "itemCount": item_count,
        "supplementCount": supplement_count,
    }


def inject_synthetic_parts(parsed: dict[str, Any]) -> dict[str, Any]:
    front_matter = clone_synthetic_part(SYNTHETIC_PART_SPECS[0])
    appendix = clone_synthetic_part(SYNTHETIC_PART_SPECS[1])

    parts = [front_matter, *parsed["parts"], appendix]
    flat_entries = [
        *build_synthetic_flat_entries(SYNTHETIC_PART_SPECS[0]),
        *parsed["flatEntries"],
        *build_synthetic_flat_entries(SYNTHETIC_PART_SPECS[1]),
    ]

    return {
        "parts": parts,
        "flatEntries": flat_entries,
        "counts": recalculate_counts(parts),
    }


def main() -> None:
    config = load_config()
    toc_pages, toc_lines = collect_toc_lines(config["tocScanPageLimit"])
    entries = coalesce_toc_entries(toc_lines)
    parsed = parse_entries(entries)
    parsed = inject_synthetic_parts(parsed)
    payload = {
        "meta": {
            "title": config["documentTitle"],
            "tocPages": toc_pages,
            **parsed["counts"],
        },
        "parts": parsed["parts"],
        "flatEntries": parsed["flatEntries"],
    }
    target = write_json("toc.json", payload)
    print_json_summary(
        "toc",
        {
            "target": str(target),
            "tocPages": toc_pages,
            **parsed["counts"],
        },
    )


if __name__ == "__main__":
    main()
