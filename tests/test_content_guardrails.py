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
collect_uncovered_non_toc_text_pages = build_content.collect_uncovered_non_toc_text_pages
derive_part_intro_title = build_content.derive_part_intro_title
extend_end_page_for_next_sibling = build_content.extend_end_page_for_next_sibling
extend_overview_end_page_for_leading_content = build_content.extend_overview_end_page_for_leading_content
find_part_intro_page_range = build_content.find_part_intro_page_range
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


MARK_TYPE_TABLE_BLOCK_TEXTS = [
    "1.1.4 출원서의 상표유형별 기재사항",
    "구 분",
    "상표견본",
    "설명란 기재",
    "시각적 표현",
    "첨부자료",
    "일반상표\n상표견본 1개\n임의\n불필요",
    "입체상표",
    "특징을 충분히 나타내는 5장 이하의 도면 또는 입체사진",
    "임의",
    "불필요",
    "사용증거(입체적 형상만으로 된 상표)",
    "색채만으로 된 상표",
    "단일색채나 색채의 조합만으로 채색된 1장의 도면 또는 사진",
    "필수",
    "불필요",
    "사용증거",
    "홀로그램상표",
    "특징을 충분히 나타내는 2장 이상 5장 이하의 도면 또는 사진",
    "필수",
    "불필요",
    "동영상자료(임의)",
    "동작상표",
    "특징을 충분히 나타내는 2장 이상 5장 이하의 도면 또는 사진",
    "필수",
    "불필요",
    "전자적 기록매체(필수)",
    "구 분",
    "상표견본",
    "설명란 기재",
    "시각적 표현",
    "첨부자료",
    "소리상표",
    "불필요",
    "필수",
    "필수",
    "사용증거(식별력 없는 소리인 경우)소리파일, 악보(임의)",
    "냄새상표",
    "불필요",
    "필수",
    "필수",
    "사용증거냄새견본",
    "기타 시각적 상표",
    "특징을 충분히 나타내는 5장 이하의 도면 또는 사진",
    "필수",
    "불필요",
    "사용증거동영상자료(임의)",
    "기타 비시각적 상표",
    "불필요",
    "필수",
    "필수",
    "사용증거기타 자료(임의)",
]


def make_text_blocks(
    texts: list[str],
    *,
    page_number: int = 91,
    page_code: str = "20303",
) -> list[dict[str, object]]:
    return [
        {
            "type": 0,
            "_pageNumber": page_number,
            "_pageCode": page_code,
            "_normalizedText": text,
        }
        for text in texts
    ]


def make_mark_type_table_blocks(*, extra_texts: list[str] | None = None, truncate_after: int | None = None) -> list[dict[str, object]]:
    texts = MARK_TYPE_TABLE_BLOCK_TEXTS.copy()
    if truncate_after is not None:
        texts = texts[:truncate_after]
    if extra_texts:
        texts.extend(extra_texts)
    return make_text_blocks(texts)


GOODS_NAMING_TABLE_BLOCK_TEXTS = [
    "1.1.3 독립적인 거래가 가능한 개별·구체적인 상품명칭을 기재하여야 하지만, 예외적으로 「상품고시」에서 인정하는 『협의의 포괄명칭』 및 『광의의 포괄명칭』을 기재할 수도 있다. 그 외에 포괄상품을 기재하는 경우 심사관은 법 제38조제1항을 적용하여 거절이유를 통지하여야 한다.",
    "구   분\n협의의 포괄명칭\n광의의 포괄명칭",
    "정   의",
    "동일 상품류 내 동일한 유사상품군에 속하는 여러 상품을 포함",
    "동일 또는 복수의 상품류 내 복수 유사군에 속하는 상품을 포함",
    "포괄명칭 사례\n신발(제25류, G270101)\n의류(제25류)",
    "스포츠전문의류(G430301),",
    "겉옷",
    "(G450101),",
    "한복(G4502),",
    "속옷",
    "(G4503) 등 포함",
    "해당하는 상품 또는 유사상품군",
    "가죽신, 운동화, 슬리퍼, 장화, 방한화, 골프화 등 포함",
    "1.2 지정상품은 한글로 기재함을 원칙으로 하되 한자나 외국어를 병기할 수도 있다.",
]

GOODS_REVIEW_TABLE_BLOCK_TEXTS = [
    "《지정상품 세분화에 따라 거절이유 해소가 가능한 경우 예시》",
    "구   분\n지정상품",
    "의류(제25류)(포함되는 유사상품군 : G430301, G450101, G450102, G4502, G4503, G450401, G4513)",
    "최초출원지정상품",
    "거절이유\n넥타이(G450401)와 관련하여 타인의 선등록상표와 동일 유사(법§34①7)",
    "보정 후지정상품",
    "넥타이가 속한 G450401 상품군을 제외, G430301, G450101, G450102, G4502, G4503, G4513에 속하는 구체적인 상품으로 보정",
    "《지정상품이 인정/불인정되는 경우》",
    "인정되지 않는 불명확한 명칭\n인정되는 명확한 명칭",
    "도매업, 소매업, 판매대행업, 판매알선업, 상품중개업",
    "가구소매업, 가구도매업, 가구판매대행업, 가구판매알선업, 가구중개업",
    "수리업, 수선업, 설치업, 유지관리업",
    "가구수리업, 가방수선업, 화재경보기설치업, 컴퓨터하드웨어유지관리업 등",
    "학원경영업",
    "외국어학원경영업, 미술학원경영업, 컴퓨터학원경영업 등",
    "2.2 판단시점",
]

GENERIC_NAME_EXAMPLE_TABLE_BLOCK_TEXTS = [
    "1.1 ‘상품의 보통명칭에 해당’할 것",
    "본호에서 규정하는 『그 상품의 보통명칭』이란 그 상품의 명칭, 약칭, 속칭, 기타 당해 상품을 취급하는 거래사회에서 그 상품을 지칭하는 것으로 실제로 사용되고 인식되어 있는 명칭을 말한다. 따라서 상표의 관념으로부터 유추하여 단순히 일반수요자가 상품의 보통명칭으로 인식할 우려가 있다는 것만으로는 이에 해당하지 않는다.",
    "《보통명칭 사례》",
    "지정상품\n상 표\n지정상품\n상 표포장용 필름",
    "랲(96후1224)",
    "자동차용 전구",
    "Truck Lite(96후986)",
    "커피음료",
    "Caffé Latté(02후321)",
    "화 장 품",
    "Foundation(01후89)",
    "위 장 약\n정로환(92후827)\n건 과 자\n콘치프(88후455)가구재료\n호마이카(86후93)\n복 사 기\nCOPYER(86후67)요 식 업\n카페, 그릴(99허2068)\n통 신 업\n컴퓨터통신",
    "1.2 상품의 보통명칭이 ‘보통으로 사용하는 방법으로 표시’되어 있을 것",
]
ONE_MARK_ONE_APPLICATION_TABLE_BLOCK_TEXTS = [
    "1.2 1상표 1출원 위반유형에 따른 심사처리방법",
    "출원인이 1상표 1출원을 위반하여 출원한 경우 다음 표와 같이 처리하되, 출원인에게 거절이유통지시 해당하는 상표, 지정상품의 삭제보정 및 분할 가능 여부를 함께 통지하여야 한다.",
    "1상표 1출원 위반 유형\n심 사 처 리 방 법\n보정방법",
    "동일상품에 동일상표를 중복출원",
    "후출원은 법§38① 위반으로 거절",
    "포괄상품인 경우(의류)에는 세부상품(바지)으로 감축",
    "보정",
    "일부상품에 동일상표를 중복출원\n후출원은 법§38① 위반으로 거절\n중복상품 삭제보정",
    "선등록상표와 동일상표를 동일상품에 중복출원",
    "출원상표를 법§38① 위반으로 거절",
    "포괄상품인 경우(의류)에는 세부상품(바지)으로 감축",
    "보정",
    "선등록상표와 동일상표를 일부상품에 중복출원",
    "출원상표를 법§38① 위반으로 거절",
    "중복상품 삭제보정",
    "1개 출원서에 동일상품 중복기재",
    "법§59(직권보정 등)에 따라 직권삭제 후출원공고결정시 직권보정사항 통보",
    "-",
    "일반상표나 색채상표를 출원하면서 상표견본을 여러 개 제출",
    "출원상표를 법§38① 위반으로 거절",
    "견본보정",
    "소리·냄새 등 비시각적 상표출원시 문자등 시각상표견본을 함께 제출",
    "출원상표를 법§38① 위반으로 거절",
    "상표견본 삭제보정",
    "1.3 1상표 1출원 위반 여부의 판단시점",
]

SOUND_FILING_TABLE_BLOCK_TEXTS = [
    "《소리상표의 상표등록출원서 기재사항 및 첨부서류 등》",
    "제출되는 서류 등의 종류",
    "관련조항",
    "필수 여부",
    "견본",
    "규칙 제28조제2항제1호",
    "없음",
    "설명서",
    "규칙 제28조제2항제2호",
    "필수",
    "시각적 표현",
    "규칙 제28조제2항제3호(규칙 제25조제1항제10호)",
    "필수",
    "소리파일",
    "규칙 제28조제2항제4호",
    "필수",
    "악보",
    "규칙 제28조제5항제5호",
    "선택",
    "2.2 소리상표는 상표의 설명란에 상표에 대한 설명이 필수적으로 기재(또는 별도의 상표에 대한 설명서를 제출)되어야 하므로(규칙§28②2), 상표의 설명이 제출되지 아니한 경우 법 제39조 및 규칙 제32조에 의하여 방식심사를 통해 보정이 이루어지는 것이 원칙이나, 상표에 대한 설명이 없는 출원서가 착오로 심사관에게 이송된 경우에는 법 제2조제1항의 상표의 정의규정에 합치하지 않는 것으로 보아 거절이유를 통지할 수 있다.",
]

SMELL_FILING_TABLE_BLOCK_TEXTS = [
    "《냄새상표의 상표등록출원서 기재사항 및 첨부서류 등》",
    "제출되는 서류 등의 종류",
    "관련조항",
    "필수 여부",
    "견본",
    "규칙 제28조제2항제1호",
    "없음",
    "상표에 대한 설명서",
    "규칙 제28조제2항제2호",
    "필수",
    "시각적표현",
    "규칙 제28조제1항제3호",
    "필수",
    "냄새견본(밀폐용기, 패치)",
    "규칙 제28조제2항제5호",
    "필수",
    "2.2 냄새상표는 상표의 설명란에 상표에 대한 설명이 필수적으로 기재(또는 별도의 상표에 대한 설명서를 제출)되어야 하므로(규칙§28②2), 상표의 설명이 제출되지 아니한 경우 법 제39조 및 규칙 제32조에 의하여 방식심사를 통해 보정이 이루어지는 것이 원칙이나, 상표에 대한 설명이 없는 출원서가 착오로 심사관에게 이송된 경우에는 법 제2조제1항의 상표의 정의규정에 합치하지 않는 것으로 보아 거절이유를 통지할 수 있다.",
]

SMELL_DISTINCTIVENESS_EXAMPLE_BLOCK_TEXTS = [
    "《품질·효능·용도 등을 직접적으로 나타내는 경우의 예시》",
    "지정상품\n냄   새타이어\n고무향목재가공업\n나무냄새커피전문점업\n커피향",
]

FAMOUS_MARK_COMPARISON_BLOCK_TEXTS = [
    "《참고 : 주지상표와 저명상표의 비교》",
    "구분\n주지상표\n저명상표입법취지\n사용사실상태의 보호\n출처혼동방지 또는 희석화 방지",
    "인식도",
    "당해 상표가 사용된 상품에 관한 거래자 및 관련 수요자층",
    "이종상품·이종영업에까지 걸친 일반수요자층",
    "범위",
    "상품의 동일․유사범위 내",
    "이종상품·이종영업까지 확대",
    "제척기간\n5년\n없음",
]

FAITH_COMPARISON_BLOCK_TEXTS = [
    "《법 제34조제1항제20호와 제4호 비교》",
    "법 §34①20\n법 §34①4",
    "당사자간 신의칙 위반이 있는 경우 적용",
    "상표 그 자체 또는 상품과의 관계에서 공서양속에 위반되거나, 출원·등록과정에서 사회적 타당성이 현저히 결여된 경우 적용단순한 신의칙 위반이 있었다는 이유만으로는 적용이 어렵고, 출원·등록과정에서 사회적 타당성이 현저히 결여된 경우 적용",
    "출원하기까지의 과정에서 신의칙 위반이 있는 경우 적용",
    "《법 제34조제1항제20호와 제13호 비교》",
    "법 §34①20\n법§34①13",
    "모방대상상표의 인식도가 필요 없음\n모방대상상표가 특정인의 상표로 인식되어야 함모방대상상표 사용자와 출원인간 신의관계 필요",
    "모방대상상표 사용자와 출원인간 신의관계 불요",
    "타인의 사용, 사용 준비중인 사실만 알고 있으면 적용",
    "부정한 목적이 있는 경우 적용",
    "동일·유사한 상품에 적용",
    "상품 제한 없음(다만, 부정목적 유무 판단을 위해 견련성 검토 필요)",
]

FAMOUS_DECEASED_COMPARISON_BLOCK_TEXTS = [
    "《법 제34조제1항제2호, 제4호, 제6호 비교》",
    "적용조문\n대  상\n\n요 건",
    "법§34①2",
    "저명한 고인",
    "고인과의 관계를 거짓으로 표시하거나 비방·모욕하거나 평판을 나쁘게 할 우려가 있는 경우",
    "법§34①4",
    "저명한 고인",
    "저명한 고인의 성명을 정당한 권리자의 동의 없이 출원하여 그 명성에 편승하려는 경우",
    "법§34①6",
    "현존하는 저명한 타인",
    "저명한 타인의 성명이나 그 약칭을 포함하는 경우",
]

HOLOGRAM_FILING_TABLE_BLOCK_TEXTS = [
    "《홀로그램상표의 상표등록출원서 기재사항 및 첨부서류 등》",
    "제출되는 서류 등의 종류\n관련조항\n필수 여부",
    "상표견본",
    "규칙 제28조제2항제1호(규칙 제29조제2항제3호)",
    "필수",
    "상표에 대한 설명서\n규칙 제28조제2항제2호\n필수",
    "전자적 기록매체",
    "규칙 제28조제5항제4호",
    "출원인 선택",
    "규칙 제29조제3항제2호\n심사관 요구",
    "2.3 홀로그램상표를 출원하면서 출원서에 상표견본을 첨부하여 제출하지 않고 전자적 기록매체만을 제출한 경우 상당한 기간을 정하여 도면 또는 사진으로 보완할 것을 명하여야 하며, 출원인이 절차보완서를 제출한 때에는 그 절차보완서가 지식재산처에 도달한 날을 상표등록출원일로 본다(법§37).",
]

BAD_FAITH_COMPARISON_BLOCK_TEXTS = [
    "《법 제34조제1항제9호, 제11호, 제12호, 제13호 비교》",
    "구분\n법§34①9\n법§34①11\n법§34①12\n법§34①13출처 오인·혼동 방지, 주지상표권자 이익보호",
    "저명상품·영업과의 오인·혼동으로부터 수요자 보호, 저명상표 희석화 방지",
    "상품의 품질오인, 출처 오인·혼동으로 인한 수요자 기만 방지(다만, 출처의 오인·혼동은 법§34①9,11,13 등을 요건에 맞게 우선 적용하고, 본호는 수요자 기만에 초점을 맞춰 적용)",
    "진정한 상표사용자 신용보호, 브로커 방지, 공정한 경쟁질서 확립",
    "취지",
    "동종업종에서 수요자들에게 현저하게 인식",
    "이종상품이나 영업에 걸친 거래자 및 일반수요자 대다수에게 현저하게 인식",
    "국내의 일반거래에 있어서 수요자나 거래자에게 인식",
    "국내·외 수요자들에게 특정인의 상품표지로 인식",
    "주지도",
    "비유사하여도 모티브나 아이디어 등을 비교하여 저명상표가 용이하게 연상되는 경우",
    "상표\n동일·유사",
    "동일·유사\n동일·유사",
    "비유사(다만, 수요자 기만 발생과 관련하여 견련관계 고려)",
    "비유사(다만, 부정목적 추정을 위해서는 견련성 검토 필요)",
    "상품\n동일·유사\n비유사",
    "상표 사용기간, 사용 방법, 사용지역, 거래 범위, 상품 판매량, 광고선전 등을 종합 고려",
    "좌동(다만, 특정인의 상표라는 인식+부당한 기대이익 유무를 통해 인식도 판단 가능)",
    "인식도 판단방법",
    "좌동\n좌동",
    "시기적 기준",
    "상표등록여부결정을 할 때",
    "상표등록출원을한 때",
    "상표등록여부결정을 할 때",
    "상표등록출원을한 때",
    "제척기간\n5년\n없음\n없음\n없음",
]

GOODS_TIMING_FIGURE_BLOCK_TEXTS = [
    "2.2.1 지정상품이 상품류 구분에 맞는지, 포괄이거나 불명확한지 여부를 판단하는 시점은 원칙적으로 출원시로 하며 소급하여 적용하지 아니한다. 따라서 「상품고시」의 개정으로 새로운 포괄명칭이 도입된 경우에는 그 시행일 이후에 출원된 지정상품부터 새로운 포괄명칭을 인정하며, 그 반대의 경우에도 마찬가지이다.",
    "《지정상품 심사 판단시점 : 출원시》",
    "심     사2012.12.1",
    "상 표 출 원2011.12.1",
    "상품고시개정2012.1.1",
    "스포츠후원 및 흥행업(S121001)",
    "<지정상품>스포츠 및오락흥행업(S1210)",
    "<상품인정>스포츠 및오락흥행업(S121001)(S121002)",
    "오락흥행업(S121002)",
    "2.2.2 법 제45조에 의하여 분할출원된 지정상품이 상품류 구분에 맞는지, 포괄이거나 불명확한지 여부를 판단하는 시점은 분할출원시가 아니라 최초출원시를 기준으로 한다.",
]


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

    def test_blocks_to_html_does_not_prepend_removed_synthetic_procedure_figure_for_요지변경이_아닌_경우(self) -> None:
        blocks = [
            {
                "type": 0,
                "_pageNumber": 134,
                "_pageCode": "30204",
                "lines": [{"spans": [{"text": "지정상품 범위의 감축은 요지변경이 아니다."}]}],
            },
            {
                "type": 0,
                "_pageNumber": 134,
                "_pageCode": "30204",
                "lines": [{"spans": [{"text": "명백한 오기의 정정은 요지변경이 아니다."}]}],
            },
        ]

        html = blocks_to_html(blocks, section_title="1. 요지변경이 아닌 경우")

        self.assertNotIn("reader-synthetic-figure", html)
        self.assertIn("지정상품 범위의 감축은 요지변경이 아니다.", html)
        self.assertIn("명백한 오기의 정정은 요지변경이 아니다.", html)
        self.assertEqual(
            blocks_to_text(blocks),
            "지정상품 범위의 감축은 요지변경이 아니다.\n\n명백한 오기의 정정은 요지변경이 아니다.",
        )

    def test_blocks_to_html_reconstructs_allowlisted_comparison_tables(self) -> None:
        blocks = [
            {"type": 0, "_pageNumber": 86, "_pageCode": "20206", "_normalizedText": "2.3.2 견련관계가 없는 비유사 상품의 종류를 다수 지정한 경우"},
            {"type": 0, "_pageNumber": 86, "_pageCode": "20206", "_normalizedText": "견련관계가 없는 경우(예시)\n견련관계가 있는 경우(예시)"},
            {"type": 0, "_pageNumber": 86, "_pageCode": "20206", "_normalizedText": "비료, 소주, 휠체어, 컴퓨터, 숙박업, 문구\n구두, 의류, 화장품, 장신구, 시계, 보석 광고업, 은행업, 건설업, 수선업, 식당업\n인쇄업, 광고업, 방송업, 통신업, 공연업"},
            {"type": 0, "_pageNumber": 86, "_pageCode": "20206", "_normalizedText": "2.3.3 개인이 법령상 일정자격 등이 필요한 상품과 관련하여 견련관계가 없는 상품을 2개 이상 지정한 경우"},
            {"type": 0, "_pageNumber": 86, "_pageCode": "20206", "_normalizedText": "견련관계가 없는 경우(예시)\n견련관계가 있는 경우(예시)병원업, 법무서비스업, 건축설계업\n변호사업, 변리사업, 공인노무사업"},
            {"type": 0, "_pageNumber": 86, "_pageCode": "20206", "_normalizedText": "2.3.4 기타 출원인이 상표를 사용할 의사 없이 상표 선점이나 타인의 상표등록을 배제할 목적 등으로 출원하는 것이라고 의심이 드는 경우"},
        ]

        html = blocks_to_html(blocks, section_title="2. 사용사실 및 사용의사의 확인")

        self.assertEqual(html.count('reader-synthetic-figure'), 2)
        self.assertEqual(html.count('<table>'), 2)
        self.assertIn('<th scope="col">견련관계가 없는 경우(예시)</th>', html)
        self.assertIn('<th scope="col">견련관계가 있는 경우(예시)</th>', html)
        self.assertIn('<td>비료, 소주, 휠체어, 컴퓨터, 숙박업, 문구</td>', html)
        self.assertIn('<td>구두, 의류, 화장품, 장신구, 시계, 보석</td>', html)
        self.assertIn('<td>광고업, 은행업, 건설업, 수선업, 식당업</td>', html)
        self.assertIn('<td>인쇄업, 광고업, 방송업, 통신업, 공연업</td>', html)
        self.assertIn('<td>병원업, 법무서비스업, 건축설계업</td>', html)
        self.assertIn('<td>변호사업, 변리사업, 공인노무사업</td>', html)
        self.assertLess(html.index('2.3.2 견련관계가 없는 비유사 상품의 종류를 다수 지정한 경우'), html.index('reader-synthetic-figure'))
        self.assertLess(html.index('2.3.3 개인이 법령상 일정자격 등이 필요한 상품과 관련하여 견련관계가 없는 상품을 2개 이상 지정한 경우'), html.rindex('reader-synthetic-figure'))
        self.assertLess(html.rindex('reader-synthetic-figure'), html.index('2.3.4 기타 출원인이 상표를 사용할 의사 없이'))
        self.assertEqual(
            blocks_to_text(blocks),
            "2.3.2 견련관계가 없는 비유사 상품의 종류를 다수 지정한 경우\n\n견련관계가 없는 경우(예시)\n견련관계가 있는 경우(예시)\n\n비료, 소주, 휠체어, 컴퓨터, 숙박업, 문구\n구두, 의류, 화장품, 장신구, 시계, 보석 광고업, 은행업, 건설업, 수선업, 식당업\n인쇄업, 광고업, 방송업, 통신업, 공연업\n\n2.3.3 개인이 법령상 일정자격 등이 필요한 상품과 관련하여 견련관계가 없는 상품을 2개 이상 지정한 경우\n\n견련관계가 없는 경우(예시)\n견련관계가 있는 경우(예시)병원업, 법무서비스업, 건축설계업\n변호사업, 변리사업, 공인노무사업\n\n2.3.4 기타 출원인이 상표를 사용할 의사 없이 상표 선점이나 타인의 상표등록을 배제할 목적 등으로 출원하는 것이라고 의심이 드는 경우",
        )

    def test_blocks_to_html_reconstructs_allowlisted_mark_type_table(self) -> None:
        blocks = make_mark_type_table_blocks(extra_texts=["1.2 상표유형별 기재사항 및 상표견본에 대한 심사"])

        html = blocks_to_html(blocks, section_title="1. 출원서의 기재사항")

        self.assertEqual(html.count('reader-synthetic-figure'), 1)
        self.assertEqual(html.count('<table>'), 1)
        self.assertIn('<th scope="col">구 분</th>', html)
        self.assertIn('<th scope="col">첨부자료</th>', html)
        self.assertIn('<td>일반상표</td>', html)
        self.assertIn('<td>상표견본 1개</td>', html)
        self.assertIn('<td></td>', html)
        self.assertIn('<td>사용증거(입체적 형상만으로 된 상표)</td>', html)
        self.assertIn('<td>사용증거(식별력 없는 소리인 경우)소리파일, 악보(임의)</td>', html)
        self.assertIn('<td>사용증거기타 자료(임의)</td>', html)
        self.assertLess(html.index('1.1.4 출원서의 상표유형별 기재사항'), html.index('reader-synthetic-figure'))
        self.assertLess(html.index('reader-synthetic-figure'), html.index('1.2 상표유형별 기재사항 및 상표견본에 대한 심사'))
        self.assertEqual(
            blocks_to_text(blocks),
            "\n\n".join(block["_normalizedText"] for block in blocks),
        )

    def test_blocks_to_html_does_not_reconstruct_mark_type_table_outside_allowlisted_section(self) -> None:
        blocks = make_mark_type_table_blocks()

        html = blocks_to_html(blocks, section_title="1. 상표 등의 등록을 받을 수 있는 자")

        self.assertNotIn('reader-synthetic-figure', html)
        self.assertNotIn('<table>', html)
        self.assertIn('구 분', html)
        self.assertIn('소리상표', html)
        self.assertIn('사용증거기타 자료(임의)', html)

    def test_blocks_to_html_falls_back_for_incomplete_mark_type_table_cluster(self) -> None:
        blocks = make_mark_type_table_blocks(truncate_after=len(MARK_TYPE_TABLE_BLOCK_TEXTS) - 1)

        html = blocks_to_html(blocks, section_title="1. 출원서의 기재사항")

        self.assertNotIn('reader-synthetic-figure', html)
        self.assertNotIn('<table>', html)
        self.assertIn('<p>구 분</p>', html)
        self.assertIn('일반상표<br />상표견본 1개<br />임의<br />불필요', html)
        self.assertIn('기타 비시각적 상표', html)

    def test_blocks_to_html_reconstructs_allowlisted_goods_naming_table(self) -> None:
        blocks = make_text_blocks(GOODS_NAMING_TABLE_BLOCK_TEXTS, page_number=95, page_code="20401")

        html = blocks_to_html(blocks, section_title="1. 지정상품의 기재요령")

        self.assertEqual(html.count('reader-synthetic-figure'), 1)
        self.assertEqual(html.count('<table>'), 1)
        self.assertIn('<th scope="col">협의의 포괄명칭</th>', html)
        self.assertIn('<th scope="col">광의의 포괄명칭</th>', html)
        self.assertIn('<td>포괄명칭 사례</td>', html)
        self.assertIn('스포츠전문의류(G430301),<br />겉옷(G450101),<br />한복(G4502),<br />속옷(G4503) 등 포함', html)
        self.assertLess(html.index('1.1.3 독립적인 거래가 가능한 개별·구체적인 상품명칭을 기재하여야 하지만'), html.index('reader-synthetic-figure'))
        self.assertLess(html.index('reader-synthetic-figure'), html.index('1.2 지정상품은 한글로 기재함을 원칙으로 하되'))
        self.assertEqual(blocks_to_text(blocks), "\n\n".join(GOODS_NAMING_TABLE_BLOCK_TEXTS))

    def test_blocks_to_html_reconstructs_allowlisted_goods_review_tables(self) -> None:
        blocks = make_text_blocks(GOODS_REVIEW_TABLE_BLOCK_TEXTS, page_number=97, page_code="20403")

        html = blocks_to_html(blocks, section_title="2. 지정상품의 심사")

        self.assertEqual(html.count('reader-synthetic-figure'), 2)
        self.assertEqual(html.count('<table>'), 2)
        self.assertIn('<th scope="col">구 분</th>', html)
        self.assertIn('<th scope="col">지정상품</th>', html)
        self.assertIn('<th scope="col">인정되지 않는 불명확한 명칭</th>', html)
        self.assertIn('<td>최초출원지정상품</td>', html)
        self.assertIn('<td>학원경영업</td>', html)
        self.assertIn('<td>외국어학원경영업, 미술학원경영업, 컴퓨터학원경영업 등</td>', html)
        self.assertLess(html.index('《지정상품 세분화에 따라 거절이유 해소가 가능한 경우 예시》'), html.index('reader-synthetic-figure'))
        self.assertLess(html.rindex('reader-synthetic-figure'), html.index('2.2 판단시점'))
        self.assertEqual(blocks_to_text(blocks), "\n\n".join(GOODS_REVIEW_TABLE_BLOCK_TEXTS))

    def test_blocks_to_html_reconstructs_allowlisted_generic_name_example_table(self) -> None:
        blocks = make_text_blocks(GENERIC_NAME_EXAMPLE_TABLE_BLOCK_TEXTS, page_number=161, page_code="40101")

        html = blocks_to_html(blocks, section_title="1. 적용요건")

        self.assertEqual(html.count('reader-synthetic-figure'), 1)
        self.assertEqual(html.count('<table>'), 1)
        self.assertIn('<th scope="col">지정상품</th>', html)
        self.assertIn('<th scope="col">상 표</th>', html)
        self.assertIn('<td>포장용 필름</td>', html)
        self.assertIn('<td>랲(96후1224)</td>', html)
        self.assertIn('<td>자동차용 전구</td>', html)
        self.assertIn('<td>Truck Lite(96후986)</td>', html)
        self.assertIn('<td>화 장 품</td>', html)
        self.assertIn('<td>컴퓨터통신</td>', html)
        self.assertLess(html.index('《보통명칭 사례》'), html.index('reader-synthetic-figure'))
        self.assertLess(html.index('reader-synthetic-figure'), html.index('1.2 상품의 보통명칭이 ‘보통으로 사용하는 방법으로 표시’되어 있을 것'))
        self.assertEqual(blocks_to_text(blocks), "\n\n".join(GENERIC_NAME_EXAMPLE_TABLE_BLOCK_TEXTS))
    def test_blocks_to_html_reconstructs_allowlisted_one_mark_one_application_table(self) -> None:
        blocks = make_text_blocks(ONE_MARK_ONE_APPLICATION_TABLE_BLOCK_TEXTS, page_number=101, page_code="20502")

        html = blocks_to_html(blocks, section_title="1. 위반유형 및 위반시 처리와 판단시점")

        self.assertEqual(html.count('reader-synthetic-figure'), 1)
        self.assertEqual(html.count('<table>'), 1)
        self.assertIn('<th scope="col">1상표 1출원 위반 유형</th>', html)
        self.assertIn('<th scope="col">심사 처리 방법</th>', html)
        self.assertIn('<th scope="col">보정방법</th>', html)
        self.assertIn('포괄상품인 경우(의류)에는 세부상품(바지)으로 감축<br />보정', html)
        self.assertIn('<td>상표견본 삭제보정</td>', html)
        self.assertLess(html.index('1.2 1상표 1출원 위반유형에 따른 심사처리방법'), html.index('reader-synthetic-figure'))
        self.assertLess(html.index('reader-synthetic-figure'), html.index('1.3 1상표 1출원 위반 여부의 판단시점'))
        self.assertEqual(blocks_to_text(blocks), "\n\n".join(ONE_MARK_ONE_APPLICATION_TABLE_BLOCK_TEXTS))

    def test_blocks_to_html_reconstructs_allowlisted_filing_requirement_tables(self) -> None:
        cases = [
            {
                "texts": SOUND_FILING_TABLE_BLOCK_TEXTS,
                "page_number": 491,
                "page_code": "40302",
                "section_title": "2. 상표 유형 및 상표의 설명에 대한 심사",
                "expected": ["<td>소리파일</td>", "<td>규칙 제28조제2항제4호</td>", "<td>선택</td>"],
            },
            {
                "texts": SMELL_FILING_TABLE_BLOCK_TEXTS,
                "page_number": 497,
                "page_code": "40402",
                "section_title": "2. 상표 유형 및 상표의 설명에 대한 심사",
                "expected": ["<td>냄새견본(밀폐용기, 패치)</td>", "<td>규칙 제28조제2항제5호</td>", "<td>필수</td>"],
            },
        ]

        for case in cases:
            with self.subTest(page_code=case["page_code"]):
                blocks = make_text_blocks(case["texts"], page_number=case["page_number"], page_code=case["page_code"])

                html = blocks_to_html(blocks, section_title=case["section_title"])

                self.assertEqual(html.count('reader-synthetic-figure'), 1)
                self.assertEqual(html.count('<table>'), 1)
                self.assertIn('<th scope="col">제출되는 서류 등의 종류</th>', html)
                self.assertIn('<th scope="col">관련조항</th>', html)
                self.assertIn('<th scope="col">필수 여부</th>', html)
                for expected in case["expected"]:
                    self.assertIn(expected, html)
                self.assertEqual(blocks_to_text(blocks), "\n\n".join(case["texts"]))

    def test_blocks_to_html_reconstructs_selected_allowlisted_reference_tables(self) -> None:
        cases = [
            {
                "texts": SMELL_DISTINCTIVENESS_EXAMPLE_BLOCK_TEXTS,
                "page_number": 499,
                "page_code": "40404",
                "section_title": "4. 식별력 유무에 대한 심사",
                "expected": ["<th scope=\"col\">지정상품</th>", "<td>타이어</td>", "<td>커피향</td>"],
            },
            {
                "texts": FAMOUS_MARK_COMPARISON_BLOCK_TEXTS,
                "page_number": 285,
                "page_code": "30704",
                "section_title": "4. 판단시점",
                "expected": ["<th scope=\"col\">주지상표</th>", "<td>입법취지</td>", "<td>출처혼동방지 또는 희석화 방지</td>"],
            },
            {
                "texts": FAMOUS_DECEASED_COMPARISON_BLOCK_TEXTS,
                "page_number": 229,
                "page_code": "30103",
                "section_title": "3. 다른 조문과의 관계",
                "expected": ["<th scope=\"col\">적용조문</th>", "<td>법§34①4</td>", "<td>저명한 타인의 성명이나 그 약칭을 포함하는 경우</td>"],
            },
            {
                "texts": FAITH_COMPARISON_BLOCK_TEXTS,
                "page_number": 339,
                "page_code": "31603",
                "section_title": "3. 다른 조문과의 관계",
                "expected": ["<th scope=\"col\">법 §34①20</th>", "<th scope=\"col\">법§34①13</th>", "<td>상품 제한 없음(다만, 부정목적 유무 판단을 위해 견련성 검토 필요)</td>"],
            },
        ]

        for case in cases:
            with self.subTest(page_code=case["page_code"]):
                blocks = make_text_blocks(case["texts"], page_number=case["page_number"], page_code=case["page_code"])

                html = blocks_to_html(blocks, section_title=case["section_title"])

                self.assertIn('reader-synthetic-figure', html)
                self.assertIn('<table>', html)
                for expected in case["expected"]:
                    self.assertIn(expected, html)
                self.assertEqual(blocks_to_text(blocks), "\n\n".join(case["texts"]))

    def test_blocks_to_html_reconstructs_allowlisted_hologram_filing_table(self) -> None:
        blocks = make_text_blocks(HOLOGRAM_FILING_TABLE_BLOCK_TEXTS, page_number=477, page_code="40202")

        html = blocks_to_html(blocks, section_title="2. 상표 유형 및 표장에 대한 심사")

        self.assertEqual(html.count('reader-synthetic-figure'), 1)
        self.assertEqual(html.count('<table>'), 1)
        self.assertIn('<th scope="col">제출되는 서류 등의 종류</th>', html)
        self.assertIn('<td>상표견본</td>', html)
        self.assertIn('출원인 선택<br />규칙 제29조제3항제2호<br />심사관 요구', html)
        self.assertLess(html.index('《홀로그램상표의 상표등록출원서 기재사항 및 첨부서류 등》'), html.index('reader-synthetic-figure'))
        self.assertLess(html.index('reader-synthetic-figure'), html.index('2.3 홀로그램상표를 출원하면서 출원서에 상표견본을 첨부하여 제출하지 않고'))
        self.assertEqual(blocks_to_text(blocks), "\n\n".join(HOLOGRAM_FILING_TABLE_BLOCK_TEXTS))

    def test_blocks_to_html_renders_allowlisted_goods_timing_crop_figure(self) -> None:
        blocks = make_text_blocks(GOODS_TIMING_FIGURE_BLOCK_TEXTS, page_number=99, page_code="20405")

        html = blocks_to_html(blocks, section_title="2. 지정상품의 심사")

        self.assertIn('<figure class="reader-image">', html)
        self.assertIn('src="generated/images/da51bb42fb7e.png"', html)
        self.assertIn('<figcaption>《지정상품 심사 판단시점 : 출원시》</figcaption>', html)
        self.assertNotIn('reader-synthetic-figure', html)
        self.assertLess(html.index('2.2.1 지정상품이 상품류 구분에 맞는지'), html.index('generated/images/da51bb42fb7e.png'))
        self.assertLess(html.index('generated/images/da51bb42fb7e.png'), html.index('2.2.2 법 제45조에 의하여 분할출원된 지정상품이'))
        self.assertEqual(blocks_to_text(blocks), "\n\n".join(GOODS_TIMING_FIGURE_BLOCK_TEXTS))

    def test_blocks_to_html_does_not_render_goods_timing_crop_outside_allowlisted_section(self) -> None:
        blocks = make_text_blocks(GOODS_TIMING_FIGURE_BLOCK_TEXTS, page_number=99, page_code="20405")

        html = blocks_to_html(blocks, section_title="1. 지정상품의 기재요령")

        self.assertNotIn('src="generated/images/da51bb42fb7e.png"', html)
        self.assertNotIn('reader-image', html)
        self.assertIn('《지정상품 심사 판단시점 : 출원시》', html)

    def test_blocks_to_html_reconstructs_allowlisted_bad_faith_comparison_table(self) -> None:
        blocks = make_text_blocks(BAD_FAITH_COMPARISON_BLOCK_TEXTS, page_number=298, page_code="30903")

        html = blocks_to_html(blocks, section_title="3. 판단시점")

        self.assertEqual(html.count('reader-synthetic-figure'), 1)
        self.assertEqual(html.count('<table>'), 1)
        self.assertIn('<th scope="col">법§34①9</th>', html)
        self.assertIn('<th scope="col">법§34①13</th>', html)
        self.assertIn('<td>취지</td>', html)
        self.assertIn('<td>진정한 상표사용자 신용보호, 브로커 방지, 공정한 경쟁질서 확립</td>', html)
        self.assertIn('<td>비유사(다만, 부정목적 추정을 위해서는 견련성 검토 필요)</td>', html)
        self.assertIn('<td>제척기간</td>', html)
        self.assertEqual(blocks_to_text(blocks), "\n\n".join(BAD_FAITH_COMPARISON_BLOCK_TEXTS))

    def test_blocks_to_html_falls_back_for_incomplete_goods_naming_table_cluster(self) -> None:
        texts = GOODS_NAMING_TABLE_BLOCK_TEXTS[:-2] + GOODS_NAMING_TABLE_BLOCK_TEXTS[-1:]
        blocks = make_text_blocks(texts, page_number=95, page_code="20401")

        html = blocks_to_html(blocks, section_title="1. 지정상품의 기재요령")

        self.assertNotIn('reader-synthetic-figure', html)
        self.assertNotIn('<table>', html)
        self.assertIn('<p>구   분<br />협의의 포괄명칭<br />광의의 포괄명칭</p>', html)
        self.assertIn('해당하는 상품 또는 유사상품군', html)
        self.assertIn('(G4503) 등 포함', html)

    def test_blocks_to_html_falls_back_for_incomplete_generic_name_example_table_cluster(self) -> None:
        texts = GENERIC_NAME_EXAMPLE_TABLE_BLOCK_TEXTS[:-2] + GENERIC_NAME_EXAMPLE_TABLE_BLOCK_TEXTS[-1:]
        blocks = make_text_blocks(texts, page_number=161, page_code="40101")

        html = blocks_to_html(blocks, section_title="1. 적용요건")

        self.assertNotIn('reader-synthetic-figure', html)
        self.assertNotIn('<table>', html)
        self.assertIn('<p>지정상품<br />상 표<br />지정상품<br />상 표포장용 필름</p>', html)
        self.assertIn('Truck Lite(96후986)', html)
        self.assertIn('Caffé Latté(02후321)', html)

    def test_blocks_to_html_does_not_reconstruct_comparison_tables_outside_allowlisted_section(self) -> None:
        blocks = [
            {"type": 0, "_pageNumber": 86, "_pageCode": "20206", "_normalizedText": "견련관계가 없는 경우(예시)\n견련관계가 있는 경우(예시)"},
            {"type": 0, "_pageNumber": 86, "_pageCode": "20206", "_normalizedText": "비료, 소주, 휠체어, 컴퓨터, 숙박업, 문구\n구두, 의류, 화장품, 장신구, 시계, 보석 광고업, 은행업, 건설업, 수선업, 식당업\n인쇄업, 광고업, 방송업, 통신업, 공연업"},
        ]

        html = blocks_to_html(blocks, section_title="1. 상표 등의 등록을 받을 수 있는 자")

        self.assertNotIn('reader-synthetic-figure', html)
        self.assertNotIn('<table>', html)
        self.assertIn('견련관계가 없는 경우(예시)', html)
        self.assertIn('비료, 소주, 휠체어, 컴퓨터, 숙박업, 문구', html)

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

    def test_find_part_intro_page_range_detects_pre_first_chapter_orphan_pages(self) -> None:
        inventory_page_map = build_inventory_page_map(
            {
                "pages": [
                    {"pageNumber": 158, "pageCode": None, "charCount": 0, "hasText": False, "topLines": []},
                    {
                        "pageNumber": 159,
                        "pageCode": None,
                        "charCount": 982,
                        "hasText": True,
                        "topLines": ["제4부 상표등록의 요건", "상표의 식별력"],
                    },
                    {
                        "pageNumber": 160,
                        "pageCode": None,
                        "charCount": 885,
                        "hasText": True,
                        "topLines": ["제4부 상표등록의 요건", "4. 법 제33조제1항 각 호의 차이"],
                    },
                    {
                        "pageNumber": 161,
                        "pageCode": "40101",
                        "charCount": 763,
                        "hasText": True,
                        "topLines": ["제1장 상품의 보통명칭인 상표"],
                    },
                ]
            }
        )

        self.assertEqual(
            find_part_intro_page_range(
                inventory_page_map,
                "제4부 상표등록의 요건",
                161,
            ),
            (159, 160),
        )

    def test_derive_part_intro_title_strips_running_header(self) -> None:
        blocks = make_text_blocks(
            [
                "제4부 상표등록의 요건",
                "상표의 식별력",
                "1. 식별력(Distinctiveness)의 의의",
            ],
            page_number=159,
            page_code="40101",
        )

        self.assertEqual(
            derive_part_intro_title(
                blocks,
                part_title="제4부 상표등록의 요건",
                chapter_title="제1장 상품의 보통명칭인 상표",
                fallback_label="제4부",
            ),
            "상표의 식별력",
        )

    def test_collect_uncovered_non_toc_text_pages_reports_uncovered_inventory_pages(self) -> None:
        inventory_page_map = build_inventory_page_map(
            {
                "pages": [
                    {"pageNumber": 159, "pageCode": None, "charCount": 982, "hasText": True, "topLines": ["제4부 상표등록의 요건", "상표의 식별력"]},
                    {"pageNumber": 160, "pageCode": None, "charCount": 885, "hasText": True, "topLines": ["제4부 상표등록의 요건", "4. 법 제33조제1항 각 호의 차이"]},
                    {"pageNumber": 161, "pageCode": "40101", "charCount": 763, "hasText": True, "topLines": ["제1장 상품의 보통명칭인 상표"]},
                ]
            }
        )
        section_entries = [
            {"id": "chapter-4-overview", "pageStart": 161, "pageEnd": 161},
        ]
        parts = [
            {
                "id": "part-4",
                "label": "제4부",
                "title": "상표등록의 요건",
                "fullTitle": "제4부 상표등록의 요건",
                "chapters": [{"id": "chapter-4"}],
            }
        ]
        chapter_start_by_slug = {"chapter-4": 161}

        self.assertEqual(
            collect_uncovered_non_toc_text_pages(
                inventory_page_map,
                parts,
                chapter_start_by_slug,
                section_entries,
            ),
            [
                {"pageNumber": 159, "pageCode": None, "topLines": ["제4부 상표등록의 요건", "상표의 식별력"]},
                {
                    "pageNumber": 160,
                    "pageCode": None,
                    "topLines": ["제4부 상표등록의 요건", "4. 법 제33조제1항 각 호의 차이"],
                },
            ],
        )

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
