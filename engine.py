"""Rule-based news engine: fetch -> de-duplicate -> tag -> score -> summarise -> explain.

No AI is used. Summaries are trimmed from the publisher's own text, and every
"why it matters" line comes from the editable table in rules.json.
"""
import html
import json
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import requests

BASE = Path(__file__).parent
UA = {"User-Agent": "Mozilla/5.0 (GlobalBrief personal dashboard)"}

STOP = set(
    "a an the of to in on for and or at by with as is are was were be been from after before "
    "over under into about amid says say said new news live update updates latest has have "
    "will its their his her this that than more less".split()
)


@dataclass
class Item:
    title: str
    link: str
    source: str
    published: datetime
    summary: str = ""
    entities: tuple = ()
    image: str = ""


# ----------------------------------------------------------------- loading
def load_json(name):
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def clean_text(s):
    s = html.unescape(re.sub(r"<[^>]+>", " ", s or ""))
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------- fetching
_IMG_SRC = re.compile(r'<img[^>]+src=["\'](https://[^"\']+)["\']', re.I)


def _image(e):
    """The best https picture the publisher puts in its feed (the largest one if several)."""
    best, best_w = "", -1
    for key in ("media_content", "media_thumbnail"):
        for m in e.get(key) or []:
            u = m.get("url", "")
            if not u.startswith("https://") or str(m.get("type", "image/")).startswith(("video", "audio")):
                continue
            try:
                w = int(m.get("width") or 0)
            except (TypeError, ValueError):
                w = 0
            if w > best_w:
                best, best_w = u, w
    if best:
        return best
    for enc in e.get("enclosures") or []:
        if str(enc.get("type", "")).startswith("image") and str(enc.get("href", "")).startswith("https://"):
            return enc["href"]
    blob = (e.get("summary") or "") + " ".join(c.get("value", "") for c in (e.get("content") or []))
    m = _IMG_SRC.search(blob)
    return m.group(1) if m else ""


def _fetch_one(feed, cutoff, per_feed):
    try:
        r = requests.get(feed["url"], headers=UA, timeout=12)
        r.raise_for_status()
        parsed = feedparser.parse(r.content)
        if not parsed.entries:
            raise ValueError("no entries")
    except Exception:
        return [], feed["name"]

    is_google = "news.google.com" in feed["url"]
    items = []
    for e in parsed.entries[:per_feed]:
        title = clean_text(e.get("title"))
        link = e.get("link", "")
        if not title or not link.startswith(("http://", "https://")):
            continue
        source = feed["name"]
        if is_google:
            # Google News puts the real publisher in <source> and in the title suffix.
            pub = clean_text((e.get("source") or {}).get("title"))
            if pub:
                source = pub
                suffix = " - " + pub
                if title.endswith(suffix):
                    title = title[: -len(suffix)]
        t = e.get("published_parsed") or e.get("updated_parsed")
        published = datetime(*t[:6], tzinfo=timezone.utc) if t else datetime.now(timezone.utc)
        if published < cutoff:
            continue
        # Google's "summary" is just a list of related links, so it is not used.
        summary = "" if is_google else clean_text(e.get("summary"))[:900]
        items.append(Item(title, link, source, published, summary, image="" if is_google else _image(e)))
    return items, None


def fetch_feeds(feeds, max_age_hours=48, per_feed=40):
    """Fetch all feeds in parallel. Returns (items, names_of_feeds_that_failed)."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    items, failed = [], []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for got, err in pool.map(lambda f: _fetch_one(f, cutoff, per_feed), feeds):
            items.extend(got)
            if err:
                failed.append(err)
    return items, failed


# ------------------------------------------------------------------ rules
def compile_terms(terms):
    """Whole-word matchers. Short ALL-CAPS terms (US, RBI, EU) are case-sensitive."""
    out = []
    for t in terms:
        case_sensitive = t.isupper() and len(t) <= 4
        pat = r"(?<![A-Za-z0-9])" + re.escape(t) + r"(?![A-Za-z0-9])"
        out.append(re.compile(pat, 0 if case_sensitive else re.I))
    return out


def _count(patterns, text):
    return sum(1 for p in patterns if p.search(text))


class Rules:
    def __init__(self, data):
        self.d = data
        self.cats = {k: compile_terms(v) for k, v in data["categories"].items()}
        self.regions = {k: compile_terms(v) for k, v in data["regions"].items()}
        self.severity_terms = [(compile_terms([t])[0], w) for t, w in data["severity"].items()]
        self.ignore = compile_terms(data.get("ignore", []))
        self.impact = [(r, [compile_terms(g) for g in r["when_all"]]) for r in data["impact_rules"]]
        self.scoring = data.get("scoring", {"high": 14, "med": 9})

    def is_ignored(self, title):
        return _count(self.ignore, title) > 0

    def tag(self, title, summary):
        """Return (categories ordered by strength, regions). A title hit counts double."""
        cats = {}
        for name, pats in self.cats.items():
            s = 2 * _count(pats, title) + _count(pats, summary)
            if s >= 2:
                cats[name] = s
        regs = []
        for name, pats in self.regions.items():
            if 2 * _count(pats, title) + _count(pats, summary) >= 2:
                regs.append(name)
        return sorted(cats, key=cats.get, reverse=True), regs

    def severity(self, title):
        return min(6, sum(w for p, w in self.severity_terms if p.search(title)))

    def explain(self, title):
        """First matching impact rule wins (order in rules.json = priority)."""
        for rule, groups in self.impact:
            if all(any(p.search(title) for p in g) for g in groups):
                return rule["text"], rule.get("affects", [])
        return None, []


def load_rules():
    return Rules(load_json("rules.json"))


# ------------------------------------------------------------- summaries
_TAIL = re.compile(r"\s*(The post .*? appeared first on .*|Read more.*|Continue reading.*|\[…\]|\[\.\.\.\])$", re.I)


def _norm_tokens(s):
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 2}


def summarize(summary, title, max_words=60, min_words=10):
    """Trim the publisher's own text to about 60 words. Returns '' if there is nothing useful."""
    s = _TAIL.sub("", clean_text(summary)).strip()
    if not s:
        return ""
    if s.lower().startswith(title.lower()):
        s = s[len(title):].lstrip(" -:–—.")
    if len(s.split()) < min_words:
        return ""
    a, b = _norm_tokens(s), _norm_tokens(title)
    if a and b and len(a & b) / len(a | b) > 0.8:  # summary is just the headline again
        return ""
    out, n = [], 0
    for sent in re.split(r"(?<=[.!?])\s+", s):
        w = len(sent.split())
        if n + w > max_words:
            if not out:
                out.append(" ".join(sent.split()[:max_words]).rstrip(",;:") + "…")
            break
        out.append(sent)
        n += w
        if n >= 32:
            break
    return " ".join(out)


def key_points(short, max_points=3, max_words=26):
    """Up to 3 short bullet points taken from the trimmed summary."""
    pts = []
    for sent in re.split(r"(?<=[.!?])\s+", short or ""):
        words = sent.split()
        if len(words) < 4:
            continue
        if len(words) > max_words:
            sent = " ".join(words[:max_words]).rstrip(",;:") + "…"
        pts.append(sent.strip())
        if len(pts) == max_points:
            break
    return pts


_FACT = re.compile(
    r"(?:(?:₹|Rs\.?|US\$|\$|€|£)\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:crore|lakh|million|billion|trillion|bn|mn|tn|%))?)"
    r"|(?:\d[\d,]*(?:\.\d+)?\s?(?:%|per cent|percent|crore|lakh|million|billion|trillion))",
    re.I,
)


def facts(text, limit=3):
    """Key figures such as 12%, $82.40 or 5 crore, shown as small tags on the card."""
    out = []
    for m in _FACT.finditer(text or ""):
        f = re.sub(r"\s+", " ", m.group(0)).strip(" .,")
        if f.lower() not in [x.lower() for x in out]:
            out.append(f)
        if len(out) == limit:
            break
    return out


# ------------------------------------------------------------- clustering
def tokens(title):
    return {w for w in re.findall(r"[a-z0-9']+", title.lower()) if w not in STOP and len(w) > 2}


def cluster(items):
    """Group near-identical headlines from different outlets (greedy, newest first)."""
    clusters = []
    for it in sorted(items, key=lambda i: i.published, reverse=True):
        t = tokens(it.title)
        for c in clusters:
            inter = len(t & c["tokens"])
            union = len(t | c["tokens"]) or 1
            j = inter / union
            if (inter >= 3 and j >= 0.4) or (inter >= 2 and j >= 0.6):
                c["items"].append(it)
                break
        else:
            clusters.append({"tokens": t, "items": [it]})
    return [c["items"] for c in clusters]


# ---------------------------------------------------------------- stories
def ago(age_h):
    if age_h < 1:
        return f"{max(1, int(age_h * 60))}m ago"
    if age_h < 48:
        return f"{int(age_h)}h ago"
    return f"{int(age_h // 24)}d ago"


_INDIA = re.compile(r"\bIndia(n)?\b")


def build_stories(items, rules, watch=None, now=None, limit=150):
    now = now or datetime.now(timezone.utc)
    stories = []
    for group in cluster(items):
        rep = group[0]  # most recent
        if rules.is_ignored(rep.title):
            continue
        short = max((summarize(i.summary, rep.title) for i in group), key=len, default="")
        raw = max((i.summary for i in group), key=len, default="")
        img_item = next((i for i in group if i.image), None)
        cats, regs = rules.tag(rep.title, raw)
        primary = cats[0] if cats else "World"

        ents = set()
        for i in group:
            ents |= set(i.entities)
        if watch:
            ents |= set(watch.match(rep.title + " " + raw))
        ents = [n for n in (watch.order if watch else []) if n in ents]
        groups = watch.groups_of(ents) if watch else []

        sources = sorted({i.source for i in group})
        age_h = max(0.0, (now - rep.published).total_seconds() / 3600)
        score = min(len(sources), 6) * 3 + max(0.0, 4 - age_h / 6) + rules.severity(rep.title)
        if groups:
            score += 3  # things on your sir's watch list come first
            if _INDIA.search(rep.title + " " + raw):
                score += 2
        impact = "HIGH" if score >= rules.scoring["high"] else "MED" if score >= rules.scoring["med"] else ""
        why, affects = rules.explain(rep.title)
        stories.append(
            {
                "title": rep.title,
                "link": rep.link,
                "short": short,
                "points": key_points(short),
                "facts": facts(rep.title + " " + raw),
                "image": img_item.image if img_item else "",
                "credit": img_item.source if img_item else "",
                "sources": sources,
                "n_sources": len(sources),
                "published": rep.published,
                "ts": int(rep.published.timestamp()),
                "age_h": age_h,
                "ago": ago(age_h),
                "cats": cats or ["World"],
                "primary": primary,
                "regions": regs,
                "entities": ents,
                "groups": groups,
                "score": round(score, 1),
                "impact": impact,
                "why": why if affects else None,
                "affects": affects,
            }
        )
    stories.sort(key=lambda s: (s["score"], s["published"]), reverse=True)
    return stories[:limit]


def is_india(s):
    """A story belongs on the India tab if it names an Indian leader/party or is mainly about India."""
    return bool({"maharashtra", "leaders"} & set(s["groups"])) or "India" in s["regions"] or s["primary"] == "India"


def _pick(cands, cfg, min_score):
    """cands are sorted best first. Fresh stories plus the day's best few, at most per_topic per topic."""
    fresh_h, top_n = cfg.get("fresh_hours", 3), cfg.get("top_of_day", 3)
    window, total, per = cfg.get("top_window_hours", 24), cfg.get("total", 20), cfg.get("per_topic", 5)
    good = [s for s in cands if s["score"] >= min_score and s["age_h"] <= window]
    topday = {id(s) for s in good[:top_n]}
    out, counts = [], {}
    for s in good:
        if s["age_h"] > fresh_h and id(s) not in topday:
            continue
        topic = s["groups"][0] if s["groups"] else s["primary"]
        if counts.get(topic, 0) >= per:
            continue
        counts[topic] = counts.get(topic, 0) + 1
        out.append(dict(s, topday=id(s) in topday))
        if len(out) >= total:
            break
    return out


def select_tabs(stories, rules):
    """World (no India stories) and India, each with its own best list."""
    cfg = rules.d.get("selection", {})
    min_score = cfg.get("min_score", rules.scoring["med"])
    ind = [s for s in stories if is_india(s)]
    wor = [s for s in stories if not is_india(s)]
    return {"world": _pick(wor, cfg, min_score), "india": _pick(ind, cfg, min_score)}


def link_markets(prices, stories, rules):
    """If an asset moved a lot, point to the strongest related recent story.
    This is a time-based match, not proof of cause, and the page says so."""
    cfg = rules.d["market_links"]
    out = []
    for p in prices:
        chg = p.get("chg")
        if chg is None or abs(chg) < cfg["thresholds"].get(p["key"], 1.5):
            continue
        wanted = set(cfg["asset_categories"].get(p["key"], []))
        cands = [s for s in stories if wanted & set(s["cats"]) and s["age_h"] <= cfg["window_hours"]]
        if cands:
            terms = compile_terms(cfg.get("asset_terms", {}).get(p["key"], []))
            # A story that names the asset itself beats a merely related one.
            best = max(cands, key=lambda s: s["score"] + (8 if _count(terms, s["title"]) else 0))
            out.append({"label": p["label"], "chg_fmt": p["chg_fmt"], "dir": p["dir"], "story": best})
    return out
