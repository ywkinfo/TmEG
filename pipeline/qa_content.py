from __future__ import annotations

import re
from typing import Any

from .build_images import is_decorative_page, load_image_exclusion
from .common import GENERATED_DIR, load_config, load_generated_json, normalize_space


HTML_TAG_RE = re.compile(r"<[^>]+>")
IMG_SRC_RE = re.compile(r'<img[^>]+src="([^"]+)"', re.IGNORECASE)


def normalize_leading_text(value: str) -> str:
    without_html = HTML_TAG_RE.sub(" ", value or "")
    return normalize_space(without_html)


def looks_like_toc_text(value: str, document_title: str) -> bool:
    text = normalize_leading_text(value)
    if not text:
        return False
    if text.startswith("목 차") or text.startswith("목차"):
        return True
    if document_title:
        return bool(re.match(rf"^{re.escape(document_title)} [ivxlcdm]+\b", text, re.IGNORECASE))
    return False


def looks_like_toc_html(value: str, document_title: str) -> bool:
    if not value:
        return False
    if re.search(r"<p>\s*(목\s*차|목차)\b", value, re.IGNORECASE):
        return True
    if not document_title:
        return False
    return bool(
        re.search(
            rf"<p>\s*{re.escape(document_title)}\s*<br\s*/?>\s*[ivxlcdm]+\b",
            value,
            re.IGNORECASE,
        )
    )


def collect_guardrail_errors(
    document_data: dict[str, Any],
    search_index: list[dict[str, Any]],
    exploration_index: list[dict[str, Any]],
    toc_pages: set[int],
    document_title: str,
) -> list[str]:
    errors: list[str] = []

    for chapter in document_data.get("chapters", []):
        chapter_id = chapter.get("id", "<unknown>")
        page_start = chapter.get("pageStart")
        if page_start in toc_pages:
            errors.append(f"chapter starts on toc page: {chapter_id} -> {page_start}")
        if looks_like_toc_text(chapter.get("summary", ""), document_title):
            errors.append(f"chapter summary looks like toc: {chapter_id}")
        if looks_like_toc_html(chapter.get("html", ""), document_title):
            errors.append(f"chapter html looks like toc: {chapter_id}")

    for entry in search_index:
        entry_id = entry.get("id", "<unknown>")
        page_start = entry.get("pageStart")
        if page_start in toc_pages:
            errors.append(f"search entry starts on toc page: {entry_id} -> {page_start}")
        if looks_like_toc_text(entry.get("excerpt", ""), document_title):
            errors.append(f"search entry excerpt looks like toc: {entry_id}")
        elif looks_like_toc_text(entry.get("text", ""), document_title):
            errors.append(f"search entry text looks like toc: {entry_id}")

    for entry in exploration_index:
        entry_id = entry.get("id", "<unknown>")
        page_start = entry.get("pageStart")
        if page_start in toc_pages:
            errors.append(f"exploration entry starts on toc page: {entry_id} -> {page_start}")
        if looks_like_toc_text(entry.get("excerpt", ""), document_title):
            errors.append(f"exploration entry excerpt looks like toc: {entry_id}")

    return errors


def expect_equal(label: str, actual: int, expected: int, errors: list[str]) -> None:
    if actual != expected:
        errors.append(f"{label}: expected {expected}, got {actual}")


def main() -> None:
    config = load_config()
    expected = config["expectedStructure"]
    document_title = config["documentTitle"]
    image_exclusion = load_image_exclusion(config)
    inventory = load_generated_json("pdf-inventory.json")
    toc = load_generated_json("toc.json")
    image_manifest = load_generated_json("image-manifest.json")
    document_data = load_generated_json("document-data.json")
    search_index = load_generated_json("search-index.json")
    exploration_index = load_generated_json("exploration-index.json")
    coverage = load_generated_json("coverage-report.json")
    toc_pages = set(toc["meta"].get("tocPages", []))
    inventory_pages = {page["pageNumber"]: page for page in inventory["pages"]}
    manifest_image_paths = {
        f"public/generated/{image['relativePath']}"
        for image in image_manifest.get("images", [])
        if image.get("relativePath")
    }
    search_index_by_key = {
        (entry["id"], entry["chapterTitle"], entry["pageStart"]): entry for entry in search_index
    }

    errors: list[str] = []

    expect_equal("pageCount", inventory["meta"]["pageCount"], expected["pageCount"], errors)
    expect_equal("partCount", toc["meta"]["partCount"], expected["partCount"], errors)
    expect_equal("chapterCount", toc["meta"]["chapterCount"], expected["chapterCount"], errors)
    expect_equal("itemCount", toc["meta"]["itemCount"], expected["itemCount"], errors)
    expect_equal("supplementCount", toc["meta"]["supplementCount"], expected["supplementCount"], errors)
    expect_equal(
        "document chapterCount",
        document_data["meta"]["chapterCount"],
        expected["chapterCount"],
        errors,
    )

    if not search_index:
        errors.append("search-index.json이 비어 있습니다.")

    if coverage["missingPageCodes"]:
        errors.append(f"missing page codes: {', '.join(coverage['missingPageCodes'])}")

    if coverage["unmappedChapterCount"] != 0:
        errors.append(f"unmappedChapterCount: {coverage['unmappedChapterCount']}")

    if coverage["unmappedSectionCount"] != 0:
        errors.append(f"unmappedSectionCount: {coverage['unmappedSectionCount']}")

    for image in image_manifest.get("images", []):
        image_id = image.get("id", "<unknown>")
        relative_path = image.get("relativePath")
        if not relative_path:
            errors.append(f"image manifest entry has no relativePath: {image_id}")
            continue
        image_path = GENERATED_DIR / relative_path
        if not image_path.exists():
            errors.append(f"image file missing: {image_id} -> {image_path}")
            continue
        if image_path.stat().st_size != image.get("byteSize"):
            errors.append(
                f"image byteSize mismatch: {image_id} -> expected {image.get('byteSize')}, got {image_path.stat().st_size}"
            )

        for page_number in image.get("pageNumbers", []):
            if page_number in toc_pages:
                errors.append(f"image manifest includes toc page: {image_id} -> {page_number}")
            if page_number in set(image_exclusion["excludeCoverPages"]):
                errors.append(f"image manifest includes excluded cover page: {image_id} -> {page_number}")
            page_meta = inventory_pages.get(page_number)
            if page_meta and is_decorative_page(page_meta, image_exclusion):
                errors.append(f"image manifest includes decorative page: {image_id} -> {page_number}")

    for chapter in document_data.get("chapters", []):
        chapter_id = chapter.get("id", "<unknown>")
        has_image = bool(chapter.get("hasImage"))
        image_count = int(chapter.get("imageCount", 0) or 0)
        if has_image != (image_count > 0):
            errors.append(f"chapter image metadata mismatch: {chapter_id}")

        image_sources = IMG_SRC_RE.findall(chapter.get("html", ""))
        if len(image_sources) != image_count:
            errors.append(
                f"chapter image count does not match html img tags: {chapter_id} -> {image_count} vs {len(image_sources)}"
            )
        for src in image_sources:
            if src not in manifest_image_paths:
                errors.append(f"chapter html references unknown image src: {chapter_id} -> {src}")

    for entry in search_index:
        entry_id = entry.get("id", "<unknown>")
        has_image = bool(entry.get("hasImage"))
        image_count = int(entry.get("imageCount", 0) or 0)
        if has_image != (image_count > 0):
            errors.append(f"search image metadata mismatch: {entry_id}")

    for entry in exploration_index:
        entry_id = entry.get("id", "<unknown>")
        has_image = entry.get("hasImage")
        if has_image is None:
            errors.append(f"exploration entry missing hasImage: {entry_id}")
            continue
        search_entry = search_index_by_key.get(
            (entry_id, entry.get("chapterTitle"), entry.get("pageStart"))
        )
        if search_entry and bool(has_image) != bool(search_entry.get("hasImage")):
            errors.append(f"exploration image metadata mismatch: {entry_id}")

    errors.extend(
        collect_guardrail_errors(
            document_data=document_data,
            search_index=search_index,
            exploration_index=exploration_index,
            toc_pages=toc_pages,
            document_title=document_title,
        )
    )

    if errors:
        raise SystemExit("QA failed\n- " + "\n- ".join(errors))

    print(
        "qa: "
        f"pages={inventory['meta']['pageCount']} "
        f"parts={toc['meta']['partCount']} "
        f"chapters={toc['meta']['chapterCount']} "
        f"items={toc['meta']['itemCount']} "
        f"supplements={toc['meta']['supplementCount']} "
        f"searchEntries={len(search_index)}"
    )


if __name__ == "__main__":
    main()
