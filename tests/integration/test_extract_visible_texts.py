from pathlib import Path

import pytest

from webpage_translation.driver.browser import Browser
from webpage_translation.driver.extract import extract_visible_texts


FIXTURE = Path(__file__).parent.parent / "fixtures" / "visible_hidden.html"


@pytest.mark.browser
def test_extract_only_returns_visible(tmp_path: Path):
    browser = Browser()
    browser.new_tab(FIXTURE.resolve().as_uri())
    items = extract_visible_texts(browser)
    texts = {i.text for i in items}
    assert "Hello world" in texts
    assert "Nested visible" in texts
    assert "Ghost text" not in texts
    assert "Invisible" not in texts
    assert "Tiny" not in texts
    assert "Hidden aria only" not in texts
