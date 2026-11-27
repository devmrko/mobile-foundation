from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient

import mobile_foundation as mf


def make_client() -> TestClient:
    app = FastAPI()
    templates = Jinja2Templates(directory=str(mf.TEMPLATE_DIR))
    mf.install(app, templates)

    @app.get("/", response_class=HTMLResponse)
    def gallery():
        return templates.env.get_template("mf/gallery.html").render()

    return TestClient(app)


def test_gallery_renders_every_component_and_css_is_served():
    client = make_client()
    html = client.get("/").text
    for cls in (
        "mf-topbar",
        "mf-btn--primary",
        "mf-input",
        "mf-row",
        "mf-check",
        "mf-badge--ok",
        "mf-notice--warn",
        "mf-details",
        "mf-steps",
        "mf-steps--compact",
        "mf-copy",
        "mf-input--mono",
        "mf-progress",
        "mf-skeleton",
        "mf-empty",
        "mf-tabbar",
        "mf-error",
    ):
        assert cls in html, cls
    assert 'name="viewport"' in html and "viewport-fit=cover" in html and "user-scalable" not in html
    assert (
        client.get("/static/mf/mobile.css").status_code == 200
        and client.get("/static/mf/components.css").status_code == 200
    )


def test_badge_text_carries_meaning_not_just_colour():
    html = make_client().get("/").text
    assert "신뢰도 높음" in html and "확인 필요" in html
