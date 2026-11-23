"""Mutual fund NAVs and returns from the free mfapi.in service (AMFI data, no key)."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from urllib.parse import quote

import requests

UA = {"User-Agent": "Mozilla/5.0 (GlobalBrief personal dashboard)"}
BASE = "https://api.mfapi.in/mf"


def _dt(s):
    return datetime.strptime(s, "%d-%m-%Y")


def nav_on(data, target):
    """data is newest first. NAV on or before `target`, or None if history does not reach back that far."""
    for row in data:
        if _dt(row["date"]) <= target:
            return float(row["nav"])
    return None


def summarize(name, data):
    """data: list of {"date": "dd-mm-yyyy", "nav": "123.4"}, newest first."""
    latest_dt = _dt(data[0]["date"])
    nav = float(data[0]["nav"])

    def ret(years):
        old = nav_on(data, latest_dt - timedelta(days=round(365.25 * years)))
        if not old:
            return None
        total = nav / old
        return (total - 1) * 100 if years <= 1 else (total ** (1 / years) - 1) * 100

    def f(v):
        return "n/a" if v is None else f"{v:+.1f}%".replace("-", "−")

    r1, r3, r5 = ret(1), ret(3), ret(5)
    return {
        "name": name, "nav_fmt": f"₹{nav:,.2f}", "date": latest_dt.strftime("%d %b %Y"),
        "r1": f(r1), "r3": f(r3), "r5": f(r5),
        "d1": "flat" if r1 is None else ("up" if r1 > 0 else "down"),
        "d3": "flat" if r3 is None else ("up" if r3 > 0 else "down"),
        "d5": "flat" if r5 is None else ("up" if r5 > 0 else "down"),
    }


def _resolve(entry):
    if entry.get("code"):
        return entry["code"]
    q = entry["query"]
    r = requests.get(f"{BASE}/search?q={quote(q)}", headers=UA, timeout=15)
    r.raise_for_status()
    words = q.lower().split()
    for hit in r.json():
        if all(w in hit["schemeName"].lower() for w in words):
            return hit["schemeCode"]
    return None


def _one(entry):
    label = entry.get("query") or str(entry.get("code"))
    try:
        code = _resolve(entry)
        if not code:
            return {"name": label, "missing": True}
        r = requests.get(f"{BASE}/{code}", headers=UA, timeout=20)
        r.raise_for_status()
        j = r.json()
        return summarize(j["meta"]["scheme_name"], j["data"])
    except Exception:
        return {"name": label, "missing": True}


def fetch(cfg):
    with ThreadPoolExecutor(max_workers=4) as pool:
        return list(pool.map(_one, cfg["funds"]))
