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
extend_end_page_for_next_sibling = build_content.extend_end_page_for_next_sibling
extend_overview_end_page_for_leading_content = build_content.extend_overview_end_page_for_leading_content
find_appendix_boundary_page = build_content.find_appendix_boundary_page
find_next_part_boundary_page = build_content.find_next_part_boundary_page
is_appendix_boundary_page = build_content.is_appendix_boundary_page
page_has_meaningful_leading_content_before_title = build_content.page_has_meaningful_leading_content_before_title
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

    def test_blocks_to_html_upgrades_month_end_timeline_cluster_to_synthetic_figure(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 46,
                "_pageCode": "10406",
                "lines": [{"spans": [{"text": "앞 설명 문단"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 46,
                "_pageCode": "10406",
                "lines": [{"spans": [{"text": "《마지막 월에 해당일이 없는 경우 기간의 만료일》"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 46,
                "_pageCode": "10406",
                "lines": [{"spans": [{"text": "12월 30일"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 46,
                "_pageCode": "10406",
                "lines": [{"spans": [{"text": "12월 31일"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 46,
                "_pageCode": "10406",
                "lines": [{"spans": [{"text": "2월 28일"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 46,
                "_pageCode": "10406",
                "lines": [{"spans": [{"text": "지정기간 2개월"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 46,
                "_pageCode": "10406",
                "lines": [{"spans": [{"text": "통지서송달일"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 46,
                "_pageCode": "10406",
                "lines": [{"spans": [{"text": "기 산 일"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 46,
                "_pageCode": "10406",
                "lines": [{"spans": [{"text": "지정기간만료"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 46,
                "_pageCode": "10406",
                "lines": [{"spans": [{"text": "2.2.4 상표에 관한 절차에 있어서 기간의 말일이 공휴일에 해당하면 기간은 다음 날로 만료한다."}]}],
            },
        ]

        html = blocks_to_html(blocks)

        self.assertIn('<figure class="reader-image">', html)
        self.assertIn('<figcaption>《마지막 월에 해당일이 없는 경우 기간의 만료일》</figcaption>', html)
        self.assertIn('src="generated/images/3d4c8a2e7b9f.png"', html)
        self.assertLess(html.index("앞 설명 문단"), html.index('generated/images/3d4c8a2e7b9f.png'))
        self.assertLess(html.index('generated/images/3d4c8a2e7b9f.png'), html.index("2.2.4 상표에 관한 절차에 있어서"))
        self.assertEqual(
            blocks_to_text(blocks),
            "앞 설명 문단\n\n《마지막 월에 해당일이 없는 경우 기간의 만료일》\n\n12월 30일\n\n12월 31일\n\n2월 28일\n\n지정기간 2개월\n\n통지서송달일\n\n기 산 일\n\n지정기간만료\n\n2.2.4 상표에 관한 절차에 있어서 기간의 말일이 공휴일에 해당하면 기간은 다음 날로 만료한다.",
        )

    def test_blocks_to_html_upgrades_holiday_extension_timeline_cluster_to_synthetic_figure(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 46,
                "_pageCode": "10406",
                "lines": [{"spans": [{"text": "앞 설명 문단"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 46,
                "_pageCode": "10406",
                "lines": [{"spans": [{"text": "《기간 만료일이 공휴일인 경우 기간연장 기산일》"}]}],
            },
            {"type": 0, "_pageNumber": 46, "_pageCode": "10406", "lines": [{"spans": [{"text": "7.20"}]}]},
            {"type": 0, "_pageNumber": 46, "_pageCode": "10406", "lines": [{"spans": [{"text": "9.19(수)"}]}]},
            {"type": 0, "_pageNumber": 46, "_pageCode": "10406", "lines": [{"spans": [{"text": "9.20(목)"}]}]},
            {"type": 0, "_pageNumber": 46, "_pageCode": "10406", "lines": [{"spans": [{"text": "9.24(월)"}]}]},
            {"type": 0, "_pageNumber": 46, "_pageCode": "10406", "lines": [{"spans": [{"text": "10.19(목)"}]}]},
            {"type": 0, "_pageNumber": 46, "_pageCode": "10406", "lines": [{"spans": [{"text": "7.19"}]}]},
            {"type": 0, "_pageNumber": 46, "_pageCode": "10406", "lines": [{"spans": [{"text": "지정 2개월"}]}]},
            {"type": 0, "_pageNumber": 46, "_pageCode": "10406", "lines": [{"spans": [{"text": "연장기간 1개월"}]}]},
            {"type": 0, "_pageNumber": 46, "_pageCode": "10406", "lines": [{"spans": [{"text": "연장기간 만료일"}]}]},
            {"type": 0, "_pageNumber": 46, "_pageCode": "10406", "lines": [{"spans": [{"text": "통지서송달일"}]}]},
            {"type": 0, "_pageNumber": 46, "_pageCode": "10406", "lines": [{"spans": [{"text": "· 만료일· 연장신청일"}]}]},
            {"type": 0, "_pageNumber": 46, "_pageCode": "10406", "lines": [{"spans": [{"text": "기산일"}]}]},
            {"type": 0, "_pageNumber": 46, "_pageCode": "10406", "lines": [{"spans": [{"text": "만료일"}]}]},
            {"type": 0, "_pageNumber": 46, "_pageCode": "10406", "lines": [{"spans": [{"text": "기간연장 기산일"}]}]},
            {
                "type": 0,
                "_pageNumber": 46,
                "_pageCode": "10406",
                "lines": [{"spans": [{"text": "2.2.5 절차에 관한 기간이 아닌 상표권의 존속기간 등은 기간의 말일이 공휴일이라도 그 다음 날까지 연장되지 아니한다."}]}],
            },
        ]

        html = blocks_to_html(blocks)

        self.assertIn('<figure class="reader-image">', html)
        self.assertIn('<figcaption>《기간 만료일이 공휴일인 경우 기간연장 기산일》</figcaption>', html)
        self.assertIn('src="generated/images/7f0f56d996ca.png"', html)
        self.assertLess(html.index("앞 설명 문단"), html.index('generated/images/7f0f56d996ca.png'))
        self.assertLess(html.index('generated/images/7f0f56d996ca.png'), html.index("2.2.5 절차에 관한 기간이 아닌"))
        self.assertEqual(
            blocks_to_text(blocks),
            "앞 설명 문단\n\n《기간 만료일이 공휴일인 경우 기간연장 기산일》\n\n7.20\n\n9.19(수)\n\n9.20(목)\n\n9.24(월)\n\n10.19(목)\n\n7.19\n\n지정 2개월\n\n연장기간 1개월\n\n연장기간 만료일\n\n통지서송달일\n\n· 만료일· 연장신청일\n\n기산일\n\n만료일\n\n기간연장 기산일\n\n2.2.5 절차에 관한 기간이 아닌 상표권의 존속기간 등은 기간의 말일이 공휴일이라도 그 다음 날까지 연장되지 아니한다.",
        )

    def test_blocks_to_html_prepends_synthetic_procedure_figures_for_allowlisted_sections(self) -> None:
        cases = [
            {
                "section_title": "1. 재심사의 청구 요건",
                "paragraphs": [
                    "거절결정등본 송달일부터 3개월 이내에 재심사를 청구해야 한다.",
                    "재심사의 청구와 함께 의견서나 보정서를 제출할 수 있다.",
                ],
                "expected": ["<figcaption>1. 재심사의 청구 요건</figcaption>", "거절결정등본 송달일부터 3개월 이내에 재심사를 청구해야 한다.", "거절결정이 있는 상표등록출원이어야 하고 거절결정불복심판 청구가 없어야 한다."],
            },
            {
                "section_title": "2. 보정 승인·각하 판단",
                "paragraphs": [
                    "심사관은 보정각하 여부를 먼저 판단한다.",
                    "보정을 승인한 후 그 내용에 따라 심사한다.",
                ],
                "expected": ["<figcaption>2. 보정 승인·각하 판단</figcaption>", "심사관은 보정각하 여부를 먼저 판단한다.", "거절결정, 출원공고 후 등록결정, 또는 새로운 거절이유 통지로 이어질 수 있다."],
            },
            {
                "section_title": "2. 절차보정(법§39)",
                "paragraphs": [
                    "절차상 방식 흠결이 있는 경우 절차보정 대상이 된다.",
                    "적합하게 보정되면 절차가 계속된다.",
                ],
                "expected": ["<figcaption>2. 절차보정(법§39)</figcaption>", "심사관은 기간을 정하여 보정을 명하거나 출원인이 자진보정할 수 있다.", "적합하게 보정되면 절차가 계속되고 미보정이면 절차를 무효로 할 수 있다."],
            },
            {
                "section_title": "3. 실체보정(법§40 내지 §41)",
                "paragraphs": [
                    "각 절차 단계에서 법이 정한 기간 안에만 실체보정을 할 수 있다.",
                    "적법한 보정은 최초출원일 기준을 유지한다.",
                ],
                "expected": ["<figcaption>3. 실체보정(법§40 내지 §41)</figcaption>", "출원공고 전후, 거절이유통지 후, 거절불복심판 후, 재심사 청구 시 등 단계별로 보정 가능성이 달라진다.", "적법한 보정은 최초출원일 기준을 유지하고 부적법한 보정은 반려되거나 요지변경 판단으로 이어진다."],
            },
            {
                "section_title": "1. 직권보정의 시기··········",
                "paragraphs": [
                    "원칙적으로 출원공고결정을 할 때에 직권보정이 가능하다.",
                    "심사관은 직권보정하면서 출원공고할 수 있다.",
                ],
                "expected": ["<figcaption>1. 직권보정의 시기</figcaption>", "출원공고결정을 할 때 직권보정이 가능하다.", "심사관은 직권보정하면서 출원공고할 수 있다."],
            },
            {
                "section_title": "3. 직권보정사항의 통보 및 의견제출기회 부여··········",
                "paragraphs": [
                    "출원인은 출원공고기간 내에 의견서를 제출할 수 있다.",
                    "의견서가 제출되면 해당 직권보정 사항은 처음부터 없었던 것으로 본다.",
                ],
                "expected": ["<figcaption>3. 직권보정사항의 통보 및 의견제출기회 부여</figcaption>", "직권보정 사항을 결정서와 상표공보에 기재해 출원인에게 알린다.", "심사관은 직권보정 전 내용으로 재심사한다."],
            },
            {
                "section_title": "4. 잘못된 직권보정의 무효",
                "paragraphs": [
                    "심사관의 직권보정이 명백히 잘못된 경우다.",
                ],
                "expected": ["<figcaption>4. 잘못된 직권보정의 무효</figcaption>", "직권보정이 명백히 잘못된 경우다.", "그 직권보정은 처음부터 없었던 것으로 본다."],
            },
            {
                "section_title": "1. 분할출원의 요건심사",
                "paragraphs": [
                    "출원의 분할은 현재 출원 계속중인 출원이어야 한다.",
                    "원상표등록출원서의 상표와 분할출원서의 상표가 동일하여야 한다.",
                ],
                "expected": ["<figcaption>1. 분할출원의 요건심사</figcaption>", "현재 출원 계속 중이어야 하고 실체보정 가능기간 이내에 분할해야 한다.", "원출원 지정상품 범위 내에서만 분할할 수 있다."],
            },
            {
                "section_title": "2. 부적법한 분할출원에 대한 처리",
                "paragraphs": [
                    "보정기간이 지난 뒤 제출된 분할출원은 반려한다.",
                    "미해소 시 분할출원일 기준 신규출원으로 심사한다.",
                ],
                "expected": ["<figcaption>2. 부적법한 분할출원에 대한 처리</figcaption>", "실질적 확장, 삭제 미보정, 출원인 또는 상표견본 불일치 등이 있으면 불인정예고통지를 한다.", "원출원 거절결정 확정 시점에 따라 최초출원일 인정 여부가 달라질 수 있다."],
            },
            {
                "section_title": "3. 분할출원의 효과",
                "paragraphs": [
                    "적법한 분할출원은 최초출원일에 출원한 것으로 본다.",
                    "분할출원은 원출원과 별개 출원이다.",
                ],
                "expected": ["<figcaption>3. 분할출원의 효과</figcaption>", "적법한 분할출원은 최초출원일에 출원한 것으로 본다.", "분할출원은 원출원과 별개 출원이므로 처음부터 다시 심사한다."],
            },
            {
                "section_title": "1. 변경출원의 요건심사",
                "paragraphs": [
                    "최초출원의 등록여부결정 또는 심결이 확정되기 전에 변경해야 한다.",
                    "최초출원과 변경출원의 목적물이 동일해야 한다.",
                ],
                "expected": ["<figcaption>1. 변경출원의 요건심사</figcaption>", "기초 등록상표에 무효·취소 심판이 청구되었거나 소멸된 경우에는 변경할 수 없다.", "공동출원은 공유자 전원이 공동으로 해야 한다."],
            },
            {
                "section_title": "3. 변경출원의 효과",
                "paragraphs": [
                    "변경출원은 최초출원일에 출원한 것으로 본다.",
                    "최초출원은 취하된 것으로 본다.",
                ],
                "expected": ["<figcaption>3. 변경출원의 효과</figcaption>", "우선권 주장과 출원시 특례는 변경출원일 기준으로 적용한다.", "변경출원이 있으면 최초출원은 취하된 것으로 본다."],
            },
            {
                "section_title": "4. 부적법한 변경출원에 대한 처리",
                "paragraphs": [
                    "확정 이후의 변경출원은 반려한다.",
                    "변경 전 최초출원으로 심사를 계속 진행한다.",
                ],
                "expected": ["<figcaption>4. 부적법한 변경출원에 대한 처리</figcaption>", "실질적 확장, 출원인 불일치, 상표견본 불일치 등이 있으면 변경출원불인정예고통지를 한다.", "분할출원과 달리 변경 전 최초출원으로 심사를 계속 진행한다."],
            },
            {
                "section_title": "1. 요지변경이 아닌 경우",
                "paragraphs": [
                    "지정상품 범위의 감축은 요지변경이 아니다.",
                    "명백한 오기의 정정은 요지변경이 아니다.",
                ],
                "expected": ["<figcaption>1. 요지변경이 아닌 경우</figcaption>", "불명료한 기재를 석명하는 보정은 요지변경이 아니다.", "상표의 부기적 부분을 삭제하는 보정은 요지변경이 아니다."],
            },
            {
                "section_title": "4. 요지변경인 경우의 처리",
                "paragraphs": [
                    "보정이 요지변경에 해당하면 보정각하결정을 하여야 한다.",
                    "보정각하결정에 대해서는 3개월 이내에 불복심판을 청구할 수 있다.",
                ],
                "expected": ["<figcaption>4. 요지변경인 경우의 처리</figcaption>", "불복 가능 기간이 지나거나 심판 결과가 확정될 때까지 심사나 심판을 중지한다.", "불복이 불가능한 경우에는 해당 절차를 계속 진행한다."],
            },
            {
                "section_title": "5. 요지변경임이 간과된 등록상표의 효력",
                "paragraphs": [
                    "송달 전에 간과되었으면 보정서를 제출한 때에 출원한 것으로 본다.",
                    "송달 후에 간과되었으면 보정 전의 상표출원으로 상표권이 설정등록된 것으로 본다.",
                ],
                "expected": ["<figcaption>5. 요지변경임이 간과된 등록상표의 효력</figcaption>", "요지변경 보정이 간과된 시점이 출원공고결정등본 송달 전인지 후인지가 중요하다.", "사후 효력 판단은 간과된 요지변경 전후 중 어느 출원을 기준으로 볼지에 따라 갈린다."],
            },
        ]

        for case in cases:
            with self.subTest(section_title=case["section_title"]):
                blocks = [
                    {
                        "type": 0,
                        "_pageNumber": 144,
                        "_pageCode": "30302",
                        "lines": [{"spans": [{"text": paragraph}]}],
                    }
                    for paragraph in case["paragraphs"]
                ]

                html = blocks_to_html(blocks, section_title=case["section_title"])

                self.assertIn("reader-synthetic-figure", html)
                for expected_text in case["expected"]:
                    self.assertIn(expected_text, html)
                self.assertLess(html.index("reader-synthetic-figure"), html.index(case["paragraphs"][0]))
                self.assertEqual(blocks_to_text(blocks), "\n\n".join(case["paragraphs"]))

    def test_blocks_to_html_does_not_prepend_synthetic_procedure_figure_for_normal_section(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 200,
                "_pageCode": "40101",
                "lines": [{"spans": [{"text": "이 절은 일반 설명 문단이다."}]}],
            },
            {
                "type": 0,
                "_pageNumber": 200,
                "_pageCode": "40101",
                "lines": [{"spans": [{"text": "다음 문단도 일반 본문으로 이어진다."}]}],
            },
        ]

        html = blocks_to_html(blocks, section_title="1. 정보제공의 요건")

        self.assertNotIn("reader-synthetic-figure", html)
        self.assertIn("이 절은 일반 설명 문단이다.", html)
        self.assertIn("다음 문단도 일반 본문으로 이어진다.", html)
        self.assertEqual(blocks_to_text(blocks), "이 절은 일반 설명 문단이다.\n\n다음 문단도 일반 본문으로 이어진다.")

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

    def test_blocks_to_text_keeps_wide_circled_digit_item_separate_from_previous_numeric_item(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 35,
                "_pageCode": "10301",
                "bbox": (78.54, 516.43, 343.22, 528.52),
                "lines": [
                    {
                        "bbox": (78.54, 516.43, 343.22, 528.52),
                        "spans": [{"text": "6. 대리인 또는 복대리인이 그 직을 사임하려는 경우"}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 35,
                "_pageCode": "10301",
                "bbox": (78.54, 533.84, 459.98, 545.92),
                "lines": [
                    {
                        "bbox": (78.54, 533.84, 459.98, 545.92),
                        "spans": [
                            {
                                "text": "④ 대리인이 「변리사법」 제6조의3에 따른 특허법인 또는 같은 법 제6조의12에 따른 특허법인(유한)의 구성원 또는 소속 변리사가 되면 다음 각 호의 어느 하나에 해당하는 행위를 할 수 있다."
                            }
                        ],
                    }
                ],
            },
        ]

        text = blocks_to_text(blocks)

        self.assertEqual(
            text,
            "6. 대리인 또는 복대리인이 그 직을 사임하려는 경우\n\n④ 대리인이 「변리사법」 제6조의3에 따른 특허법인 또는 같은 법 제6조의12에 따른 특허법인(유한)의 구성원 또는 소속 변리사가 되면 다음 각 호의 어느 하나에 해당하는 행위를 할 수 있다.",
        )

    def test_blocks_to_text_keeps_wide_numbered_items_separate_after_circled_digit_item(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 36,
                "_pageCode": "10301",
                "bbox": (78.54, 111.98, 459.97, 124.06),
                "lines": [
                    {
                        "bbox": (78.54, 111.98, 459.97, 124.06),
                        "spans": [
                            {
                                "text": "⑤ 다음 각 호의 어느 하나에 해당하는 경우에 둘 이상의 사건에 대하여 상표에 관한 절차를 밟는 자가 같고, 대리인 또는 복대리인이 같은 경우에는 신고서를 하나만 작성하여 제출할 수 있다."
                            }
                        ],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 36,
                "_pageCode": "10301",
                "bbox": (78.54, 168.14, 436.40, 180.22),
                "lines": [
                    {
                        "bbox": (78.54, 168.14, 436.40, 180.22),
                        "spans": [{"text": "1. 상표에 관한 절차를 밟는 자가 대리인을 선임하거나 해임하려는 경우"}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 36,
                "_pageCode": "10301",
                "bbox": (78.54, 186.86, 342.50, 198.94),
                "lines": [
                    {
                        "bbox": (78.54, 186.86, 342.50, 198.94),
                        "spans": [{"text": "2. 대리인이 복대리인을 선임하거나 해임하려는 경우"}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 36,
                "_pageCode": "10301",
                "bbox": (78.54, 205.58, 301.40, 217.66),
                "lines": [
                    {
                        "bbox": (78.54, 205.58, 301.40, 217.66),
                        "spans": [{"text": "3. 대리인 또는 복대리인이 사임하려는 경우"}],
                    }
                ],
            },
        ]

        text = blocks_to_text(blocks)

        self.assertEqual(
            text,
            "⑤ 다음 각 호의 어느 하나에 해당하는 경우에 둘 이상의 사건에 대하여 상표에 관한 절차를 밟는 자가 같고, 대리인 또는 복대리인이 같은 경우에는 신고서를 하나만 작성하여 제출할 수 있다.\n\n1. 상표에 관한 절차를 밟는 자가 대리인을 선임하거나 해임하려는 경우\n\n2. 대리인이 복대리인을 선임하거나 해임하려는 경우\n\n3. 대리인 또는 복대리인이 사임하려는 경우",
        )

    def test_blocks_to_text_keeps_wide_korean_letter_items_separate(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 77,
                "_pageCode": "20101",
                "bbox": (76.20, 365.60, 345.50, 377.67),
                "lines": [
                    {
                        "bbox": (76.20, 365.60, 345.50, 377.67),
                        "spans": [{"text": "    가. 상품 또는 상품의 포장에 상표를 표시하는 행위"}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 77,
                "_pageCode": "20101",
                "bbox": (76.20, 383.96, 462.26, 396.03),
                "lines": [
                    {
                        "bbox": (76.20, 383.96, 462.26, 396.03),
                        "spans": [{"text": "    나. 상품 또는 상품의 포장에 상표를 표시한 것을 양도 또는 인도하거나 양도 또는 인도할 목적으로 전시·수출 또는 수입하는 행위"}],
                    }
                ],
            },
        ]

        text = blocks_to_text(blocks)
        html = blocks_to_html(blocks)

        self.assertEqual(
            text,
            "가. 상품 또는 상품의 포장에 상표를 표시하는 행위\n\n나. 상품 또는 상품의 포장에 상표를 표시한 것을 양도 또는 인도하거나 양도 또는 인도할 목적으로 전시·수출 또는 수입하는 행위",
        )
        self.assertIn("<p>가. 상품 또는 상품의 포장에 상표를 표시하는 행위</p>\n<p>나. 상품 또는 상품의 포장에 상표를 표시한 것을 양도 또는 인도하거나 양도 또는 인도할 목적으로 전시·수출 또는 수입하는 행위</p>", html)

    def test_blocks_to_text_keeps_legal_subitem_number_separate(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 127,
                "_pageCode": "30101",
                "bbox": (75.18, 259.82, 403.40, 271.90),
                "lines": [
                    {
                        "bbox": (75.18, 259.82, 403.40, 271.90),
                        "spans": [{"text": "1. 제55조의2에 따른 재심사를 청구하는 경우: 재심사의 청구기간"}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 127,
                "_pageCode": "30101",
                "bbox": (75.18, 278.54, 429.44, 290.62),
                "lines": [
                    {
                        "bbox": (75.18, 278.54, 429.44, 290.62),
                        "spans": [{"text": "1의2. 제57조에 따른 출원공고의 결정이 있는 경우: 출원공고의 때까지"}],
                    }
                ],
            },
        ]

        text = blocks_to_text(blocks)

        self.assertEqual(
            text,
            "1. 제55조의2에 따른 재심사를 청구하는 경우: 재심사의 청구기간\n\n1의2. 제57조에 따른 출원공고의 결정이 있는 경우: 출원공고의 때까지",
        )

    def test_blocks_to_text_preserves_inline_circled_digit_enumeration_in_single_line(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 78,
                "_pageCode": "20101",
                "bbox": (80.22, 168.44, 478.20, 217.48),
                "lines": [
                    {
                        "bbox": (80.22, 168.44, 478.16, 180.52),
                        "spans": [{"text": "사용하는 표장(標章)을 말한다(법§2①1). 상표로 사용되는 『표장』은 크게 ①기호, 문자, 숫자, 도형, 도안, 입체적 형상, 이들의 결합 또는 이들에 색채를 결합한 것, ②단일의 색채, 색채의 조합, 홀로그램, 연속된 동작 등 시각적으로 인식할 수 있는 것, ③소리ㆍ냄새 등 시각적으로 인식할 수 없는 것으로 구분된다."}],
                    }
                ],
            }
        ]

        text = blocks_to_text(blocks)

        self.assertEqual(
            text,
            "사용하는 표장(標章)을 말한다(법§2①1). 상표로 사용되는 『표장』은 크게 ①기호, 문자, 숫자, 도형, 도안, 입체적 형상, 이들의 결합 또는 이들에 색채를 결합한 것, ②단일의 색채, 색채의 조합, 홀로그램, 연속된 동작 등 시각적으로 인식할 수 있는 것, ③소리ㆍ냄새 등 시각적으로 인식할 수 없는 것으로 구분된다.",
        )

    def test_blocks_to_text_merges_hanging_indent_word_split_lines(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 27,
                "_pageCode": "10201",
                "bbox": (78.54, 612.26, 459.97, 624.34),
                "lines": [
                    {
                        "bbox": (78.54, 612.26, 459.97, 624.34),
                        "spans": [
                            {
                                "text": "1. 그 외국인이 속하는 국가에서 대한민국 국민에 대하여 그 국민과 같은 조"
                            }
                        ],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 27,
                "_pageCode": "10201",
                "bbox": (105.48, 629.84, 369.98, 641.92),
                "lines": [
                    {
                        "bbox": (105.48, 629.84, 369.98, 641.92),
                        "spans": [{"text": "건으로 상표권 또는 상표에 관한 권리를 인정하는 경우"}],
                    }
                ],
            },
        ]

        text = blocks_to_text(blocks)

        self.assertEqual(
            text,
            "1. 그 외국인이 속하는 국가에서 대한민국 국민에 대하여 그 국민과 같은 조건으로 상표권 또는 상표에 관한 권리를 인정하는 경우",
        )

    def test_blocks_to_text_merges_hanging_indent_body_continuation(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 44,
                "_pageCode": "10407",
                "bbox": (63.78, 100.00, 444.26, 112.08),
                "lines": [
                    {
                        "bbox": (63.78, 100.00, 444.26, 112.08),
                        "spans": [
                            {
                                "text": "3. 상표등록출원인의 성명과 주소(법인인 경우에는 그 명칭과 영업소의 소"
                            }
                        ],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 44,
                "_pageCode": "10407",
                "bbox": (90.96, 118.12, 126.96, 130.20),
                "lines": [
                    {
                        "bbox": (90.96, 118.12, 126.96, 130.20),
                        "spans": [{"text": "재지)"}],
                    }
                ],
            },
        ]

        text = blocks_to_text(blocks)

        self.assertEqual(
            text,
            "3. 상표등록출원인의 성명과 주소(법인인 경우에는 그 명칭과 영업소의 소재지)",
        )

    def test_blocks_to_text_merges_wider_hanging_indent_continuation(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 37,
                "_pageCode": "10304",
                "bbox": (63.78, 524.90, 474.78, 536.98),
                "lines": [
                    {
                        "bbox": (63.78, 524.90, 474.78, 536.98),
                        "spans": [{"text": "(ⅰ) 『친권자』란 미성년자에 대하여 친권을 행사하는 부 또는 모를 말하며, 미성"}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 37,
                "_pageCode": "10304",
                "bbox": (113.64, 543.62, 313.57, 555.70),
                "lines": [
                    {
                        "bbox": (113.64, 543.62, 313.57, 555.70),
                        "spans": [{"text": "년자의 법정대리인이 된다(민법 제911조)."}],
                    }
                ],
            },
        ]

        text = blocks_to_text(blocks)

        self.assertEqual(text, "(ⅰ) 『친권자』란 미성년자에 대하여 친권을 행사하는 부 또는 모를 말하며, 미성년자의 법정대리인이 된다(민법 제911조).")

    def test_blocks_to_text_merges_wide_hanging_indent_note_continuation(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 209,
                "_pageCode": "40903",
                "bbox": (63.77, 483.25, 474.74, 495.33),
                "lines": [
                    {
                        "bbox": (63.77, 483.25, 474.74, 495.33),
                        "spans": [{"text": "      (참고) 사용에 의한 식별력은 원래 식별력이 없는 표장에 대세적인 권리를 부"}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 209,
                "_pageCode": "40903",
                "bbox": (130.38, 501.31, 478.24, 513.39),
                "lines": [
                    {
                        "bbox": (130.38, 501.31, 478.24, 513.39),
                        "spans": [{"text": "여하는 것이므로 과거에는 그 기준을 엄격하게 해석·적용하여야 한다고 "}],
                    }
                ],
            },
        ]

        text = blocks_to_text(blocks)

        self.assertEqual(
            text,
            "(참고) 사용에 의한 식별력은 원래 식별력이 없는 표장에 대세적인 권리를 부여하는 것이므로 과거에는 그 기준을 엄격하게 해석·적용하여야 한다고",
        )

    def test_blocks_to_text_merges_sentence_continuation_starting_with_da(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 533,
                "_pageCode": "100101",
                "bbox": (80.22, 216.56, 474.75, 228.64),
                "lines": [
                    {
                        "bbox": (80.22, 216.56, 474.75, 228.64),
                        "spans": [{"text": "심사관이나 지식재산처장이 직권으로 이를 취소하거나 변경하지 못하도록 하고 있"}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 533,
                "_pageCode": "100101",
                "bbox": (80.22, 236.36, 474.74, 248.44),
                "lines": [
                    {
                        "bbox": (80.22, 236.36, 474.74, 248.44),
                        "spans": [{"text": "다. 다만, 절차상 중대하고 명백한 하자가 있는 결정처분은 법률상 효력이 없는 처"}],
                    }
                ],
            },
        ]

        text = blocks_to_text(blocks)

        self.assertEqual(
            text,
            "심사관이나 지식재산처장이 직권으로 이를 취소하거나 변경하지 못하도록 하고 있다. 다만, 절차상 중대하고 명백한 하자가 있는 결정처분은 법률상 효력이 없는 처",
        )

    def test_blocks_to_text_merges_large_indent_word_fragment_continuation(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 533,
                "_pageCode": "100101",
                "bbox": (64.80, 550.34, 473.71, 562.42),
                "lines": [
                    {
                        "bbox": (64.80, 550.34, 473.71, 562.42),
                        "spans": [{"text": "(해당 예시) 행위능력이 없는 자가 직접 출원한 상표등록출원에 대하여 등"}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 533,
                "_pageCode": "100101",
                "bbox": (174.24, 570.14, 257.18, 582.22),
                "lines": [
                    {
                        "bbox": (174.24, 570.14, 257.18, 582.22),
                        "spans": [{"text": "록결정을 한 경우"}],
                    }
                ],
            },
        ]

        text = blocks_to_text(blocks)

        self.assertEqual(text, "(해당 예시) 행위능력이 없는 자가 직접 출원한 상표등록출원에 대하여 등록결정을 한 경우")

    def test_blocks_to_text_normalizes_broken_eui_hayeo_spacing(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 525,
                "_pageCode": "90801",
                "bbox": (76.20, 221.60, 463.35, 233.68),
                "lines": [
                    {
                        "bbox": (76.20, 221.60, 463.35, 233.68),
                        "spans": [{"text": "(1) 국제사무국에서의 표장의 등록은 10년간 유효하고, 제7조에서 명시하는 요"}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 525,
                "_pageCode": "90801",
                "bbox": (96.06, 239.72, 250.26, 251.80),
                "lines": [
                    {
                        "bbox": (96.06, 239.72, 250.26, 251.80),
                        "spans": [{"text": "건에의 하여 갱신을 할 수 있다."}],
                    }
                ],
            },
        ]

        text = blocks_to_text(blocks)

        self.assertEqual(
            text,
            "(1) 국제사무국에서의 표장의 등록은 10년간 유효하고, 제7조에서 명시하는 요건에 의하여 갱신을 할 수 있다.",
        )

    def test_blocks_to_text_merges_hanging_indent_with_larger_line_gap(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 151,
                "_pageCode": "30405",
                "bbox": (63.78, 211.88, 474.73, 223.96),
                "lines": [
                    {
                        "bbox": (63.78, 211.88, 474.73, 223.96),
                        "spans": [{"text": "5.1.1 담당심사관은 분할신청에 대한 적부를 판단하여 하자가 있는 경우 국제상표등"}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 151,
                "_pageCode": "30405",
                "bbox": (95.52, 232.82, 474.75, 244.90),
                "lines": [
                    {
                        "bbox": (95.52, 232.82, 474.75, 244.90),
                        "spans": [{"text": "록출원인(이하 “출원인”이라 한다)에게 2개월의 보정기간을 정하여 ‘국제상표분"}],
                    }
                ],
            },
        ]

        text = blocks_to_text(blocks)

        self.assertEqual(
            text,
            "5.1.1 담당심사관은 분할신청에 대한 적부를 판단하여 하자가 있는 경우 국제상표등록출원인(이하 “출원인”이라 한다)에게 2개월의 보정기간을 정하여 ‘국제상표분",
        )

    def test_blocks_to_text_keeps_large_indent_paragraph_starter_separate(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 200,
                "_pageCode": "99901",
                "bbox": (63.78, 100.00, 474.78, 112.08),
                "lines": [
                    {
                        "bbox": (63.78, 100.00, 474.78, 112.08),
                        "spans": [{"text": "선행 문단의 마지막 줄이 아직 끝나지 않은 것처럼 보여도"}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 200,
                "_pageCode": "99901",
                "bbox": (160.00, 119.20, 300.00, 131.28),
                "lines": [
                    {
                        "bbox": (160.00, 119.20, 300.00, 131.28),
                        "spans": [{"text": "다만, 이 문장은 새 문단이다."}],
                    }
                ],
            },
        ]

        text = blocks_to_text(blocks)

        self.assertEqual(text, "선행 문단의 마지막 줄이 아직 끝나지 않은 것처럼 보여도\n\n다만, 이 문장은 새 문단이다.")

    def test_blocks_to_text_keeps_medium_indent_paragraph_starter_separate(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 200,
                "_pageCode": "99901",
                "bbox": (63.78, 100.00, 474.78, 112.08),
                "lines": [
                    {
                        "bbox": (63.78, 100.00, 474.78, 112.08),
                        "spans": [{"text": "선행 문단의 마지막 줄이 아직 끝나지 않은 것처럼 보여도"}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 200,
                "_pageCode": "99901",
                "bbox": (103.78, 119.20, 300.00, 131.28),
                "lines": [
                    {
                        "bbox": (103.78, 119.20, 300.00, 131.28),
                        "spans": [{"text": "다만, 이 문장은 새 문단이다."}],
                    }
                ],
            },
        ]

        text = blocks_to_text(blocks)

        self.assertEqual(text, "선행 문단의 마지막 줄이 아직 끝나지 않은 것처럼 보여도\n\n다만, 이 문장은 새 문단이다.")

    def test_blocks_to_text_keeps_large_indent_bullet_line_separate(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 200,
                "_pageCode": "99901",
                "bbox": (63.78, 100.00, 474.78, 112.08),
                "lines": [
                    {
                        "bbox": (63.78, 100.00, 474.78, 112.08),
                        "spans": [{"text": "앞 문장은 참고자료를 충분히 증명하는"}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 200,
                "_pageCode": "99901",
                "bbox": (160.00, 119.20, 280.00, 131.28),
                "lines": [
                    {
                        "bbox": (160.00, 119.20, 280.00, 131.28),
                        "spans": [{"text": "※ 추가 서류"}],
                    }
                ],
            },
        ]

        text = blocks_to_text(blocks)

        self.assertEqual(text, "앞 문장은 참고자료를 충분히 증명하는\n\n※ 추가 서류")

    def test_blocks_to_text_keeps_indented_korean_letter_heading_as_new_paragraph(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 44,
                "_pageCode": "10407",
                "bbox": (63.78, 100.00, 444.26, 112.08),
                "lines": [
                    {
                        "bbox": (63.78, 100.00, 444.26, 112.08),
                        "spans": [{"text": "이 문단은 아직 끝나지 않은 것처럼 보여도 다음 제목과는 합쳐지면 안 된다"}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 44,
                "_pageCode": "10407",
                "bbox": (113.78, 118.08, 203.78, 130.16),
                "lines": [
                    {
                        "bbox": (113.78, 118.08, 203.78, 130.16),
                        "spans": [{"text": "가. 다음 요건"}],
                    }
                ],
            },
        ]

        text = blocks_to_text(blocks)

        self.assertEqual(text, "이 문단은 아직 끝나지 않은 것처럼 보여도 다음 제목과는 합쳐지면 안 된다\n\n가. 다음 요건")

    def test_blocks_to_text_keeps_short_label_rows_separate(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 45,
                "_pageCode": "10408",
                "bbox": (63.78, 100.00, 183.78, 112.08),
                "lines": [
                    {
                        "bbox": (63.78, 100.00, 183.78, 112.08),
                        "spans": [{"text": "지정기간 2개월"}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 45,
                "_pageCode": "10408",
                "bbox": (91.78, 118.08, 181.78, 130.16),
                "lines": [
                    {
                        "bbox": (91.78, 118.08, 181.78, 130.16),
                        "spans": [{"text": "통지서송달일"}],
                    }
                ],
            },
        ]

        text = blocks_to_text(blocks)

        self.assertEqual(text, "지정기간 2개월\n\n통지서송달일")

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

    def test_slice_entry_blocks_keeps_cross_page_continuation_before_next_title(self) -> None:
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
                "_pageNumber": 28,
                "bbox": (10, 80, 160, 100),
                "lines": [{"spans": [{"text": "1. 권리능력"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 29,
                "bbox": (10, 100, 420, 120),
                "lines": [{"spans": [{"text": "- 지정상품 : 전부※ 다만, ㅇㅇ협회가 비법인단체로서 권리능력이 없어 상표등록을 받을 수 없는 경우라면 ➀ 비법인단체라는 점과 ➁ 출원인이 등록받더라도 비법인단체와 출처의 오인·혼동의"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 30,
                "bbox": (10, 100, 260, 120),
                "lines": [{"spans": [{"text": "우려가 없다는 점이 인정될 경우 등록이 가능합니다."}]}],
            },
            {
                "type": 0,
                "_pageNumber": 30,
                "bbox": (10, 130, 220, 150),
                "lines": [{"spans": [{"text": "1.6 외국인의 권리능력"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 30,
                "bbox": (10, 220, 160, 240),
                "lines": [{"spans": [{"text": "2. 행위능력"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 30,
                "bbox": (10, 250, 220, 270),
                "lines": [{"spans": [{"text": "2.1 무능력자의 행위능력"}]}],
            },
        ]

        sliced = slice_entry_blocks(blocks, chapter_entries[0], chapter_entries[1:])
        text = blocks_to_text(sliced)

        self.assertIn("우려가 없다는 점이 인정될 경우 등록이 가능합니다.", text)
        self.assertIn("1.6 외국인의 권리능력", text)
        self.assertNotIn("2.1 무능력자의 행위능력", text)

    def test_page_has_meaningful_leading_content_before_title_detects_pre_heading_spillover(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageCode": "10305",
                "_pageNumber": 37,
                "bbox": (420, 60, 470, 80),
                "lines": [{"spans": [{"text": "제3장 대리인"}]}],
            },
            {
                "type": 0,
                "_pageCode": "10305",
                "_pageNumber": 37,
                "bbox": (80, 120, 420, 140),
                "lines": [{"spans": [{"text": "제4조(포괄위임 원용의 제한)"}]}],
            },
            {
                "type": 0,
                "_pageCode": "10305",
                "_pageNumber": 37,
                "bbox": (64, 430, 160, 450),
                "lines": [{"spans": [{"text": "1. 대리인의 구분"}]}],
            },
        ]

        self.assertTrue(
            page_has_meaningful_leading_content_before_title(
                blocks,
                "1. 대리인의 구분",
                part_title="제1부 총 칙",
                chapter_title="제3장 대리인",
            )
        )

    def test_extend_overview_end_page_for_leading_content_includes_first_child_page(self) -> None:
        overview_entry = {
            "entryType": "overview",
            "pageEnd": 36,
            "partTitle": "제1부 총 칙",
            "chapterTitle": "제3장 대리인",
        }
        following_entry = {
            "sectionTitle": "1. 대리인의 구분",
            "pageStart": 37,
        }
        page_blocks = {
            37: [
                {
                    "type": 0,
                    "_pageCode": "10305",
                    "_pageNumber": 37,
                    "bbox": (420, 60, 470, 80),
                    "lines": [{"spans": [{"text": "제3장 대리인"}]}],
                },
                {
                    "type": 0,
                    "_pageCode": "10305",
                    "_pageNumber": 37,
                    "bbox": (80, 120, 420, 140),
                    "lines": [{"spans": [{"text": "제4조(포괄위임 원용의 제한)"}]}],
                },
                {
                    "type": 0,
                    "_pageCode": "10305",
                    "_pageNumber": 37,
                    "bbox": (64, 430, 160, 450),
                    "lines": [{"spans": [{"text": "1. 대리인의 구분"}]}],
                },
            ]
        }

        self.assertEqual(
            extend_overview_end_page_for_leading_content(
                overview_entry,
                following_entry,
                36,
                page_blocks,
            ),
            37,
        )

    def test_blocks_to_text_merges_cross_page_continuation_after_header_stripping(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 29,
                "_pageCode": "10202",
                "bbox": (73.31, 619.69, 471.58, 631.77),
                "lines": [
                    {
                        "bbox": (73.31, 619.69, 471.58, 631.77),
                        "spans": [{"text": "※ 다만, ㅇㅇ협회가 비법인단체로서 권리능력이 없어 상표등록을 받을 수 없는 경우라면 "}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 29,
                "_pageCode": "10202",
                "bbox": (89.93, 638.31, 471.61, 650.49),
                "lines": [
                    {
                        "bbox": (89.93, 638.31, 471.61, 650.49),
                        "spans": [{"text": "➀ 비법인단체라는 점과 ➁ 출원인이 등록받더라도 비법인단체와 출처의 오인·혼동의 "}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 30,
                "_pageCode": "10203",
                "bbox": (65.76, 60.02, 118.80, 70.01),
                "lines": [{"bbox": (65.76, 60.02, 118.80, 70.01), "spans": [{"text": "제1부  총 칙"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 30,
                "_pageCode": "10203",
                "bbox": (89.93, 116.14, 468.34, 128.31),
                "lines": [
                    {
                        "bbox": (89.93, 116.14, 468.34, 128.31),
                        "spans": [{"text": "우려가 없다는 점이 인정될 경우 등록이 가능합니다. 가령, ➀은 소득세법에 따른 ‘고"}],
                    }
                ],
            },
        ]

        text = blocks_to_text(blocks, part_title="제1부 총 칙", chapter_title="제2장 권리능력 및 행위능력")

        self.assertIn("오인·혼동의 우려가 없다는 점이 인정될 경우", text)
        self.assertNotIn("오인·혼동의\n\n우려가", text)

    def test_blocks_to_text_keeps_cross_page_numbered_heading_separate(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 29,
                "_pageCode": "10202",
                "bbox": (89.93, 638.31, 471.61, 650.49),
                "lines": [
                    {
                        "bbox": (89.93, 638.31, 471.61, 650.49),
                        "spans": [{"text": "우려가 없다는 점이 인정될 경우 등록이 가능합니다."}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 30,
                "_pageCode": "10203",
                "bbox": (65.76, 60.02, 118.80, 70.01),
                "lines": [{"bbox": (65.76, 60.02, 118.80, 70.01), "spans": [{"text": "제1부  총 칙"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 30,
                "_pageCode": "10203",
                "bbox": (63.77, 217.03, 167.23, 229.11),
                "lines": [{"bbox": (63.77, 217.03, 167.23, 229.11), "spans": [{"text": "1.6 외국인의 권리능력"}]}],
            },
        ]

        text = blocks_to_text(blocks, part_title="제1부 총 칙", chapter_title="제2장 권리능력 및 행위능력")

        self.assertEqual(text, "우려가 없다는 점이 인정될 경우 등록이 가능합니다.\n\n1.6 외국인의 권리능력")

    def test_blocks_to_text_keeps_cross_page_bullet_separate(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 29,
                "_pageCode": "10202",
                "bbox": (89.93, 638.31, 471.61, 650.49),
                "lines": [
                    {
                        "bbox": (89.93, 638.31, 471.61, 650.49),
                        "spans": [{"text": "우려가 없다는 점이 인정될 경우 등록이 가능합니다."}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 30,
                "_pageCode": "10203",
                "bbox": (65.76, 60.02, 118.80, 70.01),
                "lines": [{"bbox": (65.76, 60.02, 118.80, 70.01), "spans": [{"text": "제1부  총 칙"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 30,
                "_pageCode": "10203",
                "bbox": (89.93, 116.14, 280.00, 128.31),
                "lines": [{"bbox": (89.93, 116.14, 280.00, 128.31), "spans": [{"text": "※ 추가 증빙자료를 제출한다."}]}],
            },
        ]

        text = blocks_to_text(blocks, part_title="제1부 총 칙", chapter_title="제2장 권리능력 및 행위능력")

        self.assertEqual(text, "우려가 없다는 점이 인정될 경우 등록이 가능합니다.\n\n※ 추가 증빙자료를 제출한다.")

    def test_blocks_to_text_keeps_cross_page_short_label_separate(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 29,
                "_pageCode": "10202",
                "bbox": (89.93, 638.31, 471.61, 650.49),
                "lines": [
                    {
                        "bbox": (89.93, 638.31, 471.61, 650.49),
                        "spans": [{"text": "우려가 없다는 점이 인정될 경우 등록이 가능합니다."}],
                    }
                ],
            },
            {
                "type": 0,
                "_pageNumber": 30,
                "_pageCode": "10203",
                "bbox": (65.76, 60.02, 118.80, 70.01),
                "lines": [{"bbox": (65.76, 60.02, 118.80, 70.01), "spans": [{"text": "제1부  총 칙"}]}],
            },
            {
                "type": 0,
                "_pageNumber": 30,
                "_pageCode": "10203",
                "bbox": (89.93, 116.14, 180.00, 128.31),
                "lines": [{"bbox": (89.93, 116.14, 180.00, 128.31), "spans": [{"text": "통지서송달일"}]}],
            },
        ]

        text = blocks_to_text(blocks, part_title="제1부 총 칙", chapter_title="제2장 권리능력 및 행위능력")

        self.assertEqual(text, "우려가 없다는 점이 인정될 경우 등록이 가능합니다.\n\n통지서송달일")

    def test_blocks_to_text_reflows_block_without_line_geometry(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 395,
                "_pageCode": "60501",
                "bbox": (89.75, 304.45, 465.53, 316.53),
                "lines": [
                    {"spans": [{"text": "항을 "}]},
                    {"spans": [{"text": "적은 "}]},
                    {"spans": [{"text": "지정상품의 "}]},
                    {"spans": [{"text": "추가등록출원서를 "}]},
                    {"spans": [{"text": "지식재산처장에게 "}]},
                    {"spans": [{"text": "제출하여야 "}]},
                ],
            },
            {
                "type": 0,
                "_pageNumber": 395,
                "_pageCode": "60501",
                "bbox": (89.75, 322.57, 113.76, 334.65),
                "lines": [{"bbox": (89.75, 322.57, 113.76, 334.65), "spans": [{"text": "한다."}]}],
            },
        ]

        text = blocks_to_text(blocks)

        self.assertEqual(text, "항을 적은 지정상품의 추가등록출원서를 지식재산처장에게 제출하여야 한다.")

    def test_blocks_to_text_keeps_list_rows_separate_in_block_without_line_geometry(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 395,
                "_pageCode": "60501",
                "bbox": (89.75, 304.45, 465.53, 316.53),
                "lines": [
                    {"spans": [{"text": "항을 "}]},
                    {"spans": [{"text": "적은 "}]},
                    {"spans": [{"text": "지정상품의 "}]},
                    {"spans": [{"text": "추가등록출원서를 "}]},
                    {"spans": [{"text": "지식재산처장에게 "}]},
                    {"spans": [{"text": "제출하여야 "}]},
                ],
            },
            {
                "type": 0,
                "_pageNumber": 395,
                "_pageCode": "60501",
                "bbox": (89.75, 322.57, 113.76, 334.65),
                "lines": [{"bbox": (89.75, 322.57, 113.76, 334.65), "spans": [{"text": "한다."}]}],
            },
            {
                "type": 0,
                "_pageNumber": 395,
                "_pageCode": "60501",
                "bbox": (78.77, 340.75, 340.08, 352.83),
                "lines": [{"spans": [{"text": "1. 제36조제1항제1호·제2호·제5호 및 제6호의 사항"}]}],
            },
        ]

        text = blocks_to_text(blocks)

        self.assertEqual(
            text,
            "항을 적은 지정상품의 추가등록출원서를 지식재산처장에게 제출하여야 한다.\n\n1. 제36조제1항제1호·제2호·제5호 및 제6호의 사항",
        )

    def test_blocks_to_text_keeps_paragraph_starter_separate_in_block_without_geometry(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 395,
                "_pageCode": "60501",
                "bbox": (89.75, 304.45, 465.53, 316.53),
                "lines": [
                    {"spans": [{"text": "제출하여야 "}]},
                    {"spans": [{"text": "한다."}]},
                    {"spans": [{"text": "다만, 이 문장은 새 문단이다."}]},
                ],
            }
        ]

        text = blocks_to_text(blocks)

        self.assertEqual(text, "제출하여야 한다.\n\n다만, 이 문장은 새 문단이다.")

    def test_blocks_to_text_keeps_circled_digit_item_separate_in_block_without_geometry(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 35,
                "_pageCode": "10301",
                "bbox": (78.54, 516.43, 459.98, 632.92),
                "lines": [
                    {"spans": [{"text": "6. 대리인 또는 복대리인이 그 직을 사임하려는 경우"}]},
                    {
                        "spans": [
                            {
                                "text": "④ 대리인이 「변리사법」 제6조의3에 따른 특허법인 또는 같은 법 제6조의12에 따른 특허법인(유한)의 구성원 또는 소속 변리사가 되면 다음 각 호의 어느 하나에 해당하는 행위를 할 수 있다."
                            }
                        ]
                    },
                    {"spans": [{"text": "1. 제3항제6호에 따라 대리인 직을 사임하는 행위"}]},
                    {
                        "spans": [
                            {
                                "text": "2. 대리인이 해당 특허법인등의 구성원 또는 소속 변리사가 되기 전에 대리하던 사건에 대하여 해당 특허법인등을 복대리인으로 선임하는 행위"
                            }
                        ]
                    },
                ],
            }
        ]

        text = blocks_to_text(blocks)

        self.assertEqual(
            text,
            "6. 대리인 또는 복대리인이 그 직을 사임하려는 경우\n\n④ 대리인이 「변리사법」 제6조의3에 따른 특허법인 또는 같은 법 제6조의12에 따른 특허법인(유한)의 구성원 또는 소속 변리사가 되면 다음 각 호의 어느 하나에 해당하는 행위를 할 수 있다.\n\n1. 제3항제6호에 따라 대리인 직을 사임하는 행위\n\n2. 대리인이 해당 특허법인등의 구성원 또는 소속 변리사가 되기 전에 대리하던 사건에 대하여 해당 특허법인등을 복대리인으로 선임하는 행위",
        )

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

    def test_extend_end_page_for_next_sibling_allows_one_page_overlap(self) -> None:
        entry = {"entryType": "item", "pageEnd": 29}
        following_entry = {"pageStart": 30}

        extended_end = extend_end_page_for_next_sibling(entry, following_entry, 29)

        self.assertEqual(extended_end, 30)

    def test_extend_end_page_for_next_sibling_respects_structural_caps(self) -> None:
        entry = {"entryType": "item", "pageEnd": 29}
        following_entry = {"pageStart": 30}

        extended_end = extend_end_page_for_next_sibling(entry, following_entry, 28)

        self.assertEqual(extended_end, 28)

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
