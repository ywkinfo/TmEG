# Source Inputs

이 디렉터리는 파이프라인 입력 원본을 두는 위치입니다.

- 기대 파일명: `상표심사기준.pdf`
- 기대 경로: `data/source/상표심사기준.pdf`
- 이 PDF는 `.gitignore`에 의해 저장소에 커밋되지 않습니다.
- 새 환경에서는 라이선스/보관 정책에 맞게 PDF를 별도로 확보한 뒤 위 경로에 배치해야 합니다.

실행 전 확인:

- `data/source/source-config.json`의 `sourcePdf` 값이 실제 파일 위치와 일치해야 합니다.
- 파일이 없으면 파이프라인은 `원본 PDF를 찾을 수 없습니다` 오류로 종료됩니다.
