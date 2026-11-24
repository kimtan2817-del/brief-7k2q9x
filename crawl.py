"""Fills cards that only have a headline, using the article's own opening text.

Safe by design:
- obeys each site's robots.txt, skips paywalled pages and anything that is not a normal web page
- the text comes from the article itself; the optional Groq step only SHORTENS it (it may not add facts)
- if Groq is off, fails, or adds a name or number that is not in the article, the plain trimmed article text is used
- any card it cannot fill is left as a headline-only card
"""
import base64
import html
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from urllib import robotparser
from urllib.parse import urlparse

import requests

import engine

UA = "GlobalBriefBot/1.0 (private news reader; obeys robots.txt)"
MAX_BYTES = 700_000
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")  # change here if Groq retires it
_ROBOTS = {}
_JUNK = re.compile(r"cookie|subscribe|sign up|newsletter|all rights reserved|javascript|advertisement|follow us|read more:", re.I)


# ------------------------------------------------------------ fetching
def _resolve(url):
    """Google News links hide the real address. Older ones can be decoded; newer ones cannot, so skip them."""
    host = urlparse(url).netloc.lower()
    if not host.endswith("news.google.com"):
        return url
    m = re.search(r"/articles/([A-Za-z0-9_-]+)", url)
    if not m:
        return None
    raw = m.group(1)
    try:
        data = base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4))
    except Exception:
        return None
    m2 = re.search(rb"https?://[\x21-\x7e]+", data)
    return m2.group(0).decode("ascii", "ignore") if m2 else None


def _allowed(url):
    p = urlparse(url)
    base = f"{p.scheme}://{p.netloc}"
    if base not in _ROBOTS:
        rp = robotparser.RobotFileParser()
        try:
            r = requests.get(base + "/robots.txt", headers={"User-Agent": UA}, timeout=5)
            if r.status_code == 200:
                rp.parse(r.text.splitlines())
            elif 400 <= r.status_code < 500:
                rp.parse([])  # no robots.txt means no restrictions
            else:
                rp.parse(["User-agent: *", "Disallow: /"])
        except Exception:
            rp.parse(["User-agent: *", "Disallow: /"])  # cannot check, so do not crawl
        _ROBOTS[base] = rp
    return _ROBOTS[base].can_fetch(UA, url)


def _strip(s):
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def extract(page):
    """Opening text of an article page, or '' (paywalled / nothing useful)."""
    if re.search(r'"isAccessibleForFree"\s*:\s*"?false', page, re.I):
        return ""
    page = re.sub(r"(?is)<(script|style|nav|header|footer|aside|form|noscript)\b.*?</\1>", " ", page)
    desc = ""
    for pat in (r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)',
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:description["\']',
                r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)'):
        m = re.search(pat, page, re.I)
        if m:
            desc = _strip(m.group(1))
            break
    art = re.search(r"(?is)<article\b.*?</article>", page)
    paras, words = [], 0
    for p in re.findall(r"(?is)<p\b[^>]*>(.*?)</p>", art.group(0) if art else page):
        t = _strip(p)
        if len(t) < 60 or _JUNK.search(t):
            continue
        paras.append(t)
        words += len(t.split())
        if words >= 140:
            break
    text = " ".join(([desc] if len(desc) > 40 else []) + paras)
    return text[:1800]


def fetch_text(url):
    real = _resolve(url)
    if not real or not _allowed(real):
        return ""
    try:
        r = requests.get(real, headers={"User-Agent": UA, "Accept": "text/html"}, timeout=8, stream=True)
        if r.status_code != 200 or "html" not in r.headers.get("Content-Type", ""):
            return ""
        body = r.raw.read(MAX_BYTES, decode_content=True)
        return extract(body.decode(r.encoding or "utf-8", "ignore"))
    except Exception:
        return ""


# ------------------------------------------------------------ shortening
def _grounded(out, source):
    """True if every number and every mid-sentence capitalised word in `out` also appears in the source."""
    src = source.lower()
    for n in re.findall(r"\d[\d,.]*", out):
        if n.strip(",.") not in src:
            return False
    for sent in re.split(r"(?<=[.!?])\s+", out):
        for w in sent.split()[1:]:
            w = w.strip(".,;:!?\"'()“”’‘")
            if len(w) > 3 and w[0].isupper() and w.lower() not in src:
                return False
    return True


def _groq(text, title, key):
    prompt = ("Summarise the news article text below in 45 to 60 words, in plain English, as 2 or 3 sentences. "
              "Use ONLY facts stated in the text. Do not add names, numbers, reasons or background that are not in it. "
              "If the text does not describe the story, reply with exactly: INSUFFICIENT\n\n"
              f"Headline: {title}\n\nText: {text}")
    body = {"model": GROQ_MODEL, "temperature": 0.1, "max_tokens": 160,
            "messages": [{"role": "user", "content": prompt}]}
    for attempt in (1, 2):
        try:
            r = requests.post(GROQ_URL, headers={"Authorization": f"Bearer {key}"}, json=body, timeout=25)
        except Exception:
            return ""
        if r.status_code == 429 and attempt == 1:
            time.sleep(6)
            continue
        if r.status_code != 200:
            return ""
        try:
            out = r.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            return ""
        n = len(out.split())
        if "INSUFFICIENT" in out or not 15 <= n <= 80 or not _grounded(out, text + " " + title):
            return ""
        return out
    return ""


def shorten(text, title):
    """Returns (summary, written_by_ai)."""
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if key:
        out = _groq(text, title, key)
        if out:
            return out, True
    return engine.summarize(text, title), False


# ------------------------------------------------------------ entry point
def enrich(stories, max_pages=30, deadline_s=150):
    """Fill `short` on headline-only stories (in place). Returns how many were filled."""
    targets = [s for s in stories if not s.get("short")][:max_pages]
    if not targets:
        return 0
    stop = time.time() + deadline_s
    with ThreadPoolExecutor(max_workers=6) as ex:
        texts = list(ex.map(lambda s: fetch_text(s["link"]), targets))
    filled = 0
    for s, text in zip(targets, texts):
        if time.time() > stop or not text:
            continue
        short, ai = shorten(text, s["title"])
        if short:
            s["short"], s["ai"] = short, ai
            filled += 1
    return filled
