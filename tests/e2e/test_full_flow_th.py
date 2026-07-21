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
    reports = sorted(tmp_path.iterdir())
    assert reports, "no report dir created"
    index = reports[-1] / "index.html"
    data = json.loads((reports[-1] / "data.json").read_text(encoding="utf-8"))
    assert index.exists()
    assert 1 <= len(data["pages"]) <= 5  # 1 when homepage failed (stop-on-fail), else 5
