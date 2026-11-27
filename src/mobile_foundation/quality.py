"""Check rendered Foundation markup; this is not a browser or a WCAG audit."""

import argparse
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

from mobile_foundation import STATIC_DIR

VOID = frozenset(
    [
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    ]
)


class Markup(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.nodes = []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        node = {"tag": tag, "attrs": dict(attrs), "parents": tuple(self.stack)}
        self.nodes.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.stack.pop()

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index]["tag"] == tag:
                del self.stack[index:]
                break


def classes(node):
    return set((node["attrs"].get("class") or "").split())


def audit_html(html: str, *, require_frame: bool = False) -> list[str]:
    """Return deterministic violations of the bundled mf component contracts.

    Pass a complete rendered page to validate ID references and bottom-bar spacing.
    Custom application classes should use a prefix other than the reserved mf- prefix.
    """
    parser = Markup()
    parser.feed(html)
    parser.close()
    nodes = parser.nodes
    issues = []
    identifiers = Counter(n["attrs"]["id"] for n in nodes if n["attrs"].get("id"))
    for name, count in identifiers.items():
        if count > 1:
            issues.append(f"duplicate-id: {name}")
    # The secondary variant intentionally inherits the base button styling.
    known = {"mf-btn--secondary"}
    for path in STATIC_DIR.glob("*.css"):
        known.update(re.findall(r"\.(mf-[a-zA-Z0-9_-]+)", path.read_text()))
    for node in nodes:
        attrs = node["attrs"]
        own = classes(node)
        for name in sorted(own):
            if name.startswith("mf-") and name not in known:
                issues.append(f"unknown-class: {name}")
            if name.startswith("mf-") and "--" in name:
                base = name.split("--", 1)[0]
                if base not in own:
                    issues.append(f"missing-base-class: {name} requires {base}")
        refs = (attrs.get("aria-describedby") or "").split()
        if node["tag"] == "label" and attrs.get("for"):
            refs.append(attrs["for"])
        for ref in refs:
            if ref not in identifiers:
                issues.append(f"missing-reference: {ref}")
        if "mf-input" in own:
            name = attrs.get("id")
            if not name or not any(n["tag"] == "label" and n["attrs"].get("for") == name for n in nodes):
                issues.append("missing-input-label: mf-input requires an id and associated label")
            if attrs.get("aria-invalid") == "true" and not attrs.get("aria-describedby"):
                issues.append("missing-error-description: invalid mf-input")
        if "mf-tabbar" in own:
            tabs = [n for n in nodes if "mf-tab" in classes(n) and any(p is node for p in n["parents"])]
            if not 3 <= len(tabs) <= 5:
                issues.append("tab-count: mf-tabbar requires 3 to 5 destinations")
            if sum(n["attrs"].get("aria-current") == "page" for n in tabs) != 1:
                issues.append("active-tab: mf-tabbar requires exactly one current page")
    mains = [n for n in nodes if "mf-main" in classes(n)]
    if require_frame and len(mains) != 1:
        issues.append("page-frame: a complete Foundation page requires exactly one mf-main")
    if (
        mains
        and any(classes(n) & {"mf-tabbar", "mf-actionbar"} for n in nodes)
        and any("mf-main--with-bar" not in classes(n) for n in mains)
    ):
        issues.append("bottom-bar-spacing: mf-main requires mf-main--with-bar")
    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pages", nargs="+", type=Path, help="Rendered UTF-8 HTML, not template source")
    args = parser.parse_args()
    failed = False
    for page in args.pages:
        try:
            issues = audit_html(page.read_text(encoding="utf-8"), require_frame=True)
        except OSError as error:
            parser.exit(2, f"{page}: {error}\n")
        for issue in issues:
            print(f"{page}: {issue}")
        failed = failed or bool(issues)
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
