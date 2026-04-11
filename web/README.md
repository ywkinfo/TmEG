# Web App

이 디렉터리는 `data/generated/` 산출물을 읽는 로컬 리더 웹앱입니다.

## Current State

- `index.html`: 정적 리더 진입점
- `public/generated/`: 파이프라인 산출물을 동기화하는 위치
- `src/app.js`: 목차, 본문, 검색, 탐색 상호작용
- `src/styles.css`: 리더 전용 스타일
- `README.md`: 실행 메모

## Usage

1. 루트에서 `npm run web:prepare`
2. 이어서 `npm run web:serve`
3. 브라우저에서 `http://localhost:4317`

## Scope

- 현재 리더는 `document-data.json`, `search-index.json`, `exploration-index.json`, `manifest.json`을 직접 읽습니다.
- 번들러나 프레임워크 없이 정적 파일로 실행되어, 데이터 계약 검증과 UI 방향 확인에 집중합니다.
- 원문 PDF 임베드는 아직 포함하지 않고, 구조화 JSON 소비와 탐색 흐름 확인을 우선합니다.
