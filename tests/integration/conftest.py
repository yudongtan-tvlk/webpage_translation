import os
import pytest


def pytest_collection_modifyitems(config, items):
    if os.environ.get("RUN_BROWSER_TESTS") == "1":
        return
    skip = pytest.mark.skip(reason="set RUN_BROWSER_TESTS=1 to enable")
    for item in items:
        if "browser" in item.keywords:
            item.add_marker(skip)
