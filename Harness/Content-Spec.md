# 심사기준 Harness Content Spec

## Canonical Inputs

- 원본 PDF: `data/source/상표심사기준.pdf`
- 입력 설정: `data/source/source-config.json`

중요:

- 이 워크스페이스의 입력 원천은 마크다운 원고가 아니라 PDF입니다.
- 따라서 chapter 경계와 section 경계는 목차와 page code에서 복원합니다.

## Source Config Rules

- `documentTitle`은 생성 산출물의 문서 제목 기준입니다.
- `sourcePdf`는 워크스페이스 루트 기준 상대 경로여야 합니다.
- `expectedStructure`는 현재 QA 계약 수치입니다.
- 수치 계약이 바뀌면 QA와 문서를 함께 갱신합니다.

## Inventory Rules

- 각 페이지는 `pageNumber`, `pageCode`, `charCount`, `imageCount`, `topLines`를 가집니다.
- 공백 페이지도 inventory에서 생략하지 않습니다.
- page code는 페이지 상단 근처에서 찾은 첫 5자리 숫자를 기준으로 기록합니다.

## TOC Rules

- 목차 페이지는 PDF 앞부분에서 `목 차` 또는 `목차`를 포함한 페이지를 기준으로 찾습니다.
- 동일한 `pageCode`가 목차 페이지와 본문 페이지에 함께 나오면 본문 페이지를 canonical start로 사용합니다.
- 목차 페이지는 구조 복원용 신호이며 chapter/section 본문 시작 페이지로 직접 사용하지 않습니다.
- 구조 단위는 `부`, `장`, `항`, `보충기준`입니다.
- 긴 항목은 여러 줄로 분리되어도 하나의 항목으로 다시 합쳐야 합니다.

## Search And Reader Rules

- chapter 데이터는 `partTitle`, `chapterTitle`, `pageStart`, `pageEnd`, `pageCode`를 보존합니다.
- search entry는 locator 없는 요약이 되면 안 됩니다.
- search entry는 최소한 `chapterTitle`, `sectionTitle`, `pageStart`, `pageEnd`, `pageCode`를 가져야 합니다.
- generated chapter summary, search excerpt, exploration excerpt는 `목 차` 또는 문서 제목 + 로마 숫자 목차 헤더로 시작하면 안 됩니다.
- 중요 정보 탐색은 제목 패턴 기반 facet을 우선 사용합니다.
