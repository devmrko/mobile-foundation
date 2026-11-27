# mobile-foundation

모바일 우선 CSS 토큰, 컴포넌트 클래스(`mf-*`), Jinja 매크로. 점검표(docs/checklist.md)의 숫자 규칙은 테스트로 집행한다.

- `static/mf/{tokens,base,components}.css` + `mobile.css`(셋을 import). React 앱은 CSS만 가져가 같은 클래스를 쓴다.
- `templates/mf/macros.html`: topbar, button, field, row, check_row, badge, notice, details, card, steps(compact), copy_field, progress, skeleton_lines, empty, youtube, tabbar, actionbar. `base.html`은 레이아웃 틀, `gallery.html`은 전체 구경.
- FastAPI: `mobile_foundation.install(app, templates)` → `/static/mf` 마운트 + `mf/*` 템플릿 로드.

```python
templates = Jinja2Templates(directory="templates")
mobile_foundation.install(
    app, templates
)  # then {% extends "mf/base.html" %} and {% import "mf/macros.html" as mf %}
```

상태: 0.3.0. receipe가 첫 사용처이며, 쓰면서 클래스를 다듬는다. 실기기(iOS/Android) 검증과 React 대응(컴포넌트 JSX)은 아직 없다.

## 공통 품질 검사

공통 구성을 사용하면서 필수 검증이 빠지는 문제를 줄이기 위해 `bash scripts/check-quality.sh`를 실행합니다. 기술별 적용 범위와 수동 확인 항목은 [품질 계약](docs/design/quality-contract.md)에 정리했습니다.

검사에는 Ruff 린트·포맷, mypy, 테스트, wheel 소비 검증이 포함됩니다. 포맷 수정은 `./uvw run ruff format .`로 실행합니다.

GitHub 설정에는 주간 Dependabot 업데이트 제안과 Gitleaks 이력 검사가 포함됩니다. 기본 브랜치에 반영한 뒤 실행되며 자동 병합은 하지 않습니다.

개발 시 재사용할 구성과 변경·검증 순서는 [개발 절차](src/mobile_foundation/DEVELOPMENT.md)에 있습니다.
설치된 패키지에서도 `python -m mobile_foundation.guide`로 같은 안내를 읽을 수 있습니다.

## 배포 버전

현재 배포 버전은 0.2.0입니다. 화면은 기존 프레임을 extends하고 매크로·토큰을 조합해 만듭니다. 앱별 업무 흐름·문구는 앱에 유지하며 공통 레이아웃 결함은 원본 Foundation에서 수정합니다. GitHub Release에 wheel/sdist를 제공합니다.

## 점검·배포 중 안내

앱이 중단되어도 정적 안내와 API JSON 503을 제공하는 공통 도구를 포함합니다. 계획된 점검 전환과 열린 화면의 입력 보존 도우미는 [배포 안내](docs/maintenance.md)를 따릅니다.
