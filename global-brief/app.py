"""Global Brief: a simple, short-card news and markets dashboard.

Run on one computer:   python app.py          (add --demo for made-up sample data)
Build a static page:   python build.py        (this is what gets published, see README)
"""
import argparse
import hmac
import os
import socket
import threading
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from flask import Flask, Response, abort, render_template, request, send_from_directory

import brief
import layout

app = Flask(__name__)

TZ = ZoneInfo(os.environ.get("BRIEF_TZ", "Asia/Kolkata"))
REFRESH_MINUTES = int(os.environ.get("REFRESH_MINUTES", "20"))

EMPTY = {"stories": [], "world": [], "india": [], "show_first": 10, "prices": [], "links": [], "commodities": [], "rupee": [], "funds": [], "fd": {},
         "failed": [], "notes": [], "watch": None}
STATE = dict(EMPTY, demo=False, updated=None, ready=False)
LOCK = threading.Lock()


# ------------------------------------------------------------------ access
def _users():
    """BRIEF_USERS="sir1:password1,sir2:password2" turns on a login prompt."""
    raw = os.environ.get("BRIEF_USERS", "")
    return dict(p.split(":", 1) for p in raw.split(",") if ":" in p)


USERS = _users()


@app.before_request
def require_login():
    if not USERS:
        return None
    auth = request.authorization
    if auth and auth.username in USERS:
        if hmac.compare_digest(USERS[auth.username].encode(), (auth.password or "").encode()):
            return None
    return Response("Login required", 401, {"WWW-Authenticate": 'Basic realm="Global Brief"'})


@app.after_request
def security_headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["X-Robots-Tag"] = "noindex, nofollow"
    resp.headers["Cache-Control"] = "no-store"
    return resp


# ----------------------------------------------------------------- refresh
def refresh(demo=False):
    data = brief.collect(demo)
    with LOCK:
        STATE.update(data, demo=demo, updated=datetime.now(timezone.utc), ready=True)


def _loop(demo):
    while True:
        try:
            refresh(demo)
        except Exception as ex:  # never let the background thread die
            print("refresh failed:", ex)
        with LOCK:
            got_news = bool(STATE["stories"])
        time.sleep(REFRESH_MINUTES * 60 if got_news else 120)  # retry sooner if nothing came in


def start_background(demo=False):
    threading.Thread(target=_loop, args=(demo,), daemon=True).start()


# -------------------------------------------------------------------- page
def context():
    with LOCK:
        s = dict(STATE)
    now = datetime.now(TZ)
    ctx = {k: s[k] for k in EMPTY}
    stories = sorted(s["world"] + s["india"], key=lambda x: x["score"], reverse=True)
    ctx.update(
        ticker=([x for x in stories if x["impact"] == "HIGH"] or stories)[:6],
        greeting="Morning" if now.hour < 12 else "Afternoon" if now.hour < 17 else "Evening",
    )
    ctx.update(
        ready=s["ready"],
        demo=s["demo"],
        nav=layout.build_nav(s) if s["watch"] else [],
        today=now.strftime("%a %d %b"),
        updated=s["updated"].astimezone(TZ).strftime("%H:%M %Z") if s["updated"] else "",
    )
    return ctx


@app.route("/")
def index():
    return render_template("index.html", **context())


@app.route("/<name>")
def static_files(name):
    if name not in ("manifest.webmanifest", "icon.svg"):
        abort(404)
    return send_from_directory(os.path.join(app.root_path, "static"), name)


# --------------------------------------------------------------------- cli
def lan_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("10.255.255.255", 1))
        return sock.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        sock.close()


if os.environ.get("BRIEF_AUTOSTART") == "1":  # for servers such as gunicorn
    start_background()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="use made-up sample data (no internet needed)")
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)))
    args = ap.parse_args()

    start_background(demo=args.demo)
    print("\n  Global Brief is starting (first load takes a few seconds)")
    print(f"  Laptop:  http://localhost:{args.port}")
    print(f"  Phone (same Wi-Fi):  http://{lan_ip()}:{args.port}")
    if not USERS:
        print("  NOTE: no login set. Anyone on your network can open this. See README to add one.\n")
    app.run(host=os.environ.get("BRIEF_HOST", "0.0.0.0"), port=args.port, debug=False, threaded=True)
