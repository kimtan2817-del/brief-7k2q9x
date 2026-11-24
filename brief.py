"""Collects everything the page needs (news, prices, comparisons, funds, FD rates)."""
import crawl
import demo_data
import engine
import history
import layout
import markets
import mf
from watch import Watch


def _fd():
    fd = engine.load_json("fd_rates.json")
    terms = []
    for b in fd["banks"]:
        for t in b["rates"]:
            if t not in terms:
                terms.append(t)
    fd["terms"] = terms
    fd["filled"] = bool(fd.get("as_of")) and any(v is not None for b in fd["banks"] for v in b["rates"].values())
    return fd


def collect(demo=False):
    rules = engine.load_rules()  # re-read each time, so edits apply without a restart
    watch = Watch(engine.load_json("watch.json"))
    notes = []
    if demo:
        items, failed = demo_data.items(), []
        prices, (commodities, rupee) = demo_data.prices(), demo_data.history_data()
        funds, fd = demo_data.funds(), demo_data.fd()
    else:
        items, failed = engine.fetch_feeds(engine.load_json("feeds.json"))
        w_items, w_failed, w_total = watch.fetch()
        items = items + w_items
        if w_failed:
            notes.append(f"{w_failed} of {w_total} name searches could not be reached")
        prices = markets.fetch_prices()
        commodities, rupee = history.fetch()
        funds = mf.fetch(engine.load_json("funds.json"))
        fd = _fd()
    stories = engine.build_stories(items, rules, watch=watch)
    for s in stories:
        s["icon"] = layout.CAT_ICONS.get(s["primary"], layout.CAT_ICONS["World"])
    tabs = engine.select_tabs(stories, rules)
    if not demo:
        try:  # open the articles of headline-only cards and fill them with real text
            n = crawl.enrich(tabs["world"] + tabs["india"])
            if n:
                notes.append(f"{n} cards filled from the article text")
        except Exception as ex:
            notes.append(f"article filling skipped: {ex}")
    return {
        "stories": stories,
        "world": tabs["world"],
        "india": tabs["india"],
        "show_first": rules.d.get("selection", {}).get("show_first", 10),
        "prices": prices,
        "links": engine.link_markets(prices, stories, rules),
        "commodities": commodities,
        "rupee": rupee,
        "funds": funds,
        "fd": fd,
        "failed": failed,
        "notes": notes,
        "watch": watch,
    }
