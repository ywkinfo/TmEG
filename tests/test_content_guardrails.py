from __future__ import annotations

import importlib
import unittest
from pathlib import Path
from unittest import mock


ROOT_DIR = Path(__file__).resolve().parents[1]
build_content = importlib.import_module("pipeline.build_content")
common = importlib.import_module("pipeline.common")
build_code_to_page_map = build_content.build_code_to_page_map
build_inventory_page_map = build_content.build_inventory_page_map
build_next_chapter_start_map = build_content.build_next_chapter_start_map
build_next_part_map = build_content.build_next_part_map
cap_entry_end_page = build_content.cap_entry_end_page
find_appendix_boundary_page = build_content.find_appendix_boundary_page
find_next_part_boundary_page = build_content.find_next_part_boundary_page
is_appendix_boundary_page = build_content.is_appendix_boundary_page
resolve_supplement_start = build_content.resolve_supplement_start
join_page_range = build_content.join_page_range
slice_entry_blocks = build_content.slice_entry_blocks
trim_overview_ranges = build_content.trim_overview_ranges
blocks_to_html = common.blocks_to_html
blocks_to_text = common.blocks_to_text
build_manifest_image_paths = importlib.import_module("pipeline.qa_content").build_manifest_image_paths
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
                "_pageNumber": 138,
                "_pageCode": "30208",
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
                "_pageNumber": 138,
                "_pageCode": "30208",
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

    def test_blocks_to_text_reflows_soft_wrapped_lines_and_strips_running_headers(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 25,
                "_pageCode": "10101",
                "bbox": (425.52, 60.03, 473.78, 70.01),
                "lines": [{"bbox": (425.52, 60.03, 473.78, 70.01), "spans": [{"text": "제1장 목 적"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 25,
                "_pageCode": "10101",
                "bbox": (226.56, 107.09, 312.0, 122.09),
                "lines": [{"bbox": (226.56, 107.09, 312.0, 122.09), "spans": [{"text": "제1장  목 적"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 25,
                "_pageCode": "10101",
                "bbox": (243.18, 181.14, 297.18, 193.14),
                "lines": [{"bbox": (243.18, 181.14, 297.18, 193.14), "spans": [{"text": "관련 법령"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 25,
                "_pageCode": "10101",
                "bbox": (68.22, 214.09, 105.92, 226.17),
                "lines": [{"bbox": (68.22, 214.09, 105.92, 226.17), "spans": [{"text": "【상표법】"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 25,
                "_pageCode": "10101",
                "bbox": (75.18, 235.69, 465.07, 247.81),
                "lines": [
                    {
                        "bbox": (75.18, 235.69, 465.07, 247.81),
                        "spans": [{"text": "제1조(목적) 이 법은 상표를 보호함으로써 상표 사용자의 업무상 신용 유지를 도모"}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 25,
                "_pageCode": "10101",
                "bbox": (85.14, 253.27, 437.23, 265.36),
                "lines": [
                    {
                        "bbox": (85.14, 253.27, 437.23, 265.36),
                        "spans": [{"text": "하여 산업발전에 이바지하고 수요자의 이익을 보호함을 목적으로 한다."}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 25,
                "_pageCode": "10101",
                "bbox": (63.78, 317.03, 159.53, 330.23),
                "lines": [{"bbox": (63.78, 317.03, 159.53, 330.23), "spans": [{"text": "1. 심사기준의 목적"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 25,
                "_pageCode": "10101",
                "bbox": (63.78, 342.44, 478.13, 354.52),
                "lines": [
                    {
                        "bbox": (63.78, 342.44, 478.13, 354.52),
                        "spans": [{"text": "    이 기준은 심사관이 상표심사(이의신청심사 포함)업무를 수행함에 있어 상표법 "}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 25,
                "_pageCode": "10101",
                "bbox": (80.22, 361.16, 478.14, 373.24),
                "lines": [
                    {
                        "bbox": (80.22, 361.16, 478.14, 373.24),
                        "spans": [{"text": "등 관련 법령을 적용하는데 필요한 구체적인 해석기준을 정함으로써 상표심사의 "}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 25,
                "_pageCode": "10101",
                "bbox": (80.22, 379.88, 295.03, 391.96),
                "lines": [
                    {
                        "bbox": (80.22, 379.88, 295.03, 391.96),
                        "spans": [{"text": "정확성·공정성·객관성 확보를 목적으로 한다."}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 25,
                "_pageCode": "10101",
                "bbox": (443.25, 684.09, 474.79, 695.07),
                "lines": [{"bbox": (443.25, 684.09, 474.79, 695.07), "spans": [{"text": "10101"}]}],
            },
        ]

        text = blocks_to_text(
            blocks,
            part_title="제1부 총칙",
            chapter_title="제1장 목적",
            section_title="1. 심사기준의 목적",
        )

        self.assertNotIn("제1장 목 적", text)
        self.assertNotIn("10101", text)
        self.assertNotIn("1. 심사기준의 목적", text)
        self.assertIn("도모하여 산업발전에", text)
        self.assertIn("상표법 등 관련 법령을 적용하는데 필요한 구체적인 해석기준", text)

    def test_blocks_to_text_keeps_numbered_heading_as_paragraph_boundary(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 25,
                "_pageCode": "10101",
                "bbox": (63.78, 317.03, 159.53, 330.23),
                "lines": [{"bbox": (63.78, 317.03, 159.53, 330.23), "spans": [{"text": "1. 심사기준의 목적"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 25,
                "_pageCode": "10101",
                "bbox": (63.78, 345.44, 478.13, 357.52),
                "lines": [
                    {
                        "bbox": (63.78, 345.44, 478.13, 357.52),
                        "spans": [{"text": "이 기준은 심사관이 상표심사(이의신청심사 포함)업무를 수행함에 있어 상표법 "}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 25,
                "_pageCode": "10101",
                "bbox": (80.22, 363.16, 478.14, 375.24),
                "lines": [
                    {
                        "bbox": (80.22, 363.16, 478.14, 375.24),
                        "spans": [{"text": "등 관련 법령을 적용하는데 필요한 구체적인 해석기준을 정함으로써 상표심사의 "}],
                    }
                ],
            },
        ]

        text = blocks_to_text(blocks)

        self.assertIn("1. 심사기준의 목적\n\n이 기준은", text)
        self.assertIn("상표법 등 관련 법령을 적용하는데 필요한 구체적인 해석기준", text)

    def test_blocks_to_text_merges_long_numbered_body_lines(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 25,
                "_pageCode": "10101",
                "bbox": (63.78, 444.02, 474.67, 456.10),
                "lines": [
                    {
                        "bbox": (63.78, 444.02, 474.67, 456.10),
                        "spans": [{"text": "2.1 심사관은 상표심사를 함에 있어 궁극적으로 상표법의 목적에 부합하는 심사를 하"}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 25,
                "_pageCode": "10101",
                "bbox": (85.44, 462.74, 478.15, 474.82),
                "lines": [
                    {
                        "bbox": (85.44, 462.74, 478.15, 474.82),
                        "spans": [{"text": "여야 하며, 관련 법령이나 심사기준 등을 적용함에 있어 획일적·형식적 심사를 "}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 25,
                "_pageCode": "10101",
                "bbox": (85.44, 481.46, 432.79, 493.54),
                "lines": [
                    {
                        "bbox": (85.44, 481.46, 432.79, 493.54),
                        "spans": [{"text": "지양하고 개별·구체적 타당성을 고려하여 정확한 심사를 하여야 한다."}],
                    }
                ],
            },
        ]

        text = blocks_to_text(blocks)

        self.assertIn("심사를 하여야 하며", text)
        self.assertIn("형식적 심사를 지양하고", text)

    def test_blocks_to_text_strips_interior_page_codes_and_update_markers(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 30,
                "_pageCode": "10204",
                "bbox": (63.78, 422.18, 176.83, 434.26),
                "lines": [{"bbox": (63.78, 422.18, 176.83, 434.26), "spans": [{"text": "2.1 무능력자의 행위능력"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 30,
                "_pageCode": "10204",
                "bbox": (63.78, 445.88, 478.19, 457.96),
                "lines": [{"bbox": (63.78, 445.88, 478.19, 457.96), "spans": [{"text": "2.1.1 무능력자는 민법에 따라 미성년자이다."}]}],
            },
            {
                "type": 0,
                "_pageNumber": 30,
                "_pageCode": "10204",
                "bbox": (63.03, 684.09, 97.11, 695.07),
                "lines": [{"bbox": (63.03, 684.09, 97.11, 695.07), "spans": [{"text": "10204"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 30,
                "_pageCode": "10204",
                "bbox": (392.46, 686.10, 474.78, 697.12),
                "lines": [{"bbox": (392.46, 686.10, 474.78, 697.12), "spans": [{"text": "(2024년 5월 추록)"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 31,
                "_pageCode": "10205",
                "bbox": (63.78, 120.18, 176.83, 132.26),
                "lines": [{"bbox": (63.78, 120.18, 176.83, 132.26), "spans": [{"text": "2.2 재외자의 행위능력"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 31,
                "_pageCode": "10205",
                "bbox": (63.78, 145.88, 478.19, 157.96),
                "lines": [{"bbox": (63.78, 145.88, 478.19, 157.96), "spans": [{"text": "2.2.1 재외자는 국적과 관계없이 국내에 주소가 없다."}]}],
            },
            {
                "type": 0,
                "_pageNumber": 31,
                "_pageCode": "10205",
                "bbox": (63.03, 684.09, 97.11, 695.07),
                "lines": [{"bbox": (63.03, 684.09, 97.11, 695.07), "spans": [{"text": "10205"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 31,
                "_pageCode": "10205",
                "bbox": (392.46, 686.10, 474.78, 697.12),
                "lines": [{"bbox": (392.46, 686.10, 474.78, 697.12), "spans": [{"text": "(2024년 5월 추록)"}]}],
            },
        ]

        text = blocks_to_text(blocks)

        self.assertNotIn("10204", text)
        self.assertNotIn("10205", text)
        self.assertNotIn("추록", text)
        self.assertIn("2.1 무능력자의 행위능력", text)
        self.assertIn("2.2 재외자의 행위능력", text)

    def test_blocks_to_text_collapses_duplicate_short_labels(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 25,
                "_pageCode": "10101",
                "bbox": (241.68, 174.01, 295.68, 186.01),
                "lines": [{"bbox": (241.68, 174.01, 295.68, 186.01), "spans": [{"text": "요건"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 25,
                "_pageCode": "10101",
                "bbox": (243.18, 181.15, 297.18, 193.15),
                "lines": [{"bbox": (243.18, 181.15, 297.18, 193.15), "spans": [{"text": "요건"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 25,
                "_pageCode": "10101",
                "bbox": (68.22, 214.10, 105.92, 226.18),
                "lines": [{"bbox": (68.22, 214.10, 105.92, 226.18), "spans": [{"text": "【상표법】"}]}],
            },
        ]

        text = blocks_to_text(blocks)

        self.assertEqual(text, "요건\n\n【상표법】")

    def test_blocks_to_text_strips_reference_metadata_labels_but_keeps_law_labels(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 25,
                "bbox": (10, 100, 80, 120),
                "lines": [{"bbox": (10, 100, 80, 120), "spans": [{"text": "관련 법령"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 25,
                "bbox": (10, 130, 100, 150),
                "lines": [{"bbox": (10, 130, 100, 150), "spans": [{"text": "【관련 법령】"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 25,
                "bbox": (10, 160, 120, 180),
                "lines": [{"bbox": (10, 160, 120, 180), "spans": [{"text": "【상표법】"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 25,
                "bbox": (10, 190, 220, 210),
                "lines": [{"bbox": (10, 190, 220, 210), "spans": [{"text": "[ 거절이유 ] 상표법 제34조"}]}],
            },
        ]

        text = blocks_to_text(blocks)

        self.assertNotIn("관련 법령", text)
        self.assertNotIn("【관련 법령】", text)
        self.assertIn("【상표법】", text)
        self.assertIn("[ 거절이유 ] 상표법 제34조", text)

    def test_blocks_to_text_collapses_exact_doubled_editorial_labels(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 113,
                "bbox": (10, 100, 180, 120),
                "lines": [{"bbox": (10, 100, 180, 120), "spans": [{"text": "관련 법령 및 취지관련 법령 및 취지"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 113,
                "bbox": (10, 130, 120, 150),
                "lines": [{"bbox": (10, 130, 120, 150), "spans": [{"text": "【상표법】"}]}],
            },
        ]

        text = blocks_to_text(blocks)

        self.assertEqual(text, "관련 법령 및 취지\n\n【상표법】")

    def test_blocks_to_text_strips_only_standalone_effective_date_notes(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 111,
                "bbox": (10, 100, 220, 120),
                "lines": [
                    {
                        "bbox": (10, 100, 220, 120),
                        "spans": [{"text": "제44조(출원의 변경) ... <개정 2023. 10. 31.>"}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 111,
                "bbox": (10, 130, 180, 150),
                "lines": [{"bbox": (10, 130, 180, 150), "spans": [{"text": "[시행일: 2024. 5. 1.]"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 111,
                "bbox": (10, 160, 220, 180),
                "lines": [
                    {
                        "bbox": (10, 160, 220, 180),
                        "spans": [{"text": "제45조(출원의 분할) ... <신설 2021. 10. 19.>"}],
                    }
                ],
            },
        ]

        text = blocks_to_text(blocks)

        self.assertNotIn("[시행일: 2024. 5. 1.]", text)
        self.assertIn("<개정 2023. 10. 31.>", text)
        self.assertIn("<신설 2021. 10. 19.>", text)

    def test_blocks_to_text_strips_page_edge_slash_heading_at_page_start(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 126,
                "bbox": (10, 100, 200, 120),
                "lines": [{"bbox": (10, 100, 200, 120), "spans": [{"text": "3 / 출원의 보정·분할·변경"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 126,
                "bbox": (10, 140, 300, 160),
                "lines": [{"bbox": (10, 140, 300, 160), "spans": [{"text": "제40조(출원공고결정 전의 보정) ..."}]}],
            },
        ]

        text = blocks_to_text(blocks)

        self.assertNotIn("3 / 출원의 보정·분할·변경", text)
        self.assertIn("제40조(출원공고결정 전의 보정)", text)

    def test_blocks_to_text_strips_page_edge_slash_heading_at_page_end(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 532,
                "bbox": (10, 100, 300, 120),
                "lines": [{"bbox": (10, 100, 300, 120), "spans": [{"text": "협의할 것을 통지하였음에도 불구하고 협의가 성립하지 아니한다."}]}],
            },
            {
                "type": 0,
                "_pageNumber": 532,
                "bbox": (10, 640, 120, 660),
                "lines": [{"bbox": (10, 640, 120, 660), "spans": [{"text": "10 / 보 칙"}]}],
            },
        ]

        text = blocks_to_text(blocks)

        self.assertNotIn("10 / 보 칙", text)
        self.assertIn("협의할 것을 통지하였음에도 불구하고 협의가 성립하지 아니한다.", text)

    def test_slice_entry_blocks_stops_before_next_same_page_section_title(self) -> None:
        chapter_entries = [
            {
                "entryType": "item",
                "sectionTitle": "1. 심사기준의 목적",
            },
            {
                "entryType": "item",
                "sectionTitle": "2. 상표심사의 기본원칙",
            },
        ]
        blocks = [
            {
                "type": 0,
                "lines": [{"spans": [{"text": "1. 심사기준의 목적"}]}],
            },
            {
                "type": 0,
                "lines": [{"spans": [{"text": "첫 번째 섹션 본문"}]}],
            },
            {
                "type": 0,
                "lines": [{"spans": [{"text": "2. 상표심사의 기본원칙"}]}],
            },
            {
                "type": 0,
                "lines": [{"spans": [{"text": "두 번째 섹션 본문"}]}],
            },
        ]

        sliced = slice_entry_blocks(blocks, chapter_entries[0], chapter_entries[1:])

        self.assertEqual(len(sliced), 1)
        self.assertEqual(blocks_to_text(sliced), "첫 번째 섹션 본문")

    def test_slice_entry_blocks_uses_numbered_subheading_when_parent_title_is_absent(self) -> None:
        chapter_entries = [
            {
                "entryType": "item",
                "sectionTitle": "1. 권리능력",
            },
            {
                "entryType": "item",
                "sectionTitle": "2. 행위능력",
            },
        ]
        blocks = [
            {
                "type": 0,
                "_pageNumber": 30,
                "bbox": (10, 40, 200, 60),
                "lines": [{"spans": [{"text": "우려가 없다는 점이 인정될 경우 등록이 가능합니다."}]}],
            },
            {
                "type": 0,
                "_pageNumber": 30,
                "bbox": (10, 100, 200, 120),
                "lines": [{"spans": [{"text": "2.1 무능력자의 행위능력"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 30,
                "bbox": (10, 140, 200, 160),
                "lines": [{"spans": [{"text": "행위능력 본문"}]}],
            },
        ]

        sliced = slice_entry_blocks(blocks, chapter_entries[1], [])

        self.assertEqual(blocks_to_text(sliced), "2.1 무능력자의 행위능력\n\n행위능력 본문")

    def test_build_next_chapter_start_map_tracks_following_chapter_boundaries(self) -> None:
        chapters = [
            {"slug": "chapter-a", "pageStart": 123},
            {"slug": "chapter-b", "pageStart": 159},
            {"slug": "chapter-c", "pageStart": 531},
        ]

        next_map = build_next_chapter_start_map(chapters)

        self.assertEqual(next_map, {"chapter-a": 159, "chapter-b": 531, "chapter-c": None})

    def test_cap_entry_end_page_stops_before_next_chapter_start(self) -> None:
        entry = {"pageStart": 156, "pageEnd": 160}

        capped_end = cap_entry_end_page(entry, 159)

        self.assertEqual(capped_end, 158)

    def test_find_next_part_boundary_page_detects_standalone_marker_page(self) -> None:
        page_blocks = {
            156: [
                {"type": 0, "bbox": (10, 100, 200, 120), "lines": [{"spans": [{"text": "현재 섹션 본문"}]}]},
            ],
            157: [
                {"type": 0, "bbox": (10, 100, 40, 120), "lines": [{"spans": [{"text": "4"}]}]},
                {"type": 0, "bbox": (10, 140, 220, 160), "lines": [{"spans": [{"text": "상표등록의 요건"}]}]},
            ],
        }
        next_part = {
            "label": "제4부",
            "title": "상표등록의 요건",
            "fullTitle": "제4부 상표등록의 요건",
        }

        boundary_page = find_next_part_boundary_page(page_blocks, 156, 160, next_part)

        self.assertEqual(boundary_page, 157)

    def test_is_appendix_boundary_page_requires_null_page_code_and_marker(self) -> None:
        self.assertTrue(is_appendix_boundary_page({"pageCode": None, "topLines": ["부 칙"]}))
        self.assertTrue(is_appendix_boundary_page({"pageCode": None, "topLines": ["별 첨"]}))
        self.assertFalse(is_appendix_boundary_page({"pageCode": "100101", "topLines": ["부 칙"]}))
        self.assertFalse(is_appendix_boundary_page({"pageCode": None, "topLines": ["재검토기한"]}))

    def test_find_appendix_boundary_page_detects_first_marker_page(self) -> None:
        inventory_page_map = build_inventory_page_map(
            {
                "pages": [
                    {"pageNumber": 537, "pageCode": "100301", "topLines": ["제3장 심사절차의 중지"]},
                    {"pageNumber": 538, "pageCode": None, "topLines": []},
                    {"pageNumber": 539, "pageCode": None, "topLines": ["부 칙"]},
                    {"pageNumber": 540, "pageCode": None, "topLines": []},
                ]
            }
        )

        boundary_page = find_appendix_boundary_page(inventory_page_map, 537, 575)

        self.assertEqual(boundary_page, 539)

    def test_resolve_supplement_start_backscans_reference_preamble_pages(self) -> None:
        page_code_map = {
            "50704": 248,
            "50706": 250,
            "50707": 251,
            "50708": 252,
        }
        page_blocks = {
            248: [
                {"type": 0, "_pageCode": "50704", "bbox": (10, 100, 220, 120), "lines": [{"spans": [{"text": "4. 다른 조문과의 관계"}]}]},
            ],
            249: [
                {"type": 0, "_pageCode": None, "bbox": (10, 100, 220, 120), "lines": [{"spans": [{"text": "관련 법령 및 취지"}]}]},
                {"type": 0, "_pageCode": None, "bbox": (10, 130, 160, 150), "lines": [{"spans": [{"text": "【상표법】"}]}]},
            ],
            250: [
                {"type": 0, "_pageCode": "50706", "bbox": (10, 100, 220, 120), "lines": [{"spans": [{"text": "【상표법시행규칙】"}]}]},
            ],
            251: [
                {"type": 0, "_pageCode": "50707", "bbox": (10, 100, 340, 120), "lines": [{"spans": [{"text": "제7장 선등록상표와 동일·유사한 상표- 보충기준1 : 상표공존동의제도"}]}]},
            ],
            252: [
                {"type": 0, "_pageCode": "50708", "bbox": (10, 100, 220, 120), "lines": [{"spans": [{"text": "1. 공존동의서 제출 요건"}]}]},
            ],
        }
        supplement = {
            "label": "보충기준1",
            "title": "상표공존동의제도",
            "fullTitle": "보충기준1: 상표공존동의제도",
            "pageCode": "50705",
            "items": [{"pageCode": "50707"}, {"pageCode": "50708"}],
        }

        supplement_start, used_fallback = resolve_supplement_start(
            page_code_map,
            page_blocks,
            supplement,
            part_title="제5부 상표등록을 받을 수 없는 상표",
            chapter_title="제7장 선등록상표와 동일·유사한 상표",
            chapter_start=248,
        )

        self.assertTrue(used_fallback)
        self.assertEqual(supplement_start, 249)

    def test_resolve_supplement_start_keeps_existing_page_code_when_present(self) -> None:
        page_code_map = {"50712": 256}
        page_blocks = {
            256: [
                {"type": 0, "_pageCode": "50712", "bbox": (10, 100, 240, 120), "lines": [{"spans": [{"text": "보충기준2 : 상표의 동일·유사"}]}]},
                {"type": 0, "_pageCode": "50712", "bbox": (10, 130, 180, 150), "lines": [{"spans": [{"text": "1. 상표의 동일"}]}]},
            ],
        }
        supplement = {
            "label": "보충기준2",
            "title": "상표의 동일·유사",
            "fullTitle": "보충기준2: 상표의 동일·유사",
            "pageCode": "50712",
            "items": [{"pageCode": "50712"}],
        }

        supplement_start, used_fallback = resolve_supplement_start(
            page_code_map,
            page_blocks,
            supplement,
            part_title="제5부 상표등록을 받을 수 없는 상표",
            chapter_title="제7장 선등록상표와 동일·유사한 상표",
            chapter_start=248,
        )

        self.assertFalse(used_fallback)
        self.assertEqual(supplement_start, 256)

    def test_build_manifest_image_paths_match_generated_html_src(self) -> None:
        image_manifest = {
            "images": [
                {"id": "image-1", "relativePath": "images/example.png"},
            ]
        }

        self.assertEqual(build_manifest_image_paths(image_manifest), {"generated/images/example.png"})

    def test_build_page_blocks_uses_generated_root_relative_image_paths(self) -> None:
        image_bytes = b"example-image"
        image_id = build_content.hashlib.sha1(image_bytes).hexdigest()[:12]
        raw_image_block = {
            "type": 1,
            "image": image_bytes,
            "ext": "png",
            "mask": None,
        }

        class FakePage:
            def get_image_info(self, hashes: bool = True, xrefs: bool = True) -> list[dict[str, int]]:
                return [{"xref": 0}]

        class FakeReader:
            def load_page(self, index: int) -> FakePage:
                self.loaded_index = index
                return FakePage()

        inventory = {"pages": [{"pageNumber": 138, "pageCode": "30208"}]}
        image_manifest = {"images": [{"id": image_id, "relativePath": "images/example.png"}]}

        with (
            mock.patch.object(build_content, "extract_page_blocks", return_value=[raw_image_block]),
            mock.patch.object(build_content, "match_inline_image_block", return_value=raw_image_block),
            mock.patch.object(build_content, "normalize_image_bytes", return_value=(image_bytes, "png")),
        ):
            page_blocks = build_content.build_page_blocks(FakeReader(), inventory, image_manifest)

        self.assertEqual(page_blocks[138][0]["_relativePath"], "generated/images/example.png")
