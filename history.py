"""Long-term comparisons for commodities and the rupee ("then vs now").

Uses Yahoo Finance's public chart endpoint (monthly prices for 10 years, no key).
It is unofficial, so it can fail; whatever cannot be fetched is simply left out.
"""
from concurrent.futures import ThreadPoolExecutor

import requests

UA = {"User-Agent": "Mozilla/5.0 (GlobalBrief personal dashboard)"}
URL = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=10y&interval=1mo"

COMMODITIES = [
    ("gold", "Gold", "USD / ounce", "GC=F"),
    ("silver", "Silver", "USD / ounce", "SI=F"),
    ("brent", "Brent crude", "USD / barrel", "BZ=F"),
    ("wti", "WTI crude", "USD / barrel", "CL=F"),
    ("natgas", "Natural gas", "USD / MMBtu", "NG=F"),
]
# code, name, how the price is quoted, Yahoo symbol (price of 1 unit in rupees), quantity
CURRENCIES = [
    ("USD", "US dollar", "1 US dollar", "INR=X", 1),
    ("EUR", "euro", "1 euro", "EURINR=X", 1),
    ("GBP", "British pound", "1 British pound", "GBPINR=X", 1),
    ("JPY", "Japanese yen", "100 Japanese yen", "JPYINR=X", 100),
    ("CNY", "Chinese yuan", "1 Chinese yuan", "CNYINR=X", 1),
    ("AED", "UAE dirham", "1 UAE dirham", "AEDINR=X", 1),
]
OUNCE_G = 31.1035


def fmt(v, digits=2):
    return f"{v:,.{digits}f}"


def pct(now, then):
    return None if not then else (now - then) / then * 100


def sgn(p):
    return "" if p is None else f"{p:+.1f}%".replace("-", "−")


def direction(p):
    return "flat" if p is None or abs(p) < 0.05 else ("up" if p > 0 else "down")


def spark(closes, w=120, h=36, pad=3, max_pts=40):
    if len(closes) < 2:
        return ""
    step = max(1, len(closes) // max_pts)
    pts = closes[::step]
    if pts[-1] != closes[-1]:
        pts = pts + [closes[-1]]
    lo, hi = min(pts), max(pts)
    span = (hi - lo) or 1
    dx = w / (len(pts) - 1)
    return " ".join(f"{i * dx:.1f},{h - pad - (v - lo) / span * (h - 2 * pad):.1f}" for i, v in enumerate(pts))


def points_ago(closes):
    """Monthly closes; the last bar is the current month."""
    n = len(closes)
    return {
        "1 year ago": closes[-13] if n >= 13 else None,
        "5 years ago": closes[-61] if n >= 61 else None,
        "10 years ago": closes[0] if n >= 115 else None,
    }


def _phrase(p):
    return f"{'up' if p > 0 else 'down'} {abs(p):.0f}%"


def build_commodity(key, label, unit, closes, price, usdinr=None):
    refs = points_ago(closes)
    rows = []
    for name, v in refs.items():
        if v:
            c = pct(price, v)
            rows.append({"label": name, "value_fmt": fmt(v), "chg_fmt": sgn(c), "dir": direction(c), "chg": c})
    window = closes[-13:] + [price]
    lo, hi = min(window), max(window)
    pos = (price - lo) / (hi - lo) if hi > lo else 0.5
    where = "near its 1-year high" if pos >= 0.85 else "near its 1-year low" if pos <= 0.15 else "in the middle of its 1-year range"
    by = {r["label"]: r["chg"] for r in rows}
    parts = []
    if "1 year ago" in by:
        parts.append(f"{_phrase(by['1 year ago'])} from a year ago")
    if "5 years ago" in by:
        parts.append(f"{_phrase(by['5 years ago'])} from 5 years ago")
    summary = f"{label} is " + " and ".join(parts) + f", and sits {where}." if parts else ""
    inr = None
    if usdinr and key in ("gold", "silver"):
        if key == "gold":
            inr = f"₹{price * usdinr / OUNCE_G * 10:,.0f} per 10 g"
        else:
            inr = f"₹{price * usdinr / OUNCE_G * 1000:,.0f} per kg"
    return {
        "key": key, "label": label, "unit": unit, "price_fmt": fmt(price), "rows": rows,
        "range_fmt": f"{fmt(lo)} – {fmt(hi)}", "summary": summary, "pts": spark(closes + [price]), "inr_fmt": inr,
    }


def build_rupee(code, name, quoted, closes, price, qty):
    """closes/price are rupees per 1 unit of the foreign currency."""
    now = price * qty
    refs = points_ago(closes)
    rows, by = [], {}
    for label, v in refs.items():
        if v:
            then = v * qty
            c = (then / now - 1) * 100  # positive = rupee stronger
            by[label] = c
            rows.append({"label": label, "value_fmt": f"₹{fmt(then)}", "chg_fmt": sgn(c), "dir": direction(c)})

    def word(c):
        return f"{abs(c):.1f}% {'stronger' if c > 0 else 'weaker'}"

    parts = []
    if "1 year ago" in by:
        parts.append(f"{word(by['1 year ago'])} than a year ago")
    if "5 years ago" in by:
        parts.append(f"{word(by['5 years ago'])} than 5 years ago")
    summary = f"The rupee is " + " and ".join(parts) + f" against the {name}." if parts else ""
    return {"code": code, "name": name, "quoted": quoted, "now_fmt": f"₹{fmt(now)}", "rows": rows,
            "summary": summary, "pts": spark([c * qty for c in closes] + [now])}


def _get(sym):
    try:
        r = requests.get(URL.format(sym=sym), headers=UA, timeout=15)
        r.raise_for_status()
        res = r.json()["chart"]["result"][0]
        closes = [c for c in res["indicators"]["quote"][0]["close"] if c is not None]
        price = res["meta"].get("regularMarketPrice") or closes[-1]
        return (closes, price) if len(closes) >= 13 else None
    except Exception:
        return None


def fetch():
    """Returns (commodities, rupee). Anything that failed is skipped."""
    syms = [c[3] for c in COMMODITIES] + [c[3] for c in CURRENCIES]
    with ThreadPoolExecutor(max_workers=6) as pool:
        got = dict(zip(syms, pool.map(_get, syms)))
    usd = got.get("INR=X")
    usdinr = usd[1] if usd else None
    commodities = [build_commodity(k, l, u, *got[s], usdinr=usdinr) for k, l, u, s in COMMODITIES if got.get(s)]
    rupee = [build_rupee(c, n, q, *got[s], qty) for c, n, q, s, qty in CURRENCIES if got.get(s)]
    return commodities, rupee
