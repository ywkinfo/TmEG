# 심사기준 Harness Architecture

## Purpose

이 워크스페이스는 `data/source/상표심사기준.pdf`를 독립 서비스용 구조화 데이터로 변환하기 위한 PDF 중심 하네스입니다.
현재 목표는 서비스 UI 완성이 아니라, 원문 추적 가능한 inventory, 목차, 챕터 데이터, 검색 인덱스를 재현 가능한 방식으로 생성하고 이를 미래 웹앱이 읽기 쉬운 구조로 정렬하는 것입니다.

## Source Of Truth

- 원본 PDF: `data/source/상표심사기준.pdf`
- 입력 설정: `data/source/source-config.json`
- 리서치/허가 메모: `data/research/`
- 생성 산출물: `data/generated/*.json`
- 파이프라인 스크립트: `pipeline/*.py`
- 웹앱 소비 레일: `web/`

## Pipeline

1. `pipeline/build_inventory.py`가 PDF 전 페이지를 스캔해 inventory를 만듭니다.
2. `pipeline/build_toc.py`가 목차 페이지를 파싱해 구조를 복원합니다.
3. `pipeline/build_content.py`가 inventory와 toc를 바탕으로 chapter JSON, search index, coverage report를 만듭니다.
4. `pipeline/qa_content.py`가 구조 수치와 매핑 누락을 검사합니다.
5. `web/`는 위 산출물을 읽는 앱이 자리잡을 경로로 남겨 둡니다.

## Generated Outputs

- `pdf-inventory.json`: 페이지별 텍스트/이미지/상단 코드 inventory
- `toc.json`: 부/장/항/보충기준 구조
- `document-data.json`: 리더용 chapter 데이터
- `search-index.json`: 검색용 section 인덱스
- `exploration-index.json`: 중요 정보 탐색용 facet 데이터
- `coverage-report.json`: 구조 매핑 누락 리포트

## Local Verification Contract

- 기준 명령: `npm run content:prepare`
- inventory, toc, document-data, search-index, coverage-report가 모두 재생성되어야 합니다.
- 현재 기준선은 `575 페이지 / 10부 / 85장 / 319항 / 보충기준 2개`입니다.

## Editing Rules

- 원본 PDF는 직접 수정하지 않습니다.
- generated JSON은 수동 수정하지 않습니다.
- 구조 기준선이나 입력 경로를 바꿀 때는 `data/source/source-config.json`과 문서를 함께 갱신합니다.
- page code 해석, 목차 파싱 규칙, coverage 기준은 스크립트와 하네스 문서에 같이 남깁니다.
