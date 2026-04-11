from __future__ import annotations

import importlib
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
build_code_to_page_map = importlib.import_module("pipeline.build_content").build_code_to_page_map
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
