# 심사기준 Workspace Overview

## Current Phase

- phase: PDF 구조 복원 하네스 정착 + 웹앱 소비 레일 정렬
- goal: 원본 PDF를 inventory, 목차, chapter JSON, search index로 재현 가능하게 추출하고, 그 결과를 웹앱이 읽기 쉬운 구조로 유지
- non-goal: 공개 웹앱 UI 완성, 라이선스 확정, 원문 HTML 완전 정규화

## Success Criteria

1. `npm run content:prepare`가 로컬에서 끝까지 실행된다.
2. inventory가 PDF 전체 페이지 수를 빠짐없이 기록한다.
3. 목차 복원 결과가 현재 기준선인 `10부 / 85장 / 319항 / 보충기준 2개`와 일치한다.
4. 챕터와 검색 엔트리가 생성된다.
5. QA가 누락된 핵심 page code와 구조 mismatch를 잡아낸다.

## Working Focus

- PDF 전수 inventory
- 목차 파싱 안정화
- page code 기반 구조 매핑
- 리더/검색용 JSON 최소 계약 고정
- coverage 리포트 생성

## Next Likely Step

- `web/`에 현재 하네스로 생성된 JSON을 읽는 독립 리더 앱 골격 추가
- 이미지/표 별도 자산 추출 lane 분리
- 수동 보정 manifest 도입
