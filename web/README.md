# Web App

이 디렉터리는 `data/generated/` 산출물을 읽는 phase-1 TmEG reader shell입니다.

## Current State

- `index.html`: Vite entry
- `public/generated/`: 파이프라인 산출물을 동기화하는 위치
- `src/App.tsx`: HashRouter 기반 home/reader shell
- `src/lib/generated-data.ts`: generated JSON adapter layer
- `src/styles.css`: 모바일 우선 reader design system

## Usage

1. 루트에서 `npm run web:prepare`
2. 의존성이 없으면 `npm --prefix web install`
3. 개발 서버는 `npm --prefix web run dev`
4. 정적 빌드는 `npm --prefix web run build`
5. 빌드 미리보기는 `npm --prefix web run preview`

## Scope

- 리더는 `toc.json`, `document-data.json`, `search-index.json`, `exploration-index.json`, `manifest.json`을 직접 읽습니다.
- `overview`는 필요 시 런타임에서 synthetic section으로 보강합니다.
- exploration route join은 section id 단독이 아니라 chapter-aware composite key로 해결합니다.
- PDF/original document viewer, bookmark, worker search, scroll-driven URL mutation은 이번 phase 범위에 포함하지 않습니다.
