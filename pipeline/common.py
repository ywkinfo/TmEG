from __future__ import annotations

import json
import re
import sys
from html import escape
from pathlib import Path
from typing import Any

try:
    from pypdf import PdfReader
except ModuleNotFoundError as exc:
    raise SystemExit(
        "pypdf 모듈이 필요합니다. 현재 환경에서 `python -c 'import pypdf'`가 동작해야 합니다."
    ) from exc


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
SOURCE_DIR = DATA_DIR / "source"
GENERATED_DIR = DATA_DIR / "generated"
CONFIG_PATH = SOURCE_DIR / "source-config.json"
PAGE_CODE_RE = re.compile(r"\b\d{5,6}\b")
WHITESPACE_RE = re.compile(r"\s+")


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def resolve_pdf_path(config: dict[str, Any]) -> Path:
    pdf_path = ROOT_DIR / config["sourcePdf"]
    if not pdf_path.exists():
        raise SystemExit(f"원본 PDF를 찾을 수 없습니다: {pdf_path}")
    return pdf_path


def open_pdf(config: dict[str, Any]) -> PdfReader:
    return PdfReader(str(resolve_pdf_path(config)))


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


def extract_page_text(page: Any) -> str:
    return (page.extract_text() or "").replace("\x00", "").strip()


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


def load_page_texts(reader: PdfReader) -> dict[int, str]:
    return {index + 1: extract_page_text(page) for index, page in enumerate(reader.pages)}


def fail(message: str) -> None:
    raise SystemExit(message)


def print_json_summary(label: str, payload: dict[str, Any]) -> None:
    print(f"{label}: {json.dumps(payload, ensure_ascii=False)}")


if sys.version_info < (3, 10):
    fail("Python 3.10 이상이 필요합니다.")
