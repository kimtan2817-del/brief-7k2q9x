"""People and countries your sir wants to follow (see watch.json).

Each name has aliases used to spot it in any headline, and search queries used
to go and fetch news about it from Google News.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus

import engine

GOOGLE = "https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"


class Watch:
    def __init__(self, cfg):
        self.cfg = cfg
        self.labels = {}
        self.entities = {}
        self.order = []
        for gid, g in cfg["groups"].items():
            self.labels[gid] = g["label"]
            for name, e in g["entities"].items():
                self.entities[name] = {
                    "group": gid,
                    "pats": engine.compile_terms(e["aliases"]),
                    "queries": e["queries"],
                }
                self.order.append(name)

    def match(self, text):
        return [n for n, e in self.entities.items() if any(p.search(text) for p in e["pats"])]

    def groups_of(self, names):
        seen = []
        for n in names:
            g = self.entities[n]["group"]
            if g not in seen:
                seen.append(g)
        return seen

    def group_entities(self, gid):
        return [n for n in self.order if self.entities[n]["group"] == gid]

    def fetch(self, per_query=25):
        """Search Google News for every name. Returns (items, failed_count, total_queries)."""
        days = int(self.cfg.get("window_days", 2))
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        jobs = [(n, q) for n in self.order for q in self.entities[n]["queries"]]

        def run(job):
            name, q = job
            url = GOOGLE.format(q=quote_plus(f"{q} when:{days}d"))
            got, err = engine._fetch_one({"name": name, "url": url}, cutoff, per_query)
            keep = []
            for it in got:
                # Search results can be loose, so keep only headlines that really name the person or country.
                if any(p.search(it.title) for p in self.entities[name]["pats"]):
                    it.entities = (name,)
                    keep.append(it)
            return keep, err

        items, failed = [], 0
        with ThreadPoolExecutor(max_workers=8) as pool:
            for got, err in pool.map(run, jobs):
                items.extend(got)
                failed += 1 if err else 0
        return items, failed, len(jobs)
