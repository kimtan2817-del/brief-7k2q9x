"""Free market prices (no API key).

Uses Yahoo Finance's public chart endpoint. It is unofficial, so it can change
or rate-limit; when it fails the dashboard simply shows "n/a" for that asset.
To swap the source later, only fetch_prices() needs to change.
"""
from concurrent.futures import ThreadPoolExecutor

import requests

UA = {"User-Agent": "Mozilla/5.0 (GlobalBrief personal dashboard)"}
URL = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=1mo&interval=1d"

SYMBOLS = [
    ("brent", "Brent crude", "USD / barrel", "BZ=F"),
    ("wti", "WTI crude", "USD / barrel", "CL=F"),
    ("natgas", "Natural gas", "USD / MMBtu", "NG=F"),
    ("gold", "Gold", "USD / ounce", "GC=F"),
    ("silver", "Silver", "USD / ounce", "SI=F"),
    ("usdinr", "USD / INR", "INR per USD", "INR=X"),
]


def spark(closes, w=64, h=24, pad=2):
    pts = closes[-12:]
    if len(pts) < 2:
        return ""
    lo, hi = min(pts), max(pts)
    span = (hi - lo) or 1
    step = w / (len(pts) - 1)
    return " ".join(f"{i * step:.1f},{h - pad - (v - lo) / span * (h - 2 * pad):.1f}" for i, v in enumerate(pts))


def build(key, label, unit, closes, price=None):
    price = closes[-1] if price is None else price
    latest = closes[-1]
    # If the last daily close IS the live price, compare with the close before it.
    ref = closes[-2] if len(closes) > 1 and abs(latest - price) <= 0.0005 * abs(price) else latest
    chg = (price - ref) / ref * 100 if ref else None
    if chg is None or abs(chg) < 0.005:
        direction = "flat"
    else:
        direction = "up" if chg > 0 else "down"
    return {
        "key": key,
        "label": label,
        "unit": unit,
        "price": price,
        "price_fmt": f"{price:,.2f}",
        "chg": chg,
        "chg_fmt": "" if chg is None else f"{chg:+.2f}%".replace("-", "−"),
        "dir": direction,
        "pts": spark(closes),
    }


def _unavailable(key, label, unit):
    return {"key": key, "label": label, "unit": unit, "price": None, "price_fmt": "n/a",
            "chg": None, "chg_fmt": "", "dir": "flat", "pts": ""}


def _fetch_one(defn):
    key, label, unit, sym = defn
    try:
        r = requests.get(URL.format(sym=sym), headers=UA, timeout=12)
        r.raise_for_status()
        res = r.json()["chart"]["result"][0]
        closes = [c for c in res["indicators"]["quote"][0]["close"] if c is not None]
        price = res["meta"].get("regularMarketPrice")
        return build(key, label, unit, closes, price)
    except Exception:
        return _unavailable(key, label, unit)


def fetch_prices():
    with ThreadPoolExecutor(max_workers=6) as pool:
        return list(pool.map(_fetch_one, SYMBOLS))
