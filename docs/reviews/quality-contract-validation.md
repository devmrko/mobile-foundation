# 공통 품질 계약 적용 검증

2026-11-27, 현재 로컬 작업 트리에서 Codex가 실행한 원본 검증 기록이다. 기존 진행 중 변경은 보존했다. 원격 CI 실행·릴리스·소비 프로젝트 일괄 업그레이드는 수행하지 않았다.

- Python 3.13.16에서 `UV_BIN=/Users/joungmin/devkit/workspace/python-foundation/.tools/uv/bin/uv bash scripts/check-quality.sh`를 실행했다. UV_BIN은 이번 환경의 실행 도구 경로이며 기본 명령은 uv 또는 저장소 uvw를 사용한다.
- 전체 검사 명령 종료 0. lint 및 실제 CSS·렌더·누락 변형 테스트 16개 통과.
- wheel/sdist를 빌드하고 소스 경로 없이 새 venv의 wheel로 gallery/CSS/quality API와 CLI를 사용했다.
- 코드로 확인한 것은 렌더된 DOM 계약과 CSS 수치다. 스크린샷 비교, 브라우저 수동 관찰, 실제 휴대폰 검증은 이번 작업에서 실행하지 않았다.
- Starlette TestClient의 HTTPX deprecation 경고를 숨기지 않았다.
