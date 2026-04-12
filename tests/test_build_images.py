from __future__ import annotations

import unittest
from unittest import mock

from pipeline.build_images import (
    DEFAULT_IMAGE_EXCLUSION,
    TIMELINE_CROP_IMAGE_SPECS,
    build_region_asset,
    build_manifest_entries,
    is_decorative_page,
    load_image_exclusion,
    prune_repeated_assets,
    should_skip_image_info,
    should_skip_page,
)


class BuildImagesTest(unittest.TestCase):
    def test_load_image_exclusion_applies_defaults(self) -> None:
        exclusion = load_image_exclusion({})

        self.assertEqual(exclusion, DEFAULT_IMAGE_EXCLUSION)

    def test_should_skip_page_respects_toc_cover_and_decorative_rules(self) -> None:
        exclusion = load_image_exclusion({})
        decorative_page = {"charCount": 20, "imageCount": 3}
        normal_page = {"charCount": 200, "imageCount": 1}

        self.assertTrue(should_skip_page(8, normal_page, {8, 9}, exclusion))
        self.assertTrue(should_skip_page(1, normal_page, set(), exclusion))
        self.assertTrue(is_decorative_page(decorative_page, exclusion))
        self.assertTrue(should_skip_page(30, decorative_page, set(), exclusion))
        self.assertFalse(should_skip_page(30, normal_page, set(), exclusion))

    def test_should_skip_image_info_respects_min_dimensions(self) -> None:
        exclusion = load_image_exclusion({"imageExclusion": {"minDimensionPx": 50}})

        self.assertTrue(should_skip_image_info({"width": 10, "height": 100}, exclusion))
        self.assertTrue(should_skip_image_info({"width": 100, "height": 10}, exclusion))
        self.assertFalse(should_skip_image_info({"width": 100, "height": 100}, exclusion))

    def test_prune_repeated_assets_excludes_high_repetition_assets(self) -> None:
        assets = {
            "keep": {"_pageNumbers": [10, 11]},
            "drop": {"_pageNumbers": list(range(1, 13))},
        }

        kept_assets, excluded_occurrence_count = prune_repeated_assets(assets, max_page_repetitions=10)

        self.assertEqual(list(kept_assets), ["keep"])
        self.assertEqual(excluded_occurrence_count, 12)

    def test_build_manifest_entries_strips_private_fields_and_sorts(self) -> None:
        assets = {
            "b": {
                "id": "bbbbbbbbbbbb",
                "filename": "bbbbbbbbbbbb.png",
                "relativePath": "images/bbbbbbbbbbbb.png",
                "width": 100,
                "height": 80,
                "byteSize": 42,
                "_pageNumbers": [20],
                "_pageCodes": ["10301"],
            },
            "a": {
                "id": "aaaaaaaaaaaa",
                "filename": "aaaaaaaaaaaa.png",
                "relativePath": "images/aaaaaaaaaaaa.png",
                "width": 120,
                "height": 90,
                "byteSize": 84,
                "_pageNumbers": [10],
                "_pageCodes": ["10201"],
            },
        }

        entries = build_manifest_entries(assets)

        self.assertEqual([entry["id"] for entry in entries], ["aaaaaaaaaaaa", "bbbbbbbbbbbb"])
        self.assertEqual(
            set(entries[0]),
            {"id", "filename", "relativePath", "pageNumbers", "pageCodes", "width", "height", "byteSize"},
        )

    def test_build_region_asset_uses_spec_metadata_and_png_bytes(self) -> None:
        spec = TIMELINE_CROP_IMAGE_SPECS["《마지막 월에 해당일이 없는 경우 기간의 만료일》"]
        page = mock.Mock()
        pixmap = mock.Mock(width=840, height=320)
        pixmap.tobytes.return_value = b"png-bytes"
        page.get_pixmap.return_value = pixmap

        document = mock.Mock()
        document.load_page.return_value = page

        asset = build_region_asset(document, spec)

        self.assertEqual(asset["id"], "3d4c8a2e7b9f")
        self.assertEqual(asset["filename"], "3d4c8a2e7b9f.png")
        self.assertEqual(asset["relativePath"], "images/3d4c8a2e7b9f.png")
        self.assertEqual(asset["_pageCodes"], ["10406"])
        self.assertEqual(asset["_pageNumbers"], [46])
        self.assertEqual(asset["width"], 840)
        self.assertEqual(asset["height"], 320)
        self.assertEqual(asset["byteSize"], len(b"png-bytes"))
        page.get_pixmap.assert_called_once()

    def test_build_region_asset_uses_scanned_figure_crop_spec_metadata(self) -> None:
        spec = TIMELINE_CROP_IMAGE_SPECS["《지정상품 심사 판단시점 : 출원시》"]
        page = mock.Mock()
        pixmap = mock.Mock(width=836, height=324)
        pixmap.tobytes.return_value = b"png-bytes"
        page.get_pixmap.return_value = pixmap

        document = mock.Mock()
        document.load_page.return_value = page

        asset = build_region_asset(document, spec)

        self.assertEqual(asset["id"], "da51bb42fb7e")
        self.assertEqual(asset["filename"], "da51bb42fb7e.png")
        self.assertEqual(asset["relativePath"], "images/da51bb42fb7e.png")
        self.assertEqual(asset["_pageCodes"], ["20405"])
        self.assertEqual(asset["_pageNumbers"], [99])
        self.assertEqual(asset["width"], 836)
        self.assertEqual(asset["height"], 324)
        self.assertEqual(asset["byteSize"], len(b"png-bytes"))
        page.get_pixmap.assert_called_once()


if __name__ == "__main__":
    unittest.main()
