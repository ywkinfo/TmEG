from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from pipeline.common import load_config, load_generated_json
from pipeline.export_notebooklm import clean_title, export_notebooklm, extract_law_refs


class NotebookLMExportTest(unittest.TestCase):
    def test_clean_title_removes_dot_leaders_and_condenses_spaced_syllables(self) -> None:
        self.assertEqual(clean_title("제1부 총 칙········"), "제1부 총칙")
        self.assertEqual(clean_title("제1장 목 적······"), "제1장 목적")

    def test_extract_law_refs_captures_trademark_act_refs_only(self) -> None:
        text = "\n".join(
            [
                "【상표법】",
                "제34조(상표등록을 받을 수 없는 상표)",
                "법 제35조제1항에 따른 심사",
                "법§36①2에 해당",
                "【상훈법】",
                "법 제99조에 따른 훈장",
                "제9조(훈장의 종류)",
            ]
        )

        refs = extract_law_refs(text)

        self.assertIn("제34조", refs)
        self.assertIn("제35조제1항", refs)
        self.assertIn("제36조제1항제2호", refs)
        self.assertNotIn("제9조", refs)
        self.assertNotIn("제99조", refs)

    def test_export_nlm_generates_full_source_set(self) -> None:
        config = load_config()
        search_index = load_generated_json("search-index.json")
        toc = load_generated_json("toc.json")
        image_manifest = load_generated_json("image-manifest.json")

        with tempfile.TemporaryDirectory() as tmp:
            summary = export_notebooklm(
                config=config,
                search_index=search_index,
                toc=toc,
                image_manifest=image_manifest,
                output_dir=Path(tmp),
                generated_date="2026-04-11",
            )

            self.assertEqual(summary["fileCount"], 15)
            self.assertTrue((Path(tmp) / "00-문서안내.md").exists())
            self.assertTrue((Path(tmp) / "02-법령참조표.md").exists())
            self.assertTrue((Path(tmp) / "07-제5부(상).md").exists())
            self.assertTrue((Path(tmp) / "08-제5부(하).md").exists())

            guide = (Path(tmp) / "00-문서안내.md").read_text(encoding="utf-8")
            law_table = (Path(tmp) / "02-법령참조표.md").read_text(encoding="utf-8")
            upper_part_5 = (Path(tmp) / "07-제5부(상).md").read_text(encoding="utf-8")

            self.assertIn("> 출처 PDF: data/source/상표심사기준.pdf", guide)
            self.assertIn("실제 Google Docs 반영 전 단계 산출물", guide)
            self.assertIn("| 법령조문 | 부 | 장 | 항 | pageCode |", law_table)
            self.assertIn("#### 이미지 참고", upper_part_5)
            self.assertIn("- 섹션 이미지 참고 페이지:", upper_part_5)

    def test_split_part_5_is_aligned(self) -> None:
        config = load_config()
        search_index = load_generated_json("search-index.json")
        toc = load_generated_json("toc.json")
        image_manifest = load_generated_json("image-manifest.json")

        with tempfile.TemporaryDirectory() as tmp:
            export_notebooklm(
                config=config,
                search_index=search_index,
                toc=toc,
                image_manifest=image_manifest,
                output_dir=Path(tmp),
                generated_date="2026-04-11",
            )

            upper_part_5 = (Path(tmp) / "07-제5부(상).md").read_text(encoding="utf-8")
            lower_part_5 = (Path(tmp) / "08-제5부(하).md").read_text(encoding="utf-8")

            self.assertIn("# 제5부(상)", upper_part_5)
            self.assertIn("# 제5부(하)", lower_part_5)
            self.assertIn("## 제12장 ", upper_part_5)
            self.assertNotIn("## 제13장 ", upper_part_5)
            self.assertIn("## 제13장 ", lower_part_5)
            self.assertNotIn("## 제12장 ", lower_part_5)

    def test_export_uses_env_date_when_not_explicitly_provided(self) -> None:
        config = load_config()
        search_index = load_generated_json("search-index.json")
        toc = load_generated_json("toc.json")
        image_manifest = load_generated_json("image-manifest.json")

        with tempfile.TemporaryDirectory() as tmp:
            previous = os.environ.get("NOTEBOOKLM_EXPORT_DATE")
            os.environ["NOTEBOOKLM_EXPORT_DATE"] = "2026-04-12"
            try:
                export_notebooklm(
                    config=config,
                    search_index=search_index,
                    toc=toc,
                    image_manifest=image_manifest,
                    output_dir=Path(tmp),
                )
            finally:
                if previous is None:
                    os.environ.pop("NOTEBOOKLM_EXPORT_DATE", None)
                else:
                    os.environ["NOTEBOOKLM_EXPORT_DATE"] = previous

            guide = (Path(tmp) / "00-문서안내.md").read_text(encoding="utf-8")
            self.assertIn("> 생성일: 2026-04-12", guide)


if __name__ == "__main__":
    unittest.main()
