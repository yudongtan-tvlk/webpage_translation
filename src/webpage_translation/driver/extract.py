from __future__ import annotations

from typing import Any

from webpage_translation.driver.browser import Browser
from webpage_translation.qa.types import BBox, TextItem


EXTRACT_JS: str = r"""
(function () {
  function selectorFor(el) {
    if (el.id) return '#' + CSS.escape(el.id);
    const parts = [];
    while (el && el.nodeType === 1 && parts.length < 6) {
      let part = el.nodeName.toLowerCase();
      if (el.classList && el.classList.length) part += '.' + [...el.classList].map(CSS.escape).join('.');
      const parent = el.parentElement;
      if (parent) {
        const sibs = [...parent.children].filter(c => c.nodeName === el.nodeName);
        if (sibs.length > 1) part += ':nth-of-type(' + (sibs.indexOf(el) + 1) + ')';
      }
      parts.unshift(part);
      el = el.parentElement;
    }
    return parts.join(' > ');
  }
  function ownText(el) {
    let s = '';
    for (const n of el.childNodes) {
      if (n.nodeType === 3) s += n.nodeValue;
    }
    return s.replace(/\s+/g, ' ').trim();
  }
  const out = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
  let node = walker.currentNode;
  while (node) {
    const text = ownText(node);
    if (text) {
      const style = getComputedStyle(node);
      if (style.display !== 'none' && style.visibility !== 'hidden' && style.visibility !== 'collapse' && parseFloat(style.opacity || '1') > 0) {
        const r = node.getBoundingClientRect();
        if (r.width > 0 && r.height > 0) {
          out.push({
            text,
            selector: selectorFor(node),
            bbox: { x: r.x + window.scrollX, y: r.y + window.scrollY, w: r.width, h: r.height },
          });
        }
      }
    }
    node = walker.nextNode();
  }
  return out;
})()
"""


def extract_visible_texts(browser: Browser) -> tuple[TextItem, ...]:
    browser.run("js('window.scrollTo(0, 0)')\nimport time; time.sleep(0.2)\n")
    raw: list[dict[str, Any]] = browser.eval_json(f"js({EXTRACT_JS!r})")
    items: list[TextItem] = []
    for row in raw:
        b = row["bbox"]
        items.append(
            TextItem(
                text=str(row["text"]),
                selector=str(row["selector"]),
                bbox=BBox(x=float(b["x"]), y=float(b["y"]), w=float(b["w"]), h=float(b["h"])),
            )
        )
    return tuple(items)


def max_content_bottom(texts: tuple[TextItem, ...]) -> float:
    if not texts:
        return 0.0
    return max(t.bbox.y + t.bbox.h for t in texts)
