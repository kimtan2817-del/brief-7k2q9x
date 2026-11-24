"""Sections shown in the left menu (laptop) and bottom bar (phone)."""

ICONS = {
    "world": "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18",
    "india": "M12 21s-6-5.3-6-10a6 6 0 1 1 12 0c0 4.7-6 10-6 10zM12 8a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5z",
    "markets": "M4 20V11M10 20V5M16 20v-6M2 21h20",
    "money": "M3 7h18v12H3zM3 11h18M7 15h3",
    "gov": "M3 10l9-6 9 6M5 10v8M9 10v8M15 10v8M19 10v8M3 20h18",
}

# Picture shown on a card when the publisher gives no image.
CAT_ICONS = {
    "World": ICONS["world"],
    "Energy": "M13 3L5 14h6l-1 7 8-11h-6l1-7z",
    "Metals": "M6 4h12l3 5-9 11L3 9l3-5zM3 9h18",
    "War & Security": "M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3z",
    "Policy & Tariffs": ICONS["gov"],
    "India": ICONS["india"],
    "Markets & Economy": ICONS["markets"],
    "Money": ICONS["money"],
    "Deals": "M8 12l3 3 5-6M3 12a9 9 0 1 0 18 0 9 9 0 0 0-18 0z",
}


def build_nav(state):
    stories = state["stories"]
    money = [s for s in stories if "Money" in s["cats"] and s["age_h"] <= 48][:5]
    assets = [s for s in stories if {"Energy", "Metals"} & set(s["cats"]) and s["age_h"] <= 48][:5]

    def sec(sid, label, lst=None):
        return {"id": sid, "label": label, "icon": ICONS[sid], "stories": lst,
                "brief": (lst or [])[:7] if sid in ("world", "india") else None}

    return [sec("world", "World", state["world"]), sec("india", "India", state["india"]),
            sec("markets", "Markets", assets), sec("money", "Money", money)]
