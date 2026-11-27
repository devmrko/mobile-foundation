"""Consumer markup mutations must fail even when template rendering succeeds."""

import pytest
from jinja2 import Environment, FileSystemLoader, select_autoescape

from mobile_foundation import TEMPLATE_DIR
from mobile_foundation.quality import audit_html

ENV = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=select_autoescape())


def render(source, **values):
    return ENV.from_string(source).render(**values)


def test_real_gallery_obeys_component_contracts():
    assert audit_html(ENV.get_template("mf/gallery.html").render(), require_frame=True) == []


def test_complete_page_cannot_silently_omit_foundation_frame():
    assert any(issue.startswith("page-frame:") for issue in audit_html("<main>본문</main>", require_frame=True))


@pytest.mark.parametrize("error", [None, "입력 내용을 확인하세요"])
def test_field_states_keep_labels_and_error_links(error):
    html = render(
        '{% import "mf/macros.html" as mf %}{{ mf.field("title", "제목", error=error) }}', error=error
    )
    assert audit_html(html) == []
    assert any("missing-input-label" in issue for issue in audit_html(html.replace('for="f-title"', "")))
    if error:
        assert any("missing-reference" in issue for issue in audit_html(html.replace('id="e-title"', "")))


def test_detail_frame_owns_action_spacing_and_escapes_consumer_content():
    html = render(
        """{% extends "mf/frame_detail.html" %}
{% block topbar %}{{ mf.topbar(title, back_url="/") }}{% endblock %}
{% block content %}{{ title }}{% endblock %}
{% block actions %}{{ mf.button("저장", "primary", disabled=True) }}{% endblock %}""",
        title="<script>bad()</script>",
    )
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert "disabled" in html
    assert audit_html(html) == []
    assert any("bottom-bar-spacing" in issue for issue in audit_html(html.replace(" mf-main--with-bar", "")))


@pytest.mark.parametrize(
    "before,after,rule",
    [
        ("mf-btn mf-btn--primary", "mf-btn--primary", "missing-base-class"),
        ("mf-btn mf-btn--primary", "mf-btn mf-btn--prmary", "unknown-class"),
        ('aria-current="page"', "", "active-tab"),
        ('id="f-url"', 'id="f-bad"', "duplicate-id"),
    ],
)
def test_gallery_mutations_are_rejected(before, after, rule):
    html = ENV.get_template("mf/gallery.html").render()
    assert before in html
    assert any(issue.startswith(rule + ":") for issue in audit_html(html.replace(before, after)))
