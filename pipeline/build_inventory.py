from __future__ import annotations

from .common import (
    detect_page_code,
    extract_page_text,
    extract_top_lines,
    load_config,
    open_pdf,
    print_json_summary,
    write_json,
)


def main() -> None:
    config = load_config()
    reader = open_pdf(config)
    pages: list[dict[str, object]] = []
    image_pages = 0
    empty_pages = 0

    for index, page in enumerate(reader.pages, start=1):
        text = extract_page_text(page)
        top_lines = extract_top_lines(text)
        image_count = len(getattr(page, "images", []) or [])
        if image_count:
            image_pages += 1
        if not text:
            empty_pages += 1
        pages.append(
            {
                "pageNumber": index,
                "pageCode": detect_page_code(top_lines),
                "charCount": len(text),
                "imageCount": image_count,
                "hasText": bool(text),
                "topLines": top_lines,
            }
        )

    payload = {
        "meta": {
            "title": config["documentTitle"],
            "pageCount": len(reader.pages),
            "imagePageCount": image_pages,
            "emptyPageCount": empty_pages,
        },
        "pages": pages,
    }
    target = write_json("pdf-inventory.json", payload)
    print_json_summary(
        "inventory",
        {
            "target": str(target),
            "pageCount": len(reader.pages),
            "imagePageCount": image_pages,
            "emptyPageCount": empty_pages,
        },
    )


if __name__ == "__main__":
    main()
