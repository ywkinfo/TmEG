from __future__ import annotations

import json
import re
import sys
from html import escape
from pathlib import Path
from typing import Any

try:
    import pymupdf
except ModuleNotFoundError as exc:
    raise SystemExit(
        "pymupdf 모듈이 필요합니다. 현재 환경에서 `python -c 'import pymupdf'`가 동작해야 합니다."
    ) from exc


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
SOURCE_DIR = DATA_DIR / "source"
GENERATED_DIR = DATA_DIR / "generated"
CONFIG_PATH = SOURCE_DIR / "source-config.json"
PAGE_CODE_RE = re.compile(r"\b\d{5,6}\b")
WHITESPACE_RE = re.compile(r"\s+")
DOT_LEADER_RE = re.compile(r"[·ㆍ.]{2,}.*$")
PAGE_ONLY_RE = re.compile(r"^\d{5,6}$")
UPDATE_MARKER_RE = re.compile(r"^\(20\d{2}년\s*\d+월\s*추록\)$")
EFFECTIVE_DATE_NOTE_RE = re.compile(r"^\[시행일:\s*20\d{2}\.\s*\d{1,2}\.\s*\d{1,2}\.\]$")
PAGE_EDGE_SLASH_HEADING_RE = re.compile(r"^\d+\s*/\s*[^/]+(?:\s*/\s*[^/]+){0,3}$")
CHAPTER_LABEL_RE = re.compile(r"^제\s*\d+\s*(?:부|장|절)\b")
NUMBERED_HEADING_RE = re.compile(r"^(?:\d+(?:\.\d+)*\.?\s+|[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]\s+)")
BRACKET_LABEL_RE = re.compile(r"^[【《].+[】》]$")
GENERIC_LABELS = {
    "관련 법령",
    "관련 법령 및 취지",
    "제도의 취지",
    "판단시 유의사항",
    "판단시점",
    "적용요건",
    "요건",
}
REFERENCE_METADATA_LABELS = {
    "관련 법령",
    "관련판례",
    "참조조문",
    "참조판례",
    "【관련 법령】",
    "【관련판례】",
    "【참조조문】",
    "【참조판례】",
}
EDITORIAL_LABELS = {
    "관련 법령 및 취지",
}


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def resolve_pdf_path(config: dict[str, Any]) -> Path:
    pdf_path = ROOT_DIR / config["sourcePdf"]
    if not pdf_path.exists():
        raise SystemExit(f"원본 PDF를 찾을 수 없습니다: {pdf_path}")
    return pdf_path


def open_pdf(config: dict[str, Any]) -> pymupdf.Document:
    return pymupdf.open(str(resolve_pdf_path(config)))


def ensure_generated_dir() -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def write_json(filename: str, data: Any) -> Path:
    ensure_generated_dir()
    target = GENERATED_DIR / filename
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def load_generated_json(filename: str) -> Any:
    target = GENERATED_DIR / filename
    if not target.exists():
        raise SystemExit(f"generated 파일이 없습니다: {target}")
    return json.loads(target.read_text(encoding="utf-8"))


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
    return collapse_spaced_syllables(normalize_line(stripped))


def normalize_space(value: str) -> str:
    return normalize_line(value)


def extract_page_text(page: Any) -> str:
    return (page.get_text("text") or "").replace("\x00", "").strip()


def extract_page_blocks(page: Any, sort: bool = False) -> list[dict[str, Any]]:
    return page.get_text("dict", sort=sort).get("blocks", [])


def count_image_blocks(page: Any) -> int:
    return sum(1 for block in extract_page_blocks(page) if block.get("type") == 1)


def extract_top_lines(text: str, limit: int = 8) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = normalize_space(raw_line)
        if not line:
            continue
        lines.append(line)
        if len(lines) >= limit:
            break
    return lines


def detect_page_code(top_lines: list[str]) -> str | None:
    for line in top_lines[:8]:
        match = PAGE_CODE_RE.search(line)
        if match:
            return match.group(0)
    return None


def slugify(value: str) -> str:
    lowered = value.lower().strip()
    cleaned = re.sub(r"[^\w\s-]", "", lowered, flags=re.UNICODE)
    collapsed = re.sub(r"[-\s]+", "-", cleaned, flags=re.UNICODE).strip("-")
    return collapsed or "section"


def make_excerpt(text: str, limit: int = 220) -> str:
    normalized = normalize_space(text)
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


def text_to_html(text: str) -> str:
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text.strip()) if block.strip()]
    if not blocks:
        return "<p></p>"
    paragraphs = [f"<p>{escape(block).replace(chr(10), '<br />')}</p>" for block in blocks]
    return "\n".join(paragraphs)


def strip_running_header_lines(
    lines: list[str],
    *,
    part_title: str = "",
    chapter_title: str = "",
    page_code: str | None = None,
    section_title: str = "",
    strip_section_title: bool = False,
) -> list[str]:
    normalized_lines = [normalize_line(line) for line in lines]
    normalized_lines = [line for line in normalized_lines if line]
    header_titles = {clean_title(part_title), clean_title(chapter_title)}
    header_titles.discard("")
    compact_page_code = (page_code or "").replace(" ", "")

    while normalized_lines:
        current = normalized_lines[0]
        if clean_title(current) in header_titles:
            normalized_lines.pop(0)
            continue
        if compact_page_code and current.replace(" ", "") == compact_page_code:
            normalized_lines.pop(0)
            continue
        break

    while normalized_lines:
        current = normalized_lines[-1]
        if compact_page_code and current.replace(" ", "") == compact_page_code:
            normalized_lines.pop()
            continue
        break

    if strip_section_title and normalized_lines and clean_title(normalized_lines[0]) == clean_title(section_title):
        normalized_lines.pop(0)

    return normalized_lines


def strip_running_header(
    text: str,
    part_title: str,
    chapter_title: str,
    page_code: str | None,
    section_title: str,
) -> str:
    return "\n".join(
        strip_running_header_lines(
            text.splitlines(),
            part_title=part_title,
            chapter_title=chapter_title,
            page_code=page_code,
            section_title=section_title,
            strip_section_title=True,
        )
    ).strip()


def _bbox_value(bbox: Any, index: int) -> float | None:
    if not isinstance(bbox, (tuple, list)) or len(bbox) != 4:
        return None
    value = bbox[index]
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _block_sort_key(indexed_block: tuple[int, dict[str, Any]]) -> tuple[float, float, int]:
    index, block = indexed_block
    bbox = block.get("bbox")
    top = _bbox_value(bbox, 1)
    left = _bbox_value(bbox, 0)
    return (
        top if top is not None else 10**9,
        left if left is not None else 10**9,
        index,
    )


def _extract_text_line_entries(block: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for line in block.get("lines", []):
        raw_text = "".join(span.get("text", "") for span in line.get("spans", []))
        raw_text = raw_text.replace("\x00", "")
        raw_text = _collapse_doubled_editorial_label(raw_text)
        text = raw_text.strip()
        if not text:
            continue
        entries.append(
            {
                "kind": "text",
                "raw_text": raw_text,
                "text": text,
                "bbox": line.get("bbox") or block.get("bbox"),
                "page_number": block.get("_pageNumber"),
                "page_code": block.get("_pageCode"),
            }
        )
    return entries


def _has_line_geometry(block: dict[str, Any]) -> bool:
    return any((line.get("bbox") or block.get("bbox")) for line in block.get("lines", []))


def _looks_like_short_heading(text: str, bbox: Any = None) -> bool:
    normalized = clean_title(text)
    if not normalized:
        return False
    if normalized in GENERIC_LABELS:
        return True
    if BRACKET_LABEL_RE.fullmatch(normalized):
        return True
    if CHAPTER_LABEL_RE.match(normalized) and len(normalized) <= 40:
        return True
    width = None
    left = _bbox_value(bbox, 0)
    right = _bbox_value(bbox, 2)
    if left is not None and right is not None:
        width = right - left
    return bool(
        len(normalized) <= 80
        and NUMBERED_HEADING_RE.match(normalized)
        and (width is None or width <= 260.0)
        and not normalized.endswith((".", "!", "?", "…"))
    )


def _ends_sentence(text: str) -> bool:
    return normalize_line(text).endswith((".", "!", "?", "…", ":", "】", "》"))


def _can_merge_lines(previous: dict[str, Any], current: dict[str, Any]) -> bool:
    previous_bbox = previous.get("bbox")
    current_bbox = current.get("bbox")
    previous_bottom = _bbox_value(previous_bbox, 3)
    current_top = _bbox_value(current_bbox, 1)
    previous_left = _bbox_value(previous_bbox, 0)
    current_left = _bbox_value(current_bbox, 0)

    if previous_bottom is None or current_top is None or previous_left is None or current_left is None:
        return False

    if current_top - previous_bottom > 10.0:
        return False
    if abs(current_left - previous_left) > 24.0:
        return False
    if _looks_like_short_heading(previous["text"], previous_bbox):
        return False
    if _looks_like_short_heading(current["text"], current_bbox):
        return False
    if _ends_sentence(previous["text"]):
        return False
    return True


def _join_line_text(previous: dict[str, Any], current: dict[str, Any]) -> str:
    separator = " " if previous["raw_text"].endswith((" ", "\u00a0")) or current["raw_text"].startswith((" ", "\u00a0")) else ""
    return f"{previous['text']}{separator}{current['text']}"


def _flush_paragraph(paragraph_lines: list[dict[str, Any]], normalized_blocks: list[dict[str, Any]]) -> None:
    if not paragraph_lines:
        return

    merged_text = paragraph_lines[0]["text"]
    previous_line = paragraph_lines[0]
    for line in paragraph_lines[1:]:
        merged_text = _join_line_text({**previous_line, "text": merged_text}, line)
        previous_line = line

    normalized_blocks.append(
        {
            "type": 0,
            "_normalizedText": merged_text.strip(),
            "_pageNumber": paragraph_lines[0].get("page_number"),
            "_pageCode": paragraph_lines[0].get("page_code"),
        }
    )


def _collapse_duplicate_labels(page_elements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    collapsed: list[dict[str, Any]] = []
    for element in page_elements:
        if (
            collapsed
            and element.get("kind") == "text"
            and collapsed[-1].get("kind") == "text"
            and clean_title(element["text"]) == clean_title(collapsed[-1]["text"])
            and _looks_like_short_heading(element["text"], element.get("bbox"))
        ):
            continue
        collapsed.append(element)
    return collapsed


def _is_update_marker(text: str) -> bool:
    return bool(UPDATE_MARKER_RE.fullmatch(normalize_line(text)))


def _is_effective_date_note(text: str) -> bool:
    return bool(EFFECTIVE_DATE_NOTE_RE.fullmatch(normalize_line(text)))


def _is_page_edge_slash_heading(text: str) -> bool:
    normalized = normalize_line(text)
    if not PAGE_EDGE_SLASH_HEADING_RE.fullmatch(normalized):
        return False
    if any(punctuation in normalized for punctuation in (".", "?", "!", ":", ";", "(", ")", "[", "]", "§")):
        return False
    return True


def _is_reference_metadata_label(text: str) -> bool:
    return normalize_line(text) in REFERENCE_METADATA_LABELS


def _collapse_doubled_editorial_label(text: str) -> str:
    normalized = normalize_line(text)
    for label in EDITORIAL_LABELS:
        if normalized == f"{label}{label}":
            return label
    return text


def _strip_page_edges(
    page_elements: list[dict[str, Any]],
    *,
    part_title: str,
    chapter_title: str,
    section_title: str,
    strip_section_title: bool,
) -> list[dict[str, Any]]:
    stripped = list(page_elements)
    page_code = next(
        (element.get("page_code") for element in stripped if element.get("kind") == "text" and element.get("page_code")),
        None,
    )

    while stripped and stripped[0].get("kind") == "text":
        text = stripped[0]["text"]
        if _is_page_edge_slash_heading(text):
            stripped.pop(0)
            continue
        remaining = strip_running_header_lines(
            [text],
            part_title=part_title,
            chapter_title=chapter_title,
            page_code=page_code,
        )
        if remaining == [normalize_line(text)]:
            break
        stripped.pop(0)

    while stripped and stripped[-1].get("kind") == "text":
        text = stripped[-1]["text"]
        if _is_update_marker(text):
            stripped.pop()
            continue
        if _is_page_edge_slash_heading(text):
            stripped.pop()
            continue
        remaining = strip_running_header_lines([text], page_code=page_code)
        if remaining == [normalize_line(text)]:
            break
        stripped.pop()

    if strip_section_title:
        normalized_section_title = clean_title(section_title)
        for index, element in enumerate(stripped):
            if element.get("kind") != "text":
                continue
            if clean_title(element["text"]) == normalized_section_title:
                stripped.pop(index)
                break

    return stripped


def _strip_reference_metadata_labels(page_elements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stripped: list[dict[str, Any]] = []
    for element in page_elements:
        if element.get("kind") == "text" and (
            _is_reference_metadata_label(element["text"]) or _is_effective_date_note(element["text"])
        ):
            continue
        stripped.append(element)
    return stripped


def normalize_content_blocks(
    blocks: list[dict[str, Any]],
    *,
    part_title: str = "",
    chapter_title: str = "",
    section_title: str = "",
) -> list[dict[str, Any]]:
    pages: dict[int, list[tuple[int, dict[str, Any]]]] = {}
    for index, block in enumerate(blocks):
        page_number = block.get("_pageNumber") or 0
        pages.setdefault(int(page_number), []).append((index, block))

    normalized_blocks: list[dict[str, Any]] = []
    should_strip_section_title = bool(section_title)

    for page_number in sorted(pages):
        page_elements: list[dict[str, Any]] = []
        for _, block in sorted(pages[page_number], key=_block_sort_key):
            if block.get("type") == 0:
                if not _has_line_geometry(block):
                    block_text = text_block_to_text(block)
                    if block_text:
                        page_elements.append(
                            {
                                "kind": "text",
                                "raw_text": block_text,
                                "text": block_text,
                                "bbox": None,
                                "page_number": block.get("_pageNumber"),
                                "page_code": block.get("_pageCode"),
                            }
                        )
                    continue
                page_elements.extend(_extract_text_line_entries(block))
                continue
            if block.get("type") == 1:
                page_elements.append(
                    {
                        "kind": "image",
                        "block": block,
                    }
                )

        page_elements = _strip_page_edges(
            page_elements,
            part_title=part_title,
            chapter_title=chapter_title,
            section_title=section_title,
            strip_section_title=should_strip_section_title,
        )
        page_elements = _strip_reference_metadata_labels(page_elements)
        page_elements = _collapse_duplicate_labels(page_elements)
        should_strip_section_title = False

        paragraph_lines: list[dict[str, Any]] = []
        for element in page_elements:
            if element.get("kind") == "image":
                _flush_paragraph(paragraph_lines, normalized_blocks)
                paragraph_lines = []
                normalized_blocks.append(element["block"])
                continue

            if not paragraph_lines:
                paragraph_lines = [element]
                continue

            if _can_merge_lines(paragraph_lines[-1], element):
                paragraph_lines.append(element)
                continue

            _flush_paragraph(paragraph_lines, normalized_blocks)
            paragraph_lines = [element]

        _flush_paragraph(paragraph_lines, normalized_blocks)

    return normalized_blocks


def text_block_to_text(block: dict[str, Any]) -> str:
    if block.get("type") != 0:
        return ""

    normalized_text = block.get("_normalizedText")
    if isinstance(normalized_text, str):
        return normalized_text.strip()

    lines: list[str] = []
    for line in block.get("lines", []):
        line_text = "".join(span.get("text", "") for span in line.get("spans", []))
        line_text = line_text.replace("\x00", "").rstrip()
        if line_text.strip():
            lines.append(line_text.strip())
    return "\n".join(lines).strip()


def blocks_to_text(
    blocks: list[dict[str, Any]],
    *,
    part_title: str = "",
    chapter_title: str = "",
    section_title: str = "",
) -> str:
    normalized_blocks = normalize_content_blocks(
        blocks,
        part_title=part_title,
        chapter_title=chapter_title,
        section_title=section_title,
    )
    text_blocks = [text_block_to_text(block) for block in normalized_blocks if block.get("type") == 0]
    return "\n\n".join(block for block in text_blocks if block).strip()


def blocks_to_html(
    blocks: list[dict[str, Any]],
    *,
    part_title: str = "",
    chapter_title: str = "",
    section_title: str = "",
) -> str:
    normalized_blocks = normalize_content_blocks(
        blocks,
        part_title=part_title,
        chapter_title=chapter_title,
        section_title=section_title,
    )
    html_blocks: list[str] = []

    for block in normalized_blocks:
        block_type = block.get("type")
        if block_type == 0:
            block_text = text_block_to_text(block)
            if block_text:
                html_blocks.append(text_to_html(block_text))
            continue

        if block_type != 1:
            continue

        relative_path = block.get("_relativePath")
        if not relative_path:
            continue

        page_number = block.get("_pageNumber")
        page_code = block.get("_pageCode")
        alt_text = f"상표 이미지 (p.{page_number})" if page_number else "상표 이미지"
        caption_parts = [f"p.{page_number}"] if page_number else []
        if page_code:
            caption_parts.append(str(page_code))
        caption_html = (
            f"<figcaption>{escape(' · '.join(caption_parts))}</figcaption>" if caption_parts else ""
        )
        html_blocks.append(
            "\n".join(
                [
                    '<figure class="reader-image">',
                    (
                        f'<a href="{escape(relative_path)}" target="_blank" rel="noreferrer">'
                        f'<img src="{escape(relative_path)}" loading="lazy" alt="{escape(alt_text)}" />'
                        "</a>"
                    ),
                    caption_html,
                    "</figure>",
                ]
            ).replace("\n\n", "\n")
        )

    if not html_blocks:
        return "<p></p>"
    return "\n".join(html_blocks)


def load_page_texts(reader: pymupdf.Document) -> dict[int, str]:
    return {index + 1: extract_page_text(reader.load_page(index)) for index in range(reader.page_count)}


def fail(message: str) -> None:
    raise SystemExit(message)


def print_json_summary(label: str, payload: dict[str, Any]) -> None:
    print(f"{label}: {json.dumps(payload, ensure_ascii=False)}")


if sys.version_info < (3, 10):
    fail("Python 3.10 이상이 필요합니다.")
