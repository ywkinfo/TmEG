from __future__ import annotations

import importlib
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
build_content = importlib.import_module("pipeline.build_content")
common = importlib.import_module("pipeline.common")
build_code_to_page_map = build_content.build_code_to_page_map
join_page_range = build_content.join_page_range
trim_overview_ranges = build_content.trim_overview_ranges
blocks_to_html = common.blocks_to_html
blocks_to_text = common.blocks_to_text
collect_guardrail_errors = importlib.import_module("pipeline.qa_content").collect_guardrail_errors


class ContentGuardrailsTest(unittest.TestCase):
    def test_build_code_to_page_map_prefers_body_page_for_duplicate_codes(self) -> None:
        inventory = {
            "pages": [
                {"pageNumber": 7, "pageCode": "10101"},
                {"pageNumber": 25, "pageCode": "10101"},
                {"pageNumber": 26, "pageCode": "10102"},
            ]
        }

        mapping = build_code_to_page_map(inventory, {7, 8, 9})

        self.assertEqual(mapping["10101"], 25)
        self.assertEqual(mapping["10102"], 26)

    def test_build_code_to_page_map_falls_back_to_only_toc_page(self) -> None:
        inventory = {
            "pages": [
                {"pageNumber": 9, "pageCode": "20501"},
            ]
        }

        mapping = build_code_to_page_map(inventory, {7, 8, 9})

        self.assertEqual(mapping["20501"], 9)

    def test_collect_guardrail_errors_flags_toc_page_starts(self) -> None:
        document_data = {
            "chapters": [
                {
                    "id": "chapter-1",
                    "pageStart": 7,
                    "summary": "정상 본문",
                    "html": "<section><p>정상 본문</p></section>",
                }
            ]
        }
        search_index = [
            {"id": "search-1", "pageStart": 8, "excerpt": "정상 본문", "text": "정상 본문"}
        ]
        exploration_index = [{"id": "explore-1", "pageStart": 9, "excerpt": "정상 본문"}]

        errors = collect_guardrail_errors(
            document_data=document_data,
            search_index=search_index,
            exploration_index=exploration_index,
            toc_pages={7, 8, 9},
            document_title="상표심사기준",
        )

        self.assertTrue(any("chapter starts on toc page: chapter-1" in error for error in errors))
        self.assertTrue(any("search entry starts on toc page: search-1" in error for error in errors))
        self.assertTrue(any("exploration entry starts on toc page: explore-1" in error for error in errors))

    def test_collect_guardrail_errors_flags_toc_contamination(self) -> None:
        document_data = {
            "chapters": [
                {
                    "id": "chapter-summary",
                    "pageStart": 25,
                    "summary": "목 차 i 제1장 목적 10101",
                    "html": "<section><p>정상 본문</p></section>",
                },
                {
                    "id": "chapter-html",
                    "pageStart": 26,
                    "summary": "정상 본문",
                    "html": "<section><h2>제2장</h2><p>상표심사기준<br />ii<br />제7장 절차의 보완 및 보정 10701</p></section>",
                },
            ]
        }
        search_index = [
            {
                "id": "search-1",
                "pageStart": 25,
                "excerpt": "목 차 iii 제5장 1상표 1출원 20501",
                "text": "정상 본문",
            }
        ]
        exploration_index = [
            {
                "id": "explore-1",
                "pageStart": 25,
                "excerpt": "상표심사기준 ii 제7장 절차의 보완 및 보정 10701",
            }
        ]

        errors = collect_guardrail_errors(
            document_data=document_data,
            search_index=search_index,
            exploration_index=exploration_index,
            toc_pages={7, 8, 9},
            document_title="상표심사기준",
        )

        self.assertTrue(any("chapter summary looks like toc: chapter-summary" in error for error in errors))
        self.assertTrue(any("chapter html looks like toc: chapter-html" in error for error in errors))
        self.assertTrue(any("search entry excerpt looks like toc: search-1" in error for error in errors))
        self.assertTrue(any("exploration entry excerpt looks like toc: explore-1" in error for error in errors))

    def test_trim_overview_ranges_stops_before_first_child_page(self) -> None:
        chapters = [
            {
                "slug": "chapter-1",
                "pageStart": 10,
                "pageEnd": 14,
            }
        ]
        section_entries = [
            {
                "id": "chapter-1-overview",
                "chapterSlug": "chapter-1",
                "entryType": "overview",
                "pageStart": 10,
                "pageEnd": 14,
            },
            {
                "id": "item-1",
                "chapterSlug": "chapter-1",
                "entryType": "item",
                "pageStart": 12,
                "pageEnd": 14,
            },
        ]
        page_texts = {
            10: "개요 첫 문단",
            11: "개요 둘째 문단",
            12: "제1절 본문",
            13: "제1절 계속",
        }

        trim_overview_ranges(chapters, section_entries)
        overview_entry = section_entries[0]

        self.assertEqual(overview_entry["pageStart"], 10)
        self.assertEqual(overview_entry["pageEnd"], 11)
        self.assertEqual(
            join_page_range(page_texts, overview_entry["pageStart"], overview_entry["pageEnd"]),
            "개요 첫 문단\n\n개요 둘째 문단",
        )

    def test_trim_overview_ranges_leaves_title_only_when_first_child_starts_at_chapter_start(self) -> None:
        chapters = [
            {
                "slug": "chapter-1",
                "pageStart": 20,
                "pageEnd": 24,
            }
        ]
        section_entries = [
            {
                "id": "chapter-1-overview",
                "chapterSlug": "chapter-1",
                "entryType": "overview",
                "pageStart": 20,
                "pageEnd": 24,
            },
            {
                "id": "item-1",
                "chapterSlug": "chapter-1",
                "entryType": "item",
                "pageStart": 20,
                "pageEnd": 24,
            },
        ]
        page_texts = {
            20: "제1절 본문",
            21: "제1절 계속",
        }

        trim_overview_ranges(chapters, section_entries)
        overview_entry = section_entries[0]

        self.assertEqual(overview_entry["pageEnd"], 19)
        self.assertEqual(
            join_page_range(page_texts, overview_entry["pageStart"], overview_entry["pageEnd"]),
            "",
        )

    def test_blocks_to_text_ignores_image_blocks(self) -> None:
        blocks = [
            {
                "type": 0,
                "lines": [
                    {"spans": [{"text": "첫 문단"}]},
                    {"spans": [{"text": "둘째 줄"}]},
                ],
            },
            {
                "type": 1,
                "_relativePath": "generated/images/example.png",
                "_pageNumber": 138,
                "_pageCode": "30208",
            },
            {
                "type": 0,
                "lines": [{"spans": [{"text": "마지막 문단"}]}],
            },
        ]

        self.assertEqual(blocks_to_text(blocks), "첫 문단\n둘째 줄\n\n마지막 문단")

    def test_blocks_to_html_renders_text_and_image_blocks_in_order(self) -> None:
        blocks = [
            {
                "type": 0,
                "lines": [{"spans": [{"text": "앞 문단"}]}],
            },
            {
                "type": 1,
                "_relativePath": "generated/images/example.png",
                "_pageNumber": 138,
                "_pageCode": "30208",
            },
            {
                "type": 0,
                "lines": [{"spans": [{"text": "뒤 문단"}]}],
            },
        ]

        html = blocks_to_html(blocks)

        self.assertIn('<figure class="reader-image">', html)
        self.assertIn('src="generated/images/example.png"', html)
        self.assertIn('alt="상표 이미지 (p.138)"', html)
        self.assertIn('<figcaption>p.138 · 30208</figcaption>', html)
        self.assertLess(html.index("앞 문단"), html.index('<figure class="reader-image">'))
        self.assertLess(html.index('<figure class="reader-image">'), html.index("뒤 문단"))
