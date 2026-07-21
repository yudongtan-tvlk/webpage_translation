from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader, select_autoescape


def _basename(value: str | None) -> str:
    if not value:
        return ""
    return Path(value).name


def _env() -> Environment:
    env = Environment(
        loader=PackageLoader("webpage_translation.report", "templates"),
        autoescape=select_autoescape(["html", "j2"]),
    )
    env.filters["basename"] = _basename
    return env


def render_report(output_dir: Path, payload: dict[str, Any]) -> Path:
    if output_dir.exists():
        raise FileExistsError(f"report dir already exists: {output_dir}")
    output_dir.mkdir(parents=True)
    shots_dir = output_dir / "screenshots"
    shots_dir.mkdir()
    for page in payload["pages"]:
        shot = page["page"].get("screenshot")
        if shot:
            src = Path(shot)
            if src.exists():
                shutil.copy2(src, shots_dir / src.name)
    env = _env()
    html = env.get_template("index.html.j2").render(payload=payload)
    index = output_dir / "index.html"
    index.write_text(html, encoding="utf-8")
    return index
