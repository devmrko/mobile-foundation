# mobile-foundation

모바일 우선 CSS 토큰, 컴포넌트 클래스(`mf-*`), Jinja 매크로. 점검표(docs/checklist.md)의 숫자 규칙은 테스트로 집행한다.

- `static/mf/{tokens,base,components}.css` + `mobile.css`(셋을 import). React 앱은 CSS만 가져가 같은 클래스를 쓴다.
- `templates/mf/macros.html`: topbar, button, field, row, check_row, badge, notice, details, card, steps(compact), copy_field, progress, skeleton_lines, empty, youtube, tabbar, actionbar. `base.html`은 레이아웃 틀, `gallery.html`은 전체 구경.
- FastAPI: `mobile_foundation.install(app, templates)` → `/static/mf` 마운트 + `mf/*` 템플릿 로드.

```python
templates = Jinja2Templates(directory="templates")
mobile_foundation.install(app, templates)   # then {% extends "mf/base.html" %} and {% import "mf/macros.html" as mf %}
```

상태: 0.1.0 초안. receipe가 첫 사용처이며, 쓰면서 클래스를 다듬는다. 실기기(iOS/Android) 검증과 React 대응(컴포넌트 JSX)은 아직 없다.
