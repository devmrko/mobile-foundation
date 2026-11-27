"""Verify packaged CSS/templates/quality API without source-tree imports."""

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uv", default="uv")
    args = parser.parse_args()
    wheels = list((ROOT / "dist").glob("mobile_foundation-*.whl"))
    if len(wheels) != 1:
        parser.error("Build exactly one current mobile-foundation wheel in dist first")
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    with tempfile.TemporaryDirectory(prefix="mobile-foundation-consumer-") as temporary:
        base = Path(temporary)
        venv = base / "venv"
        subprocess.run([args.uv, "venv", "--python", sys.executable, str(venv)], check=True)
        python = venv / "bin/python"
        subprocess.run([args.uv, "pip", "install", "--python", str(python), str(wheels[0])], check=True)
        code = """
from pathlib import Path
import sys
from jinja2 import Environment, FileSystemLoader, select_autoescape
import mobile_foundation as mf
from mobile_foundation.quality import audit_html
assert Path(mf.__file__).is_relative_to(Path(sys.prefix))
env = Environment(loader=FileSystemLoader(mf.TEMPLATE_DIR), autoescape=select_autoescape())
html = env.get_template('mf/gallery.html').render()
assert audit_html(html) == [], audit_html(html)
assert (mf.STATIC_DIR / 'mobile.css').is_file()
assert (mf.STATIC_DIR / 'tokens.css').is_file()
assert (mf.STATIC_DIR / 'components.css').is_file()
Path('page.html').write_text(html)
"""
        subprocess.run([str(python), "-c", code], check=True, cwd=base, env=env)
        guide = subprocess.run(
            [str(python), "-m", "mobile_foundation.guide"],
            check=True,
            cwd=base,
            env=env,
            capture_output=True,
            text=True,
        )
        assert "mf/frame_tabs.html" in guide.stdout and "mobile_foundation.quality" in guide.stdout
        subprocess.run(
            [str(python), "-m", "mobile_foundation.quality", "page.html"], check=True, cwd=base, env=env
        )
        print("PASS installed wheel: packaged guide/templates/CSS and rendered markup contract")


if __name__ == "__main__":
    main()
