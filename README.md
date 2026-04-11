# 심사기준

상표심사기준 PDF를 신뢰할 수 있는 구조화 데이터로 재현하고, 그 결과를 이후 웹앱에서 소비할 수 있게 정리한 독립 워크스페이스입니다.
현재 입력 원천은 `data/source/상표심사기준.pdf`이며, 이 워크스페이스는 PDF inventory, 목차 복원, 검색용 인덱스, 리더용 문서 데이터 생성과 웹 소비 레일 분리를 담당합니다.

## Structure

- `data/source/상표심사기준.pdf`: 원본 PDF
- `data/source/README.md`: 원본 PDF 배치 규칙과 로컬 준비 메모
- `PROJECT-OVERVIEW.md`: 현재 phase, 목표, 검증 기준
- `pyproject.toml`: Python 의존성 및 pytest 설정
- `Harness/`: 하네스 계약 문서
- `data/source/source-config.json`: PDF 입력과 기대 구조 수치
- `data/research/`: 라이선스 메모, 수동 보정 메모, 검증 기록
- `data/generated/`: inventory, toc, coverage, document-data, search-index, exploration-index 산출물
- `pipeline/common.py`: 공용 경로, JSON 입출력, PDF 헬퍼
- `pipeline/build_inventory.py`: 페이지 inventory 생성
- `pipeline/build_toc.py`: PDF 목차 복원
- `pipeline/build_content.py`: 리더/검색용 JSON 생성
- `pipeline/qa_content.py`: 구조 QA, coverage, 목차 오염 가드레일 검증
- `pipeline/sync_web_generated.py`: generated JSON을 `web/public/generated/`로 동기화
- `web/`: generated JSON을 직접 읽는 로컬 리더 앱

## Commands

- `npm run content:inventory`: 페이지 inventory 생성
- `npm run content:toc`: 목차 구조 복원
- `npm run content:build`: 문서 데이터와 검색 인덱스 생성
- `npm run content:qa`: 구조 수치와 coverage 검증
- `npm run content:prepare`: inventory, toc, build, qa를 순서대로 실행
- `npm run web:sync`: 현재 generated JSON을 웹 리더 경로로 복사하고 manifest를 생성
- `npm run web:prepare`: content pipeline 재생성 후 웹 리더 자산까지 동기화
- `npm run web:serve`: `http://localhost:4317`에서 정적 리더 실행
- `npm run test`: pytest로 로컬 테스트 실행

## Notes

- 원본 PDF는 직접 수정하지 않습니다.
- 원본 PDF는 `.gitignore`로 저장소에 포함하지 않으며, 각 환경에서 `data/source/상표심사기준.pdf` 경로에 별도로 배치해야 합니다.
- generated JSON은 손으로 맞추지 말고 스크립트 재실행으로 갱신합니다.
- 라이선스와 공개 허용 범위는 `data/research/` 메모로 별도 관리하는 것을 전제로 합니다.
- 현재 하네스의 목표는 누락 없는 구조 복원과 검색/탐색용 데이터 기반을 안정적으로 만들고, 그 결과를 `web/` 앱이 바로 읽을 수 있게 유지하는 것입니다.
- 현재 하네스의 실행 계약은 `README.md`, `Harness/*.md`, `data/source/source-config.json`, 실제 파이프라인 스크립트가 우선이며, `PLAN.md`는 미래 리더 앱 구상 참고 문서로 취급합니다.
- 동일한 `pageCode`가 목차 페이지와 본문 페이지에 함께 나오면 본문 페이지를 우선 사용해야 하며, generated summary/excerpt가 `목 차`류 텍스트로 시작하면 QA에서 실패해야 합니다.
- 웹 리더는 번들러 없이 정적 파일로 열리며, 먼저 `npm run web:prepare`로 JSON을 동기화한 뒤 `npm run web:serve`로 확인합니다.
