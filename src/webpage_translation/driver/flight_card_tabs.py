"""Expand each of the four detail tabs on the first flight card and
scrape the resulting panel.

On Traveloka's flight search results, every card has a compact tab row
just below the summary with four labels:

    Flight Details | Fare & Benefits | Refund | Reschedule

Each label is localized (verbatim strings live in the driver's label
map). Clicking a tab reveals a panel of descriptive text inside the
same card. We drive all four tabs on the FIRST card, and — for each
tab — also click any obvious sub-links inside the panel before
scraping (bounded: one click per sub-link, no recursion beyond one
level).
"""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime

from webpage_translation.context import FlowContext
from webpage_translation.driver.actions import wait_for_selector
from webpage_translation.driver.browser import Browser
from webpage_translation.driver.extract import extract_visible_texts
from webpage_translation.qa.types import BBox, PageResult, TextItem

_CARD_CONTAINER = "[data-testid^='flight-inventory-card-container']"

# Labels in target locales. Fallback to English (source-of-truth) when
# the locale isn't in the map — Traveloka often shows the English label
# untranslated anyway (which is exactly the kind of leak we want to
# catch downstream).
_TAB_LABELS: dict[str, dict[str, str]] = {
    "en-SG": {
        "flight_details": "Flight Details",
        "fare_benefits": "Fare & Benefits",
        "refund": "Refund",
        "reschedule": "Reschedule",
    },
    "th-TH": {
        "flight_details": "รายละเอียด",
        "fare_benefits": "ทธิประโยชน์ที่รวมไว้",
        "refund": "การคืนเงิน",
        "reschedule": "เปลี่ยนเที่ยวบิน",
    },
    "id-ID": {
        "flight_details": "Detail Penerbangan",
        "fare_benefits": "Tarif & Manfaat",
        "refund": "Refund",
        "reschedule": "Reschedule",
    },
    "vi-VN": {
        "flight_details": "Chi tiết chuyến bay",
        "fare_benefits": "Giá vé & Ưu đãi",
        "refund": "Hoàn tiền",
        "reschedule": "Đổi lịch",
    },
    "zh-CN": {
        "flight_details": "航班详情",
        "fare_benefits": "价格和权益",
        "refund": "退款",
        "reschedule": "改期",
    },
    "zh-EN": {
        "flight_details": "Flight Details",
        "fare_benefits": "Fare & Benefits",
        "refund": "Refund",
        "reschedule": "Reschedule",
    },
    "ja-JP": {
        "flight_details": "フライト詳細",
        "fare_benefits": "料金・特典",
        "refund": "払い戻し",
        "reschedule": "日程変更",
    },
    "ko-KR": {
        "flight_details": "항공편 상세",
        "fare_benefits": "요금 및 혜택",
        "refund": "환불",
        "reschedule": "일정 변경",
    },
    "ms-MY": {
        "flight_details": "Perincian Penerbangan",
        "fare_benefits": "Tambang & Faedah",
        "refund": "Refund",
        "reschedule": "Reschedule",
    },
}

_TAB_ORDER: tuple[tuple[str, str], ...] = (
    ("flight_details", "Flight Details"),
    ("fare_benefits", "Fare & Benefits"),
    ("refund", "Refund"),
    ("reschedule", "Reschedule"),
)

_MAX_SUBLINK_CLICKS = 6
_CARD_VERTICAL_PAD = 8  # extra px above/below to avoid clipping outlines


def _scroll_first_card_into_view(browser: Browser) -> None:
    """Scroll the first flight card just below the top of the viewport
    so Traveloka's virtualized tab-panel content mounts and paints
    before we capture or extract."""
    card_sel = json.dumps(_CARD_CONTAINER)
    expr = (
        "(function(){"
        f"const card=document.querySelector({card_sel});"
        "if(!card)return null;"
        "const r=card.getBoundingClientRect();"
        "window.scrollTo(0, Math.max(0, r.top + window.scrollY - 80));"
        "return true;"
        "})()"
    )
    browser.eval_json(f"js({expr!r})")
    # Give React/virtualized regions a moment to mount + paint.
    time.sleep(1.2)


def _first_card_document_rect(browser: Browser) -> tuple[float, float, float, float]:
    """Return the (x, y, width, height) rect of the first flight card in
    document space. Height covers everything from the top of the card
    down to the bottom of the currently-expanded tab panel — Traveloka
    renders each card's tab panel inline below the card summary, so the
    panel is the next-sibling block of the card container's grandparent.
    We expand the rect to include any content up to the top of the
    NEXT card container."""
    card_sel = json.dumps(_CARD_CONTAINER)
    expr = (
        "(function(){"
        f"const cards=document.querySelectorAll({card_sel});"
        "if(!cards.length)return null;"
        "const first=cards[0];"
        "const firstR=first.getBoundingClientRect();"
        "const doc=document.documentElement;"
        # Find the next card container: its top is the boundary of the
        # first card's expanded area.
        "let nextTop=doc.scrollHeight;"
        "if(cards.length>1){"
        "const nextR=cards[1].getBoundingClientRect();"
        "nextTop=nextR.top+window.scrollY;"
        "}"
        "return {"
        "x: Math.floor(firstR.left+window.scrollX),"
        "y: Math.floor(firstR.top+window.scrollY),"
        "width: Math.ceil(firstR.width),"
        "height: Math.ceil(nextTop-(firstR.top+window.scrollY))"
        "};"
        "})()"
    )
    rect = browser.eval_json(f"js({expr!r})")
    if not rect:
        raise RuntimeError("no flight card found")
    return (
        float(rect["x"]),
        float(rect["y"]),
        float(rect["width"]),
        float(rect["height"]),
    )


def _clip_texts_to_region(
    texts: tuple[TextItem, ...],
    *,
    rx: float,
    ry: float,
    rw: float,
    rh: float,
) -> tuple[TextItem, ...]:
    """Keep only TextItems whose bbox falls inside [rx, ry, rw, rh],
    translated to region-local coords so they match a region-clipped
    screenshot."""
    out: list[TextItem] = []
    for t in texts:
        tx = t.bbox.x
        ty = t.bbox.y
        tw = t.bbox.w
        th = t.bbox.h
        if tx + tw < rx or tx > rx + rw:
            continue
        if ty + th < ry or ty > ry + rh:
            continue
        out.append(
            TextItem(
                text=t.text,
                selector=t.selector,
                bbox=BBox(x=tx - rx, y=ty - ry, w=tw, h=th),
            )
        )
    return tuple(out)


def _localized_label(locale: str, page_name: str, english: str) -> tuple[str, ...]:
    per_locale = _TAB_LABELS.get(locale, {})
    localized = per_locale.get(page_name)
    if localized is None:
        return (english,)
    if localized == english:
        return (localized,)
    return (localized, english)


def _click_tab_on_first_card(
    browser: Browser, candidate_labels: tuple[str, ...]
) -> bool:
    """Click a tab on the FIRST inventory card whose own text matches
    any of `candidate_labels`. Returns True on success."""
    candidates_js = json.dumps(list(candidate_labels))
    card_sel = json.dumps(_CARD_CONTAINER)
    expr = (
        "(function(){"
        f"const labels={candidates_js};"
        f"const card=document.querySelector({card_sel});"
        "if(!card)return false;"
        # Traveloka renders the tab row just below the card container;
        # we look at siblings, parent, and grandparent to find it.
        "const roots=[card,card.parentElement,card.parentElement&&card.parentElement.parentElement].filter(Boolean);"
        "for(const root of roots){"
        "for(const el of root.querySelectorAll('*')){"
        "let ot='';for(const c of el.childNodes)if(c.nodeType===3)ot+=c.nodeValue;"
        "ot=ot.trim();"
        "if(labels.indexOf(ot)>=0){"
        "const r=el.getBoundingClientRect();"
        "if(r.width<5||r.height<5)continue;"
        "el.click();"
        "return true;"
        "}}}return false;"
        "})()"
    )
    result = browser.eval_json(f"js({expr!r})")
    return bool(result)


def _click_sublinks_in_panel(browser: Browser) -> int:
    """Click cursor:pointer inline elements that are clearly interactive
    (Learn more, See all, See details, Read more, terms, policy, ...)
    within the current viewport near the just-expanded tab panel.
    Returns the number of successful clicks (bounded)."""
    max_clicks = _MAX_SUBLINK_CLICKS
    expr = (
        "(function(){"
        "const pat=/learn more|see all|see details|more info|full policy|read more|see terms|terms & conditions|view details|more$|details$|policy$|see policy/i;"
        "const hits=[];"
        "for(const el of document.querySelectorAll('a,button,[role=\"button\"],[data-testid]')){"
        "const style=getComputedStyle(el);"
        "if(style.display==='none'||style.visibility==='hidden')continue;"
        "let ot='';for(const c of el.childNodes)if(c.nodeType===3)ot+=c.nodeValue;"
        "ot=ot.trim();"
        "if(!ot||ot.length>40)continue;"
        "if(!pat.test(ot))continue;"
        "const r=el.getBoundingClientRect();"
        "if(r.width<5||r.height<5)continue;"
        "hits.push({text:ot,x:r.x+r.width/2,y:r.y+r.height/2});"
        "}"
        f"return hits.slice(0,{max_clicks});"
        "})()"
    )
    hits = browser.eval_json(f"js({expr!r})")
    if not hits:
        return 0
    clicked = 0
    for hit in hits:
        text = str(hit.get("text", "")).strip()
        if not text:
            continue
        # Re-locate by exact text right before clicking so a re-render
        # doesn't leave us clicking on stale coordinates.
        text_js = json.dumps(text)
        click_expr = (
            "(function(){"
            f"const lbl={text_js};"
            "for(const el of document.querySelectorAll('a,button,[role=\"button\"],[data-testid]')){"
            "let ot='';for(const c of el.childNodes)if(c.nodeType===3)ot+=c.nodeValue;"
            "if(ot.trim()!==lbl)continue;"
            "const r=el.getBoundingClientRect();"
            "if(r.width<5||r.height<5)continue;"
            "el.click();return true;"
            "}return false;"
            "})()"
        )
        did = browser.eval_json(f"js({click_expr!r})")
        if did:
            clicked += 1
            time.sleep(0.6)
    return clicked


def _scrape_tab(
    browser: Browser,
    ctx: FlowContext,
    *,
    page_name: str,
    english_label: str,
) -> PageResult:
    ctx.screenshots_dir.mkdir(parents=True, exist_ok=True)
    shot = ctx.screenshots_dir / f"{page_name}.png"
    url = "https://www.traveloka.com/flight/search#" + page_name
    error: str | None = None
    texts: tuple[TextItem, ...] = ()
    try:
        wait_for_selector(browser, _CARD_CONTAINER, timeout=30)
        _scroll_first_card_into_view(browser)
        candidates = _localized_label(ctx.locale, page_name, english_label)
        if not _click_tab_on_first_card(browser, candidates):
            raise RuntimeError(
                f"tab {page_name!r} (labels {candidates!r}) not found on first card"
            )
        time.sleep(1.2)  # let the panel finish animating in
        _click_sublinks_in_panel(browser)
        time.sleep(0.6)
        # Re-scroll: the panel change may have shifted the card, and we
        # need the card + panel in the viewport so virtualized regions
        # actually mount and paint.
        _scroll_first_card_into_view(browser)
        full_texts = extract_visible_texts(browser, reset_scroll=False)
        rx, ry, rw, rh = _first_card_document_rect(browser)
        pad = _CARD_VERTICAL_PAD
        ry = max(0.0, ry - pad)
        rh = rh + 2 * pad
        texts = _clip_texts_to_region(full_texts, rx=rx, ry=ry, rw=rw, rh=rh)
        browser.screenshot_region(shot, x=rx, y=ry, width=rw, height=rh)
    except Exception as exc:
        error = f"{page_name} failed: {exc}"
    return PageResult(
        name=page_name,
        url=url,
        timestamp=datetime.now(UTC).isoformat(timespec="seconds"),
        texts=texts,
        screenshot=shot if shot.exists() else None,
        error=error,
    )


def scrape_all_tabs(browser: Browser, ctx: FlowContext) -> list[PageResult]:
    """Return one PageResult per detail tab on the first inventory card."""
    return [
        _scrape_tab(browser, ctx, page_name=name, english_label=english)
        for name, english in _TAB_ORDER
    ]
