"""Build the whole dashboard as one static page in ./site (this is what gets published).

    python build.py          live news and prices
    python build.py --demo   made-up sample data
"""
import argparse
import shutil
import sys
from pathlib import Path

from flask import render_template

import app


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--out", default="site")
    args = ap.parse_args()

    app.refresh(demo=args.demo)
    d = app.STATE
    got_anything = bool(d["stories"]) or any(p["price"] is not None for p in d["prices"])
    if not args.demo and not got_anything:
        # Exit with an error so the previous good page stays published.
        print("Nothing could be fetched, so the page was NOT rebuilt.")
        sys.exit(1)

    out = Path(args.out)
    out.mkdir(exist_ok=True)
    with app.app.test_request_context("/"):
        (out / "index.html").write_text(render_template("index.html", **app.context()), encoding="utf-8")
    for name in ("manifest.webmanifest", "icon.svg"):
        shutil.copy(Path(app.app.root_path) / "static" / name, out / name)
    print(f"Wrote {out}/index.html with {len(d['stories'])} stories")


if __name__ == "__main__":
    main()
