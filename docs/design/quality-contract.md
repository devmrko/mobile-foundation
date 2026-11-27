# 모바일 화면의 재사용·품질 검사 설계

새 기능을 조립할 때 공통 구성과 필수 검증이 빠지는 문제를 줄인다. 2026-11-27 사용자 요청으로 네 Foundation에 같은 품질 원칙을 적용한다. 이 문서는 이 저장소의 구현 계약이며 개인 기억의 사본이 아니다. 전역 원칙은 지식 DB에서 관리하고 여기에는 기술별 실행 계약을 둔다.

## 적용 계약

| 원칙 | 이 저장소의 적용 |
|---|---|
| Q1 재사용 | mf 토큰·매크로·frame_tabs/frame_detail을 기본 경로로 사용 |
| Q2 조합 | 프레임이 하단바 여백을 소유하고 field가 라벨·오류 연결을 소유 |
| Q3 상태 | 정상·비활성·입력 오류·빈 결과·로딩을 gallery와 렌더 테스트로 확인 |
| Q4 자동 검사 | 렌더된 HTML의 mf 클래스 누락·중복 ID·깨진 라벨/설명 연결·탭 활성 상태를 audit_html로 검사 |
| Q5 독립 소비 | wheel을 임시 venv에 설치해 원본 소스 없이 template/CSS/audit를 사용 |
| Q6 증거 | DOM/CSS 검사와 브라우저 시각 비교·실기기 검증을 구분 |

## 구현과 경계

Python 표준 HTMLParser로 렌더 결과를 검사하는 mobile_foundation.quality 모듈과 CLI를 제공한다. 정규식으로 Jinja 원본을 검사하지 않는다. 범위는 mf 컴포넌트 계약에 한정하며 범용 HTML validator나 접근성 검사 대체가 아니다. 화면 검사에서는 전체 문서 기준으로 ID 참조를 해석한다. 모듈은 FastAPI 없이 동작한다. 기존 public macro 인자는 바꾸지 않는다.

scripts/check-quality.sh에서 lint, pytest, build, 설치된 wheel 소비를 순서대로 실행한다. CI도 같은 명령을 사용한다. 기준 이미지를 새로 승인하거나 Storybook·Chromatic을 설치하는 작업은 포함하지 않는다. 렌더된 소비 화면은 python -m mobile_foundation.quality page.html로 검사한다.

## 완료 기준

- `bash scripts/check-quality.sh`가 실제 검사를 실행하고 첫 실패에서 0이 아닌 코드로 종료한다.
- 새 검사는 정상 소비 예제와 의도적으로 잘못된 예제에서 각각 통과·실패를 검증한다.
- 기존 검사를 유지하며 진행 중인 다른 변경을 덮어쓰지 않는다.
- 실행한 검사·실행하지 않은 환경과 시각 확인을 분리해서 보고한다.

## 소비 화면 검사

의존성을 설치한 소비 앱에서 렌더된 HTML을 저장한 뒤 실행한다.

```sh
python -m mobile_foundation.quality rendered-page.html
```

`mf-`는 Foundation 전용 클래스 접두사다. 앱 고유 클래스는 다른 접두사를 사용한다. CLI에는 전체 페이지를 전달하며 mf-main이 정확히 한 개 있어야 한다. API에서 부분 부품을 검사할 때는 기본 require_frame=False를 사용하고, 전체 페이지는 require_frame=True로 검사한다. 알 수 없는 클래스, modifier의 기본 클래스 누락, ID 중복, 라벨/설명 참조 누락, 활성 탭 개수, 하단바 본문 여백을 검사한다. 이 검사는 계산된 CSS, 실제 클릭 가능 여부, 화면 잘림이나 미적 완성도를 판단하지 않는다. 브라우저 시각 비교와 키보드·실기기 검증은 별도로 수행한다.

실제 실행 결과: [적용 검증](../reviews/quality-contract-validation.md).

## 개발 검사 보완 (2026-11-27)

렌더 검사를 유지하면서 Ruff 포맷 검사와 배포 패키지의 엄격한 mypy 검사를 공통 명령에 추가한다. HTML 파서의 노드 구조와 공개 install 함수의 타입을 명시하되 FastAPI는 선택 의존성으로 유지한다. 기존 포맷을 한 번 정리하고 이후 불일치를 CI에서 실패시킨다. 검사 실패를 숨기거나 자동 수정한 결과를 CI가 커밋하지 않는다.

Dependabot은 uv 및 GitHub Actions 업데이트를 매주 제안한다. Gitleaks는 전체 Git 이력을 비밀값을 가린 상태로 검사한다. 원격 설정은 기본 브랜치에 반영된 뒤 동작하며 자동 병합은 구성하지 않는다.
