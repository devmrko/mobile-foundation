# 공통 품질 계약 적용 검증

2026-11-27, 현재 로컬 작업 트리에서 Codex가 실행한 원본 검증 기록이다. 기존 진행 중 변경은 보존했다. 원격 CI 실행·릴리스·소비 프로젝트 일괄 업그레이드는 수행하지 않았다.

- Python 3.13.16에서 `UV_BIN=/Users/joungmin/devkit/workspace/python-foundation/.tools/uv/bin/uv bash scripts/check-quality.sh`를 실행했다. UV_BIN은 이번 환경의 실행 도구 경로이며 기본 명령은 uv 또는 저장소 uvw를 사용한다.
- 전체 검사 명령 종료 0. lint 및 실제 CSS·렌더·누락 변형 테스트 16개 통과.
- wheel/sdist를 빌드하고 소스 경로 없이 새 venv의 wheel로 gallery/CSS/quality API와 CLI를 사용했다.
- 코드로 확인한 것은 렌더된 DOM 계약과 CSS 수치다. 스크린샷 비교, 브라우저 수동 관찰, 실제 휴대폰 검증은 이번 작업에서 실행하지 않았다.
- Starlette TestClient의 HTTPX deprecation 경고를 숨기지 않았다.

## 개발 검사 보완 검증 (2026-11-27)

Codex가 이 작업 트리에서 추가 실행했다. 원격 push와 새 GitHub CI 실행은 하지 않았다.

- `bash scripts/check-quality.sh` 종료 0. Ruff 린트·포맷, 패키지 두 소스 파일의 strict mypy, 기존 테스트 16개, sdist/wheel 및 독립 wheel 소비 검증을 통과했다.
- 공개 audit_html의 list[str] 결과를 int로 반환하는 임시 소비 코드는 mypy가 return-value 오류로 거부했다. optional FastAPI의 런타임 import 위치를 유지하고 py.typed를 패키지에 포함했다.
- Gitleaks 8.30.1의 전체 Git 이력·변경 파일 검사에서 탐지 0건, actionlint 1.7.12 검사 통과. Dependabot의 실제 PR 생성과 원격 보안 job은 미실행이다.
- Starlette/HTTPX의 기존 deprecation 경고는 남아 있다. 브라우저·실기기 검증은 수행하지 않았다.

## 개발 방법론 전달 보강 검증 (2026-11-27)

확인한 공백은 원본 저장소 밖에서 기존 화면 구성과 개발·검증 절차를 읽을 경로가 없다는 점이었다. Codex가 패키지 DEVELOPMENT.md와 읽기 전용 `python -m mobile_foundation.guide`를 제공했다.

- `bash scripts/check-quality.sh` 종료 0: Ruff·strict mypy·테스트 16개·build·독립 wheel 소비 통과.
- FastAPI 없이 wheel과 Jinja만 설치한 별도 환경에서 guide CLI와 DOM 검사 CLI를 실행했다. 현재 guide.py와 DEVELOPMENT.md가 wheel에 같은 바이트로 포함됐는지 확인했다.
- 안내에는 프레임/매크로/토큰 재사용, 앱과 Foundation 소유 경계, 상태별 렌더와 실제 입력 검증, 완료 증거가 포함된다. 실제 브라우저·실기기·시각 검증은 이번 작업에서 수행하지 않았다. 원격 push/새 원격 CI는 미실행이다.

## 릴리스 작업본 검증 (2026-11-27)

0.2.0에서 포맷·타입·렌더·독립 wheel 소비 검사를 통과했다. 기존 매크로 계약은 유지하고 가이드 CLI와 타입 정보를 배포한다.
