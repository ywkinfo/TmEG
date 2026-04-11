from __future__ import annotations

from .common import (
    count_image_blocks,
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
    page_count = reader.page_count
    pages: list[dict[str, object]] = []
    image_pages = 0
    empty_pages = 0

    for index in range(page_count):
        page_number = index + 1
        page = reader.load_page(index)
        text = extract_page_text(page)
        top_lines = extract_top_lines(text)
        image_count = count_image_blocks(page)
        if image_count:
            image_pages += 1
        if not text:
            empty_pages += 1
        pages.append(
            {
                "pageNumber": page_number,
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
            "pageCount": page_count,
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
            "pageCount": page_count,
            "imagePageCount": image_pages,
            "emptyPageCount": empty_pages,
        },
    )


if __name__ == "__main__":
    main()
