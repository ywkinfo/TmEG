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
TITLE_LEADER_RE = re.compile(r"[·•⋯…]{3,}")


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


def normalize_space(value: str) -> str:
    return WHITESPACE_RE.sub(" ", value).strip()


def clean_title(value: str) -> str:
    return normalize_space(TITLE_LEADER_RE.sub("", value or ""))


def strip_running_header(
    text: str,
    *,
    chapter_title: str | None = None,
    section_title: str | None = None,
    page_code: str | None = None,
) -> str:
    def canonicalize_title(value: str | None) -> str:
        return re.sub(r"\s+", "", clean_title(value or ""))

    def strip_page_code_suffix(line: str) -> str:
        if not page_code:
            return line
        if line == page_code:
            return ""
        if line.endswith(page_code):
            return line[: -len(page_code)].strip()
        return line

    lines = text.replace("\x00", "").splitlines()
    candidates = {
        candidate
        for candidate in (
            canonicalize_title(chapter_title),
            canonicalize_title(section_title),
        )
        if candidate
    }

    while lines and not normalize_space(lines[0]):
        lines.pop(0)

    while lines:
        normalized = normalize_space(lines[0])
        if not normalized:
            lines.pop(0)
            continue
        if page_code and normalized == page_code:
            lines.pop(0)
            continue
        normalized_without_page_code = normalize_space(strip_page_code_suffix(normalized))
        canonical_line = re.sub(r"\s+", "", clean_title(normalized_without_page_code))
        if canonical_line and canonical_line in candidates:
            lines.pop(0)
            continue
        break

    return "\n".join(line.rstrip() for line in lines).strip()


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


def load_page_texts(reader: pymupdf.Document) -> dict[int, str]:
    return {index + 1: extract_page_text(reader.load_page(index)) for index in range(reader.page_count)}


def fail(message: str) -> None:
    raise SystemExit(message)


def print_json_summary(label: str, payload: dict[str, Any]) -> None:
    print(f"{label}: {json.dumps(payload, ensure_ascii=False)}")


if sys.version_info < (3, 10):
    fail("Python 3.10 이상이 필요합니다.")
