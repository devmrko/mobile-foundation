"""Mobile-first CSS and Jinja components. `install(app, templates)` mounts the static files and makes `mf/*` templates loadable."""

from pathlib import Path

from jinja2 import ChoiceLoader, FileSystemLoader

HERE = Path(__file__).parent
STATIC_DIR = HERE / "static" / "mf"
TEMPLATE_DIR = HERE / "templates"
STATIC_URL = "/static/mf"


def install(app, templates) -> None:
    """Mount `/static/mf` on a FastAPI app and add the foundation templates to a Jinja2Templates instance."""
    from fastapi.staticfiles import StaticFiles

    app.mount(STATIC_URL, StaticFiles(directory=STATIC_DIR), name="mf-static")
    env = templates.env
    env.loader = ChoiceLoader([env.loader, FileSystemLoader(TEMPLATE_DIR)]) if env.loader else FileSystemLoader(TEMPLATE_DIR)
