import re
import json
from pathlib import Path

from fastapi.routing import APIRoute

from src.deepseek_wrapper.web import app


def _read_api_reference_status_table() -> set[str]:
    readme = Path("docs/api-reference.md").read_text(encoding="utf-8")
    # Capture inline endpoint summary rows like: | ✓ | GET | `/path` |
    paths = set()
    for line in readme.splitlines():
        line = line.strip()
        if line.startswith("|") and "`/" in line and "✓" in line:
            # Extract backticked path(s) from the row
            paths_in_line = re.findall(r"`(/[^`]+)`", line)
            for p in paths_in_line:
                paths.add(p)
    return paths


def _collect_fastapi_paths() -> set[str]:
    paths: set[str] = set()
    for route in app.routes:
        if isinstance(route, APIRoute):
            paths.add(route.path)
    return paths


def test_documented_routes_exist_in_app():
    documented_paths = _read_api_reference_status_table()
    app_paths = _collect_fastapi_paths()
    # Only check the ✓ entries; ignore X roadmap entries by construction
    missing = sorted(p for p in documented_paths if p not in app_paths)
    assert not missing, f"Documented routes not found in app: {missing}"


