from __future__ import annotations

from collections import Counter
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
FORCED_LEGAL_ITEM_START_RE = re.compile(
    r"^(?:[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳](?:\s+|(?=[가-힣A-Za-z]))|\d{1,2}\.\s+|\d{1,2}(?:의\d{1,2})+\.\s+|\d{1,2}(?:\.\d{1,2}){1,2}\s+)"
)
INDENTED_KOREAN_LEGAL_ITEM_START_RE = re.compile(r"^\s+[가나다라마바사아자차카타파하]\.\s+")
BRACKET_LABEL_RE = re.compile(r"^[【《].+[】》]$")
HANGING_INDENT_SUBHEADING_START_RE = re.compile(
    r"^(?:[가나다라마바사아자차카타파하]\.\s+|\([ⅰⅱⅲⅳⅴⅵⅶⅷⅸⅹivxlcdmIVXLCDM]+\)\s*)"
)
HANGING_INDENT_BULLET_START_RE = re.compile(r"^(?:[-•▪※]\s+)")
HANGING_INDENT_WORD_FRAGMENT_RE = re.compile(r"^[가-힣]{2,}|^[가-힣][가-힣][^\s]*")
LARGE_INDENT_PARAGRAPH_START_RE = re.compile(
    r"^(?:다만|또한|그리고|그러나|한편|이 경우|다음(?:은|과|의)?|따라서|즉|예를 들어)"
)
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


SYNTHETIC_TIMELINE_SPECS: dict[str, dict[str, Any]] = {
    clean_title("《마지막 월에 해당일이 없는 경우 기간의 만료일》"): {
        "layout": "columns",
        "dates": ["12월 30일", "12월 31일", "2월 28일"],
        "labels": ["통지서송달일", "기산일", "지정기간만료"],
        "durations": ["지정기간 2개월"],
        "imageRelativePath": "generated/images/3d4c8a2e7b9f.png",
    },
    clean_title("《기간 만료일이 공휴일인 경우 기간연장 기산일》"): {
        "layout": "flow",
        "dates": ["7.19", "7.20", "9.19(수)", "9.20(목)", "9.24(월)", "10.19(목)"],
        "labels": ["통지서송달일", "기산일", "만료일", "기간연장 기산일", "만료일", "연장신청일", "연장기간 만료일"],
        "durations": ["지정 2개월", "연장기간 1개월"],
        "imageRelativePath": "generated/images/7f0f56d996ca.png",
    },
}
# HTML-only reader aids for tightly allowlisted procedure sections.
# These rows are editorial summaries for reader comprehension, not extracted source text,
# and they must never affect `blocks_to_text` or other search/locator paths.
SYNTHETIC_PROCEDURE_SPECS: dict[str, list[tuple[str, str]]] = {
    clean_title("1. 재심사의 청구 요건"): [
        ("시기 요건", "거절결정등본 송달일부터 3개월 이내에 재심사를 청구해야 한다."),
        ("대상 출원 요건", "거절결정이 있는 상표등록출원이어야 하고 거절결정불복심판 청구가 없어야 한다."),
        ("병행 가능 행위", "재심사의 청구와 함께 의견서나 보정서를 제출할 수 있다."),
        ("결과", "요건을 충족하면 재심사를 청구할 수 있고 요건을 벗어나면 허용되지 않는다."),
    ],
    clean_title("2. 보정 승인·각하 판단"): [
        ("선행 판단", "심사관은 보정각하 여부를 먼저 판단한다."),
        ("승인 시", "보정을 승인한 후 그 내용에 따라 심사한다."),
        ("각하 시", "보정을 각하한 후 보정 전 출원을 기준으로 심사한다."),
        ("후속 처분", "거절결정, 출원공고 후 등록결정, 또는 새로운 거절이유 통지로 이어질 수 있다."),
    ],
    clean_title("2. 절차보정(법§39)"): [
        ("흠결 유형", "절차상 방식 흠결이 있는 경우 절차보정 대상이 된다."),
        ("보정 기회", "심사관은 기간을 정하여 보정을 명하거나 출원인이 자진보정할 수 있다."),
        ("기간 준수", "지정된 기간 안에 흠결을 해소해야 한다."),
        ("결과", "적합하게 보정되면 절차가 계속되고 미보정이면 절차를 무효로 할 수 있다."),
    ],
    clean_title("3. 실체보정(법§40 내지 §41)"): [
        ("절차 단계", "출원공고 전후, 거절이유통지 후, 거절불복심판 후, 재심사 청구 시 등 단계별로 보정 가능성이 달라진다."),
        ("보정 가능 기간", "각 절차 단계에서 법이 정한 기간 안에만 실체보정을 할 수 있다."),
        ("허용 범위", "적법한 보정은 허용되지만 요지변경이나 기간 도과 보정은 허용되지 않는다."),
        ("효과", "적법한 보정은 최초출원일 기준을 유지하고 부적법한 보정은 반려되거나 요지변경 판단으로 이어진다."),
    ],
    clean_title("1. 직권보정의 시기"): [
        ("원칙", "출원공고결정을 할 때 직권보정이 가능하다."),
        ("조건 1", "1차 심사 시 명백한 오기 외 다른 거절이유가 없어야 한다."),
        ("조건 2", "거절이유 통지 후 다른 거절이유는 해소되었고 명백한 오기가 남아 있어야 한다."),
        ("처리", "심사관은 직권보정하면서 출원공고할 수 있다."),
    ],
    clean_title("3. 직권보정사항의 통보 및 의견제출기회 부여"): [
        ("통보", "직권보정 사항을 결정서와 상표공보에 기재해 출원인에게 알린다."),
        ("이의", "출원인은 출원공고기간 내에 의견서를 제출할 수 있다."),
        ("효과", "의견서가 제출되면 해당 직권보정은 처음부터 없었던 것으로 보고 출원공고결정도 함께 취소한다."),
        ("후속", "심사관은 직권보정 전 내용으로 재심사한다."),
    ],
    clean_title("4. 잘못된 직권보정의 무효"): [
        ("요건", "직권보정이 명백히 잘못된 경우다."),
        ("의견 제출", "출원인이 별도로 의견을 제출하지 않아도 된다."),
        ("효과", "그 직권보정은 처음부터 없었던 것으로 본다."),
    ],
    clean_title("1. 분할출원의 요건심사"): [
        ("시기", "현재 출원 계속 중이어야 하고 실체보정 가능기간 이내에 분할해야 한다."),
        ("주체", "원출원인 또는 정당한 승계인이 해야 하며 공동출원은 전원이 공동으로 진행한다."),
        ("상표 동일성", "원상표등록출원서의 상표와 분할출원서의 상표가 동일해야 한다."),
        ("범위", "원출원 지정상품 범위 내에서만 분할할 수 있다."),
    ],
    clean_title("2. 부적법한 분할출원에 대한 처리"): [
        ("기간 경과", "보정기간이 지난 뒤 제출된 분할출원은 반려한다."),
        ("부적법 사유", "실질적 확장, 삭제 미보정, 출원인 또는 상표견본 불일치 등이 있으면 불인정예고통지를 한다."),
        ("미해소", "의견서나 보정서로 해소하지 못하면 불인정확정통지 후 분할출원일 기준 신규출원으로 심사한다."),
        ("경합 처리", "원출원 거절결정 확정 시점에 따라 최초출원일 인정 여부가 달라질 수 있다."),
    ],
    clean_title("3. 분할출원의 효과"): [
        ("소급", "적법한 분할출원은 최초출원일에 출원한 것으로 본다."),
        ("우선권·특례", "우선권 주장과 출원시 특례는 분할출원일 기준으로 적용되고 30일 내 일부 취하가 가능하다."),
        ("재분할", "재분할도 요건을 충족하면 최초출원일에 출원한 것으로 간주한다."),
        ("독립성", "분할출원은 원출원과 별개 출원이므로 처음부터 다시 심사한다."),
    ],
    clean_title("1. 변경출원의 요건심사"): [
        ("시기", "최초출원의 등록여부결정 또는 심결이 확정되기 전에 변경해야 한다."),
        ("금지", "기초 등록상표에 무효·취소 심판이 청구되었거나 소멸된 경우에는 변경할 수 없다."),
        ("실체요건", "최초출원이 존재하고 목적물이 동일하며 변경출원인은 동일인 또는 정당한 승계인이어야 한다."),
        ("공동출원", "공동출원은 공유자 전원이 공동으로 해야 한다."),
    ],
    clean_title("3. 변경출원의 효과"): [
        ("소급", "변경출원은 최초출원일에 출원한 것으로 본다."),
        ("우선권·특례", "우선권 주장과 출원시 특례는 변경출원일 기준으로 적용한다."),
        ("자동 인정", "최초출원에 있던 우선권 주장이나 특례 주장은 변경출원에도 자동으로 인정된다."),
        ("취하 간주", "변경출원이 있으면 최초출원은 취하된 것으로 본다."),
    ],
    clean_title("4. 부적법한 변경출원에 대한 처리"): [
        ("기간 경과", "확정 이후의 변경출원은 부적법하므로 반려한다."),
        ("부적법 사유", "실질적 확장, 출원인 불일치, 상표견본 불일치 등이 있으면 변경출원불인정예고통지를 한다."),
        ("미해소", "의견서나 보정서로 해소하지 못하면 변경출원불인정확정통지를 한다."),
        ("후속 심사", "분할출원과 달리 변경 전 최초출원으로 심사를 계속 진행한다."),
    ],
    clean_title("1. 요지변경이 아닌 경우"): [
        ("감축", "지정상품 범위의 감축은 요지변경이 아니다."),
        ("오기 정정", "명백한 오기의 정정은 요지변경이 아니다."),
        ("불명료 해소", "불명료한 기재를 석명하는 보정은 요지변경이 아니다."),
        ("부기적 삭제", "상표의 부기적 부분을 삭제하는 보정은 요지변경이 아니다."),
    ],
    clean_title("4. 요지변경인 경우의 처리"): [
        ("요지변경 판단", "보정이 요지변경에 해당하면 보정각하결정을 하여야 한다."),
        ("불복 가능 여부", "보정각하결정에 대해서는 3개월 이내에 불복심판을 청구할 수 있다."),
        ("심사 중지 여부", "불복 가능 기간이 지나거나 심판 결과가 확정될 때까지 심사나 심판을 중지한다."),
        ("후속 절차", "불복이 불가능한 경우에는 해당 절차를 계속 진행한다."),
    ],
    clean_title("5. 요지변경임이 간과된 등록상표의 효력"): [
        ("문제된 보정 시점", "요지변경 보정이 간과된 시점이 출원공고결정등본 송달 전인지 후인지가 중요하다."),
        ("송달 전", "송달 전에 간과되었으면 보정서를 제출한 때에 출원한 것으로 본다."),
        ("송달 후", "송달 후에 간과되었으면 보정 전의 상표출원으로 상표권이 설정등록된 것으로 본다."),
        ("기준 출원", "사후 효력 판단은 간과된 요지변경 전후 중 어느 출원을 기준으로 볼지에 따라 갈린다."),
    ],
}
DATEISH_LINE_RE = re.compile(r"^(?:\d{1,2}월\s*\d{1,2}일|\d{1,2}\.\d{1,2}(?:\([^)]+\))?)$")
SYNTHETIC_TIMELINE_KEYWORDS = {
    "통지서송달일",
    "기산일",
    "지정기간만료",
    "만료일",
    "기간연장",
    "연장기간",
    "연장신청일",
    "지정기간",
    "개월",
}


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


def _bbox_width(bbox: Any) -> float | None:
    left = _bbox_value(bbox, 0)
    right = _bbox_value(bbox, 2)
    if left is None or right is None:
        return None
    return right - left


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


def _extract_text_line_entries_without_geometry(block: dict[str, Any]) -> list[dict[str, Any]]:
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
                "bbox": None,
                "page_number": block.get("_pageNumber"),
                "page_code": block.get("_pageCode"),
            }
        )
    return entries


def _has_distinct_line_geometry(block: dict[str, Any]) -> bool:
    return any(line.get("bbox") for line in block.get("lines", []))


def _is_single_row_fragmented_block(block: dict[str, Any]) -> bool:
    line_bboxes = [line.get("bbox") for line in block.get("lines", []) if line.get("bbox")]
    if len(line_bboxes) < 2:
        return False

    top = _bbox_value(line_bboxes[0], 1)
    bottom = _bbox_value(line_bboxes[0], 3)
    if top is None or bottom is None:
        return False

    for bbox in line_bboxes[1:]:
        current_top = _bbox_value(bbox, 1)
        current_bottom = _bbox_value(bbox, 3)
        if current_top is None or current_bottom is None:
            return False
        if abs(current_top - top) > 0.5 or abs(current_bottom - bottom) > 0.5:
            return False

    return True


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


def _starts_forced_legal_paragraph_item(text: str, raw_text: str | None = None) -> bool:
    if FORCED_LEGAL_ITEM_START_RE.match(normalize_line(text)):
        return True
    return bool(raw_text) and bool(INDENTED_KOREAN_LEGAL_ITEM_START_RE.match(raw_text))


def _ends_sentence(text: str) -> bool:
    return normalize_line(text).endswith((".", "!", "?", "…", ":", "】", "》"))


def _ends_with_hangul_syllable(text: str) -> bool:
    normalized = normalize_line(text)
    return bool(normalized) and bool(re.search(r"[가-힣]$", normalized))


def _starts_with_hangul_word_fragment(text: str) -> bool:
    return bool(HANGING_INDENT_WORD_FRAGMENT_RE.match(normalize_line(text)))


def _starts_with_large_indent_paragraph_start(text: str) -> bool:
    return bool(LARGE_INDENT_PARAGRAPH_START_RE.match(normalize_line(text)))


def _looks_like_hanging_indent_subheading(text: str, bbox: Any = None) -> bool:
    normalized = normalize_line(text)
    if not HANGING_INDENT_SUBHEADING_START_RE.match(normalized):
        return False

    width = _bbox_width(bbox)
    return len(normalized) <= 80 and (width is None or width <= 260.0)


def _allows_hanging_indent_merge(
    previous: dict[str, Any],
    current: dict[str, Any],
    *,
    line_gap: float,
    left_delta: float,
) -> bool:
    if not 0.0 <= line_gap <= 10.0:
        return False

    previous_width = _bbox_width(previous.get("bbox"))
    if previous_width is None or previous_width < 260.0:
        return False

    current_text = current.get("text", "")
    if _starts_with_large_indent_paragraph_start(current_text):
        return False

    if 24.0 < left_delta <= 56.0:
        return True

    return bool(
        56.0 < left_delta <= 120.0
        and _ends_with_hangul_syllable(previous.get("text", ""))
        and _starts_with_hangul_word_fragment(current_text)
    )


def _starts_hanging_indent_excluded_text(text: str, bbox: Any = None) -> bool:
    normalized = normalize_line(text)
    return bool(HANGING_INDENT_BULLET_START_RE.match(normalized)) or _looks_like_hanging_indent_subheading(
        normalized,
        bbox,
    )


def _normalize_common_broken_legal_spacing(text: str) -> str:
    return re.sub(r"([가-힣])에의 하여", r"\1에 의하여", text)


def _can_merge_lines_without_geometry(previous: dict[str, Any], current: dict[str, Any]) -> bool:
    if not previous["raw_text"].endswith((" ", "\u00a0")) and not current["raw_text"].startswith((" ", "\u00a0")):
        return False
    if _starts_with_large_indent_paragraph_start(current["text"]):
        return False
    if _starts_forced_legal_paragraph_item(current["text"], current.get("raw_text")):
        return False
    if _looks_like_short_heading(previous["text"]):
        return False
    if _looks_like_short_heading(current["text"]):
        return False
    if _starts_hanging_indent_excluded_text(current["text"]):
        return False
    if _ends_sentence(previous["text"]):
        return False
    return True


def _reflow_text_block_without_geometry(block: dict[str, Any]) -> tuple[str, str]:
    line_entries = _extract_text_line_entries_without_geometry(block)
    if not line_entries:
        return "", ""

    merged_raw_text = line_entries[0]["raw_text"]
    merged_text = line_entries[0]["text"]
    previous_line = line_entries[0]
    for entry in line_entries[1:]:
        if _can_merge_lines_without_geometry(previous_line, entry):
            separator = " " if merged_raw_text.endswith((" ", "\u00a0")) or entry["raw_text"].startswith((" ", "\u00a0")) else ""
            merged_raw_text = f"{merged_raw_text}{separator}{entry['raw_text']}"
            merged_text = f"{merged_text}{separator}{entry['text']}"
            previous_line = entry
            continue

        separator = "\n\n" if (
            _starts_with_large_indent_paragraph_start(entry["text"])
            or _starts_forced_legal_paragraph_item(entry["text"], entry.get("raw_text"))
            or _looks_like_short_heading(entry["text"])
            or _starts_hanging_indent_excluded_text(entry["text"])
        ) else "\n"
        merged_raw_text = f"{merged_raw_text}{separator}{entry['raw_text']}"
        merged_text = f"{merged_text}{separator}{entry['text']}"
        previous_line = entry

    return merged_raw_text, _normalize_common_broken_legal_spacing(merged_text.strip())


def _can_merge_lines(previous: dict[str, Any], current: dict[str, Any]) -> bool:
    previous_bbox = previous.get("bbox")
    current_bbox = current.get("bbox")
    previous_bottom = _bbox_value(previous_bbox, 3)
    current_top = _bbox_value(current_bbox, 1)
    previous_left = _bbox_value(previous_bbox, 0)
    current_left = _bbox_value(current_bbox, 0)

    if previous_bottom is None or current_top is None or previous_left is None or current_left is None:
        return False

    line_gap = current_top - previous_bottom
    left_delta = current_left - previous_left

    if line_gap > 10.0:
        return False
    if abs(left_delta) > 24.0 and not _allows_hanging_indent_merge(
        previous,
        current,
        line_gap=line_gap,
        left_delta=left_delta,
    ):
        return False
    if _starts_forced_legal_paragraph_item(current["text"], current.get("raw_text")):
        return False
    if _looks_like_short_heading(previous["text"], previous_bbox):
        return False
    if _looks_like_short_heading(current["text"], current_bbox):
        return False
    if _starts_hanging_indent_excluded_text(current["text"], current_bbox):
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
    merged_text = _normalize_common_broken_legal_spacing(merged_text)

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
    paragraph_lines: list[dict[str, Any]] = []

    for page_number in sorted(pages):
        page_elements: list[dict[str, Any]] = []
        for _, block in sorted(pages[page_number], key=_block_sort_key):
            if block.get("type") == 0:
                if block.get("lines") and (
                    not _has_distinct_line_geometry(block) or _is_single_row_fragmented_block(block)
                ):
                    block_raw_text, block_text = _reflow_text_block_without_geometry(block)
                    if block_text:
                        page_elements.append(
                            {
                                "kind": "text",
                                "raw_text": block_raw_text,
                                "text": block_text,
                                "bbox": block.get("bbox"),
                                "page_number": block.get("_pageNumber"),
                                "page_code": block.get("_pageCode"),
                            }
                        )
                    continue
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


def _is_synthetic_timeline_title(text: str) -> bool:
    return clean_title(text) in SYNTHETIC_TIMELINE_SPECS


def _is_synthetic_timeline_boundary(text: str) -> bool:
    normalized = normalize_line(text)
    if not normalized:
        return True
    if _is_synthetic_timeline_title(normalized):
        return True
    if BRACKET_LABEL_RE.fullmatch(normalized):
        return True
    if NUMBERED_HEADING_RE.match(normalized):
        return True
    if FORCED_LEGAL_ITEM_START_RE.match(normalized):
        return True
    return False


def _looks_like_synthetic_timeline_support_text(text: str) -> bool:
    normalized = clean_title(text)
    if not normalized:
        return False
    if DATEISH_LINE_RE.fullmatch(normalized):
        return True
    if any(keyword in normalized for keyword in SYNTHETIC_TIMELINE_KEYWORDS):
        return True
    return False


def _expand_synthetic_timeline_items(text: str) -> list[str]:
    normalized = clean_title(text)
    if not normalized:
        return []
    split_items = [normalize_line(part) for part in re.split(r"\s*·\s*", normalized) if normalize_line(part)]
    if len(split_items) > 1:
        return split_items
    return [normalized]


def _collect_synthetic_timeline_items(
    normalized_blocks: list[dict[str, Any]],
    start_index: int,
) -> tuple[list[str], int]:
    items: list[str] = []
    index = start_index + 1
    while index < len(normalized_blocks):
        block = normalized_blocks[index]
        if block.get("type") != 0:
            break
        text = text_block_to_text(block)
        if not text:
            break
        if _is_synthetic_timeline_boundary(text):
            break
        if not _looks_like_synthetic_timeline_support_text(text):
            break
        items.extend(_expand_synthetic_timeline_items(text))
        index += 1
    return items, index


def _take_expected_timeline_values(counter: Counter[str], expected_values: list[str]) -> list[str] | None:
    taken: list[str] = []
    for value in expected_values:
        if counter[value] <= 0:
            return None
        counter[value] -= 1
        taken.append(value)
    return taken


def _render_timeline_crop_figure(title: str, relative_path: str) -> str:
    return "\n".join(
        [
            '<figure class="reader-image">',
            (
                f'<a href="{escape(relative_path)}" target="_blank" rel="noreferrer">'
                f'<img src="{escape(relative_path)}" loading="lazy" alt="{escape(title)}" />'
                "</a>"
            ),
            f"<figcaption>{escape(title)}</figcaption>",
            "</figure>",
        ]
    )


def _render_synthetic_timeline_table(title: str, items: list[str]) -> str | None:
    spec = SYNTHETIC_TIMELINE_SPECS.get(clean_title(title))
    if spec is None:
        return None

    expected_counter = Counter(spec["dates"] + spec["labels"] + spec["durations"])
    actual_counter = Counter(items)
    if actual_counter != expected_counter:
        return None

    remaining = Counter(items)
    dates = _take_expected_timeline_values(remaining, spec["dates"])
    labels = _take_expected_timeline_values(remaining, spec["labels"])
    durations = _take_expected_timeline_values(remaining, spec["durations"])
    if dates is None or labels is None or durations is None or any(remaining.values()):
        return None

    image_relative_path = spec.get("imageRelativePath")
    if image_relative_path:
        return _render_timeline_crop_figure(title, image_relative_path)

    if spec["layout"] == "columns":
        label_cells = "".join(f"<td>{escape(label)}</td>" for label in labels)
        date_cells = "".join(f"<td>{escape(date)}</td>" for date in dates)
        duration_row = ""
        if durations:
            duration_row = (
                f'<tr><th scope="row">기간</th><td colspan="{len(labels)}">{escape(" · ".join(durations))}</td></tr>'
            )
        table_html = (
            "<table>"
            "<tbody>"
            f'<tr><th scope="row">표시</th>{label_cells}</tr>'
            f'<tr><th scope="row">날짜</th>{date_cells}</tr>'
            f"{duration_row}"
            "</tbody>"
            "</table>"
        )
    else:
        table_html = (
            "<table>"
            "<tbody>"
            f'<tr><th scope="row">날짜 흐름</th><td>{escape(" → ".join(dates))}</td></tr>'
            f'<tr><th scope="row">표시</th><td>{escape(" · ".join(labels))}</td></tr>'
            f'<tr><th scope="row">기간</th><td>{escape(" · ".join(durations))}</td></tr>'
            "</tbody>"
            "</table>"
        )

    return "\n".join(
        [
            '<figure class="reader-image reader-synthetic-figure">',
            f"<figcaption>{escape(title)}</figcaption>",
            table_html,
            "</figure>",
        ]
    )


def _render_synthetic_timeline_figure(
    normalized_blocks: list[dict[str, Any]],
    start_index: int,
) -> tuple[str | None, int]:
    title = text_block_to_text(normalized_blocks[start_index])
    if not _is_synthetic_timeline_title(title):
        return None, start_index + 1

    items, next_index = _collect_synthetic_timeline_items(normalized_blocks, start_index)
    html = _render_synthetic_timeline_table(title, items)
    if html is None:
        return None, start_index + 1
    return html, next_index


def _render_synthetic_procedure_figure(section_title: str) -> str | None:
    rows = SYNTHETIC_PROCEDURE_SPECS.get(clean_title(section_title))
    if rows is None:
        return None

    body_html = "".join(
        f'<tr><th scope="row">{escape(label)}</th><td>{escape(content)}</td></tr>' for label, content in rows
    )
    return "\n".join(
        [
            '<figure class="reader-image reader-synthetic-figure">',
            f"<figcaption>{escape(clean_title(section_title))}</figcaption>",
            f"<table><tbody>{body_html}</tbody></table>",
            "</figure>",
        ]
    )


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
    synthetic_procedure_html = _render_synthetic_procedure_figure(section_title)
    if synthetic_procedure_html is not None:
        html_blocks.append(synthetic_procedure_html)

    index = 0
    while index < len(normalized_blocks):
        synthetic_figure_html, next_index = _render_synthetic_timeline_figure(normalized_blocks, index)
        if synthetic_figure_html is not None:
            html_blocks.append(synthetic_figure_html)
            index = next_index
            continue

        block = normalized_blocks[index]
        block_type = block.get("type")
        if block_type == 0:
            block_text = text_block_to_text(block)
            if block_text:
                html_blocks.append(text_to_html(block_text))
            index += 1
            continue

        if block_type != 1:
            index += 1
            continue

        relative_path = block.get("_relativePath")
        if not relative_path:
            index += 1
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
        index += 1

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
