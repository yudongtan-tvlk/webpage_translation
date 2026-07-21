import json
import os
import subprocess
from datetime import date, timedelta
from pathlib import Path

import pytest


pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_E2E") != "1", reason="set RUN_E2E=1 to enable"
)


def test_full_flow_th(tmp_path: Path):
    target = (date.today() + timedelta(days=45)).isoformat()
    result = subprocess.run(
        [
            "uv", "run", "webpage-translation",
            "--locale", "th-TH",
            "--date", target,
            "--report-root", str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode in (0, 1, 3), result.stderr
    report_dirs = [
        p for p in tmp_path.iterdir() if p.is_dir() and (p / "index.html").exists()
    ]
    assert report_dirs, "no report dir with index.html created"
    report = report_dirs[0]
    data = json.loads((report / "data.json").read_text(encoding="utf-8"))
    assert 1 <= len(data["pages"]) <= 5  # 1 when homepage failed (stop-on-fail), else 5
