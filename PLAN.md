# 상표심사기준 웹앱 — 최종 구현 계획

## Context

상표심사기준 PDF(575페이지, 5.5MB)를 검색·탐색 가능한 정적 웹앱으로 만드는 프로젝트입니다. 현재 하네스 기준 원문에는 텍스트 520페이지, 이미지 94페이지, 공백 55페이지가 있고, 구조 계약은 `10부 / 85장 / 319항 / 보충기준 2개`입니다. 원문 추적 가능성이 핵심 요구사항이며, 라이선스 확인 결과에 따라 오버레이형(v1) → 구조화 리더형(v2)으로 확장하는 2단계 전략을 따릅니다.

**결정된 사항**:
- 완전 독립 프로젝트 (`심사기준/` 디렉토리에서 진행)
- PDF 추출: Python pypdf
- 웹앱: Vite + React + TypeScript (정적 빌드)
- 원문 뷰어: pdf.js 임베드
- 검색: MiniSearch (GloTm 검증 완료된 라이브러리)
- PoC 범위: 제1부 총칙 (이미지 감지 + 원문 점프 fallback 포함)

---

## 원안 대비 수정사항

| 원안 | 수정 | 이유 |
|---|---|---|
| 7개 JSON 파일 | 5개로 간소화 (웹앱 배포 3 + 빌드 중간 2) | GloTm 패턴 참고, 과도한 분리 불필요 |
| 커스텀 검색 엔진 | MiniSearch 사용 | exact+prefix+fuzzy 이미 지원, 검증됨 |
| 이미지 처리 9단계 | 이미지 감지+fallback을 PoC에 포함 | 16% 페이지가 이미지, 리스크 조기 검증 필요 |
| PDF 뷰어 방식 미정 | pdf.js 임베드 확정 | 앱 내 페이지 점프가 가능한 유일한 방식 |
| 도구 미정 | Python pypdf 기준으로 정리 | 현재 하네스 구현 및 `pyproject.toml` 의존성과 일치 |
| `trademark-exam-service/` 별도 디렉토리 | 현재 `심사기준/` 디렉토리에서 진행 | 입력 PDF와 파이프라인이 이미 같은 워크스페이스 안에 있음 |

---

## 폴더 구조

```
심사기준/
├── LICENSE-NOTE.md              # 이용허락 범위 메모
├── pipeline/                    # Python PDF 추출·구조화·QA 스크립트
│   ├── common.py
│   ├── build_inventory.py
│   ├── build_toc.py
│   ├── build_content.py
│   └── qa_content.py
├── data/
│   ├── source/                  # 입력 설정
│   │   ├── 상표심사기준.pdf      # 원본 PDF
│   │   └── source-config.json
│   ├── research/                # 라이선스/수동 보정 메모
│   └── generated/               # 파이프라인 산출물
│       ├── pdf-inventory.json
│       ├── toc.json
│       ├── coverage-report.json
│       ├── document-data.json
│       ├── search-index.json
│       └── exploration-index.json
├── web/                         # 웹앱 소비 레일 (현재 스캐폴드)
│   ├── public/
│   │   └── generated/
│   └── src/
└── tests/                       # 구조·검색·커버리지 테스트
    ├── test_coverage.py
    ├── test_toc_mapping.py
    └── test_search.py
```

---

## 데이터 모델 (5개 파일)

### 빌드 중간산물 (웹앱에 배포하지 않음)

**1. `pages.jsonl`** — 페이지별 원문 (canonical layer)
```jsonl
{"page": 1, "text": "...", "hasImage": false, "isBlank": false, "headerCode": "총칙", "imageCount": 0}
```
- 575줄 (페이지당 1줄), 공백 페이지도 포함

**2. `coverage-report.json`** — QA 산출물
```json
{
  "totalPages": 575, "textPages": 520, "blankPages": 55, "imagePages": 94,
  "mappedPages": 575, "unmappedPages": 0,
  "toc": {"parts": 9, "chapters": 81, "sections": 310, "supplements": 2},
  "missingInToc": [], "orphanPages": []
}
```

### 웹앱 배포 대상

**3. `document-data.json`** — 목차 + 섹션 + 본문 HTML
```json
{
  "meta": {"title": "상표심사기준", "builtAt": "...", "partCount": 9, "chapterCount": 81, "sectionCount": 310},
  "parts": [
    {
      "id": "part-1",
      "title": "제1부 총칙",
      "chapters": [
        {
          "id": "ch-1-1",
          "slug": "제1부-총칙-제1장",
          "title": "제1장 ...",
          "sections": [
            {
              "id": "sec-1-1-1",
              "title": "1. ...",
              "html": "<div>...</div>",
              "pageStart": 12, "pageEnd": 14,
              "pageCodes": ["총칙-1-1"],
              "contentKind": "text",
              "hasImage": false, "hasTable": true
            }
          ],
          "headings": [{"id": "...", "depth": 3, "title": "...", "children": []}]
        }
      ]
    }
  ]
}
```

**4. `search-index.json`** — MiniSearch용 인덱스
```json
[
  {
    "id": "sec-1-1-1",
    "partTitle": "제1부 총칙",
    "chapterSlug": "제1부-총칙-제1장",
    "chapterTitle": "제1장 ...",
    "sectionTitle": "1. ...",
    "text": "원문 평문 텍스트...",
    "excerpt": "처음 200자...",
    "pageStart": 12,
    "pageCodes": ["총칙-1-1"],
    "lawRefs": ["상표법 제2조"]
  }
]
```

**5. `exploration-index.json`** — 탐색 facet 메타데이터
```json
[
  {
    "sectionId": "sec-1-1-1",
    "facets": {
      "part": "제1부 총칙",
      "chapter": "제1장 ...",
      "lawRefs": ["상표법 제2조"],
      "hasRequirements": true,
      "hasTimingRule": false,
      "hasCaseExample": false,
      "hasTable": true,
      "hasImage": false,
      "category": ["출원", "적용요건"]
    }
  }
]
```

---

## 구현 순서

### Phase 0: 환경 구축
- [ ] Python 가상환경 + pypdf 설치
- [ ] Vite + React + TypeScript 프로젝트 초기화 (`web/`)
- [ ] MiniSearch, pdfjs-dist 의존성 추가

### Phase 1: PDF Inventory (전체 575페이지)
- [ ] `extract_pages.py` 작성: 모든 페이지에서 텍스트, 이미지 존재 여부, 공백 여부 추출
- [ ] `pages.jsonl` 생성 — 575줄 전수 기록
- [ ] 기본 검증: 텍스트 520, 공백 55, 이미지 94 확인

### Phase 2: 목차 복원
- [ ] `parse_toc.py` 작성: 목차 페이지에서 `부 → 장 → 항 → 보충기준` 구조 파싱
- [ ] 10부 / 85장 / 319항 / 보충기준 2개 기준선 확인 및 잠금

### Phase 3: 본문 매핑 + 섹션 분할 (PoC: 제1부만)
- [ ] `split_sections.py` 작성: 각 페이지를 부/장/항에 연결
- [ ] 페이지 상단 코드값을 stable locator로 저장
- [ ] 항목 단위로 텍스트 분할
- [ ] **이미지 감지**: 제1부 내 이미지 포함 페이지 식별 + `hasImage` 플래그 설정
- [ ] `document-data.json` 생성 (제1부 범위)

### Phase 4: 검색 인덱스 (PoC: 제1부만)
- [ ] `build_search_index.py` 작성
- [ ] 섹션 단위 인덱스 생성
- [ ] `search-index.json` 생성

### Phase 5: 웹앱 기본 UI
- [ ] `App.tsx` — 3패널 레이아웃 (좌: 목차, 중: 본문, 우: 검색/탐색)
- [ ] `TocPanel.tsx` — 부/장/항 트리 탐색
- [ ] `ContentReader.tsx` — 섹션 HTML 렌더링 + 원문 페이지 번호 표시
- [ ] `SearchPanel.tsx` — MiniSearch 기반 실시간 검색 (Web Worker)
- [ ] `PdfViewer.tsx` — pdf.js 임베드 뷰어 + 페이지 점프
- [ ] **원문 점프**: 모든 섹션, 검색 결과에서 PDF 페이지로 이동 가능

### Phase 6: 커버리지 검증 (PoC 게이트)
- [ ] `qa_coverage.py` 작성
- [ ] 제1부 범위에서 미매핑 페이지 0건 확인
- [ ] 이미지 포함 페이지의 fallback(원문 점프) 작동 확인
- [ ] 검색 결과에서 원문 페이지 이동 확인
- [ ] **PoC 판정**: 전체 확장 가능 여부, 누락률, 검색 속도, 이미지 처리 난이도 평가

### Phase 7: 전체 확장 (PoC 통과 후)
- [ ] 제2부~제10부 + 보충기준 2개 처리
- [ ] 575페이지 전체 커버리지 달성
- [ ] `exploration-index.json` 생성 (faceted 탐색)
- [ ] `ExplorePanel.tsx` — 중요 정보 탐색 UI

### Phase 8: 이미지/표 보강
- [ ] 표 → HTML 재구성 (가능한 범위)
- [ ] 이미지 포함 페이지 → 자산 추출 또는 원문 점프 보완

### Phase 9: 검증 게이트 (최종)
- [ ] 575페이지 모두 inventory 존재
- [ ] 575페이지 모두 구조 또는 페이지 레벨에서 접근 가능
- [ ] 공백 55페이지 누락 없음
- [ ] 이미지 94페이지 coverage 확보
- [ ] 10부/85장/319항/보충기준 2개 매핑 성공
- [ ] 검색 결과에서 항상 원문 페이지 이동 가능
- [ ] 미매핑 페이지 0건
- [ ] 원문 없는 중요 정보 카드 0건

---

## 검증 방법

1. **파이프라인 검증**: `python qa_coverage.py` — 커버리지 리포트 생성, 누락 0건 확인
2. **구조 검증**: `python tests/test_toc_mapping.py` — 목차↔본문 매핑 일치 확인
3. **검색 검증**: `python tests/test_search.py` — 주요 키워드 검색 결과 확인
4. **웹앱 검증**: `npm run dev` 후 브라우저에서 수동 확인 — 목차 탐색, 검색, 원문 점프
5. **빌드 검증**: `npm run build` — 정적 빌드 성공 확인

---

## 주요 파일 경로

| 파일 | 역할 |
|---|---|
| `data/source/상표심사기준.pdf` | 원본 PDF (이미 존재) |
| `pipeline/extract_pages.py` | Phase 1 핵심 스크립트 |
| `pipeline/parse_toc.py` | Phase 2 핵심 스크립트 |
| `pipeline/split_sections.py` | Phase 3 핵심 스크립트 |
| `data/generated/document-data.json` | 웹앱 핵심 데이터 |
| `web/src/components/PdfViewer.tsx` | pdf.js 임베드 뷰어 |
| `web/src/search/worker.ts` | Web Worker 검색 |

---

## GloTm에서 참고할 패턴 (복사가 아닌 참고)

- `searchPanel.tsx` — MiniSearch 초기화, 디바운싱, 키보드 네비게이션 패턴
- `markdownArticle.tsx` — HTML 렌더링, 앵커 링크, 테이블 스크롤 래핑 패턴
- `shared.ts` — Chapter, SearchEntry, HeadingNode 타입 구조
- `build-content.ts` — heading tree 구축 로직, excerpt 생성 로직
