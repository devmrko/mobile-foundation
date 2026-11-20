"""Executable form of docs/checklist.md: the numeric rules are enforced against the real CSS files."""

import re
from pathlib import Path

CSS = Path(__file__).parent.parent / "src" / "mobile_foundation" / "static" / "mf"
tokens = (CSS / "tokens.css").read_text()
components = (CSS / "components.css").read_text()


def px(name: str) -> float:
    return float(re.search(rf"--{name}:\s*([\d.]+)px", tokens).group(1))


def block(selector: str) -> str:
    m = re.search(rf"(?:^|\}}|\n){re.escape(selector)}\s*(?:,[^{{]*)?\{{([^}}]*)\}}", components) or re.search(rf"{re.escape(selector)}[^{{]*\{{([^}}]*)\}}", components)
    assert m, f"no rule for {selector}"
    return m.group(1)


def test_touch_target_token_meets_material_and_wcag():
    assert px("mf-target") >= 48 and px("mf-target-gap") >= 8


def test_input_font_size_prevents_ios_zoom():
    assert px("mf-font-input") >= 16
    assert "font-size: var(--mf-font-input)" in block(".mf-input")


def test_every_interactive_component_has_minimum_height():
    for selector in (".mf-btn", ".mf-input", ".mf-tab", ".mf-details > summary", ".mf-topbar__back"):
        body = block(selector)
        assert "var(--mf-target)" in body, f"{selector} lacks the touch target minimum"
    for selector in (".mf-row", ".mf-check"):
        assert re.search(r"min-height:\s*(5\d|[6-9]\d)px", block(selector)), selector


def test_safe_area_and_reduced_motion_present():
    assert "safe-area-inset-bottom" in tokens and "safe-area-inset-top" in tokens
    assert "prefers-reduced-motion" in (CSS / "base.css").read_text()


def hex_rgb(value: str) -> tuple[float, ...]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) / 255 for i in (0, 2, 4))


def luminance(value: str) -> float:
    r, g, b = (c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in hex_rgb(value))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def themes() -> dict[str, dict[str, str]]:
    light = dict(re.findall(r"--(mf-[\w-]+):\s*(#[0-9a-fA-F]{6})", tokens.split("@media")[0]))
    dark = dict(re.findall(r"--(mf-[\w-]+):\s*(#[0-9a-fA-F]{6})", tokens.split(':root[data-theme="dark"]')[1]))
    return {"light": light, "dark": {**light, **dark}}


def test_text_contrast_meets_wcag_aa_in_both_themes():
    for name, t in themes().items():
        for fg in ("mf-text", "mf-text-muted", "mf-ok", "mf-warn", "mf-bad", "mf-info", "mf-primary"):
            for bg in ("mf-bg", "mf-surface"):
                assert contrast(t[fg], t[bg]) >= 4.5, f"{name}: {fg} on {bg} = {contrast(t[fg], t[bg]):.2f}"
        assert contrast(t["mf-on-primary"], t["mf-primary"]) >= 4.5, f"{name}: on-primary"
