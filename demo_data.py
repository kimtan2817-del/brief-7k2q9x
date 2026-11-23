"""Made-up sample data so the dashboard can be seen and tested offline.
Nothing here is real news, a real quote or a real price. Every headline starts with "Sample:"."""
import base64
import math
from datetime import datetime, timedelta, timezone

import history
import markets
import mf
from engine import Item


def items():
    now = datetime.now(timezone.utc)
    raw = [
        # Maharashtra
        ("Sample Wire A", "Sample: Fadnavis reviews state infrastructure projects with senior officials", 35,
         "The chief minister held a review meeting on road, metro and port projects, asking departments to speed up approvals and report progress every month. Officials said several land acquisition issues are being resolved."),
        ("Sample Wire B", "Sample: Fadnavis chairs review of road and metro projects", 50, ""),
        ("Sample Wire A", "Sample: Sharad Pawar meets party leaders ahead of local body discussions", 120,
         "The senior leader met office bearers to discuss preparations and candidate selection. Party sources said the meeting focused on organisation building in rural districts."),
        ("Sample Wire C", "Sample: Uddhav Thackeray addresses party workers in Mumbai", 200,
         "Addressing workers, the Shiv Sena (UBT) chief spoke about civic issues and the party's plans for the coming months. He urged workers to stay in touch with residents of their wards."),
        ("Sample Wire B", "Sample: Raj Thackeray holds meeting on civic issues in Pune", 260,
         "The MNS chief met local office bearers to discuss traffic, water supply and civic services. A statement said further meetings will follow in other cities this month."),
        ("Sample Wire C", "Sample: Eknath Shinde announces review of welfare schemes", 300,
         "The deputy chief minister said departments will submit progress reports on welfare schemes within two weeks. He asked officials to make sure benefits reach eligible families without delay."),
        ("Sample Wire A", "Sample: Rohit Pawar raises farmers' concerns during district visit", 180,
         "During a visit to rural areas, the MLA met farmers and listened to concerns about crop prices and irrigation. He said he would raise the issues with the state government."),
        ("Sample Wire B", "Sample: Jay Pawar attends cooperative sector event in Baramati", 400,
         "He spoke at an event on cooperative institutions and rural credit, and met local leaders afterwards. Organisers said hundreds of members attended."),
        # India leaders
        ("Sample Wire A", "Sample: PM Modi chairs meeting on infrastructure and investment", 45,
         "The prime minister reviewed progress on major infrastructure projects and asked ministries to remove delays. Officials presented updates on rail, highways and ports during the meeting."),
        ("Sample Wire C", "Sample: Amit Shah reviews internal security preparedness with state officials", 90,
         "The home minister held a review meeting with senior officials from several states. The discussion covered coordination between agencies and preparedness for the coming festival season."),
        ("Sample Wire B", "Sample: Ajit Doval holds security consultations with regional counterparts", 150,
         "The national security adviser met counterparts for talks on regional security cooperation. Both sides agreed to keep communication channels open, an official statement said."),
        ("Sample Wire A", "Sample: Nitin Gadkari reviews highway projects, sets completion targets", 220,
         "The road transport minister reviewed ongoing highway works and directed contractors to meet deadlines. He also asked for stricter quality checks on newly built stretches."),
        ("Sample Wire C", "Sample: BJP president Nitin Nabin begins state tour to meet party units", 250,
         "The party president started a tour of several states to meet local units and review organisational work. He is expected to hold meetings with office bearers at each stop."),
        ("Sample Wire B", "Sample: Jaishankar holds talks with visiting foreign minister on trade and travel", 70,
         "The external affairs minister met his visiting counterpart for talks on trade, travel and cooperation. The two sides said they would work to finalise pending agreements soon."),
        # World
        ("Sample Wire A", "Sample: US revises steel and aluminium tariff schedule, Indian exporters watch closely", 12,
         "A revised tariff schedule on steel and aluminium imports has been published for public comment. Draft rates of up to 15% are being studied by exporters in India and other countries, who are assessing the effect on costs."),
        ("Sample Business Times", "Sample: Steel and aluminium tariff schedule revised by US, India exporters brace", 20, ""),
        ("Sample Wire C", "Sample: US steel and aluminium tariff schedule revised; exporters in India brace", 33, ""),
        ("Sample Wire B", "Sample: Russia and India discuss energy supply arrangements", 160,
         "Officials from the two countries met to discuss long-term energy supply and payment arrangements. Both sides described the talks as constructive and agreed to meet again."),
        ("Sample Wire A", "Sample: China and India hold border talks, agree to continue dialogue", 130,
         "Representatives of China and India held a round of talks and agreed to keep dialogue going through diplomatic channels. No major announcements were made after the meeting."),
        ("Sample Wire C", "Sample: UAE and India sign agreement to expand trade in local currencies", 80,
         "The agreement aims to make it easier for businesses in the UAE and India to settle trade in their own currencies. Officials said it could reduce costs and speed up payments."),
        ("Sample Wire A", "Sample: Iran talks resume as shipping insurers reassess risk in key sea lane", 25,
         "Talks resumed this week while shipping insurers reviewed risk ratings for a key sea lane. Traders said oil prices reacted to the headlines, though trading volumes stayed normal."),
        ("Sample Wire B", "Sample: Iran talks resume; shippers weigh risk on key sea lane", 40, ""),
        ("Sample Wire C", "Sample: Israel and regional mediators discuss ceasefire arrangements", 95,
         "Mediators and Israeli officials held discussions on possible ceasefire arrangements. Details were not made public, and officials said talks would continue in the coming days."),
        # Parties and deals
        ("Sample Wire A", "Sample: Congress party leaders meet Rahul Gandhi to finalise seat talks with allies", 20,
         "Senior Congress party leaders met Rahul Gandhi to discuss seat sharing with alliance partners. Party sources said talks will continue over the next few days before an announcement."),
        ("Sample Wire B", "Sample: Congress leaders meet Rahul Gandhi on seat talks with allies", 35, ""),
        ("Sample Wire C", "Sample: BJP and allies review Lok Sabha session strategy, floor managers named", 50,
         "The BJP and its allies met to plan business for the coming Lok Sabha session. Floor managers were named for key bills, party officials said."),
        ("Sample Wire A", "Sample: BJP allies review Lok Sabha session strategy", 65, ""),
        ("Sample Wire B", "Sample: Global steelmaker announces billion-dollar acquisition of European rival", 15,
         "The company said it agreed to acquire a European rival in a deal valued at about $2 billion, subject to regulatory approval. Executives said the merger would widen its reach in specialty steel."),
        ("Sample Wire C", "Sample: Steelmaker agrees acquisition of European rival in $2 billion deal", 30, ""),
        # Money
        ("Sample Wire A", "Sample: Mutual fund SIP inflows stay steady for another month", 110,
         "Monthly investments through systematic investment plans stayed steady at about ₹25,000 crore, industry data showed. Analysts said regular investors continued to put money in despite market swings."),
        ("Sample Wire B", "Sample: Banks revise fixed deposit rates for select tenures", 140,
         "Several banks changed fixed deposit rates for selected tenures this week. Customers are advised to compare rates and tenures before booking a deposit."),
        ("Sample Wire C", "Sample: Bond yields ease as traders expect steady repo rate", 100,
         "Government bond yields eased slightly as traders expected the central bank to keep its policy rate unchanged. Dealers said trading remained calm."),
        ("Sample Wire A", "Sample: RBI keeps repo rate unchanged, rupee steady against the dollar", 60,
         "The central bank left its policy rate unchanged and said it would watch inflation closely. The rupee traded in a narrow range against the dollar after the announcement."),
        # Commodities
        ("Sample Energy Daily", "Sample: OPEC signals output cut as crude holds near weekly high", 30,
         "Oil producers signalled a possible cut of 1 million barrels a day while crude prices stayed close to this week's high of $82. Traders said supply concerns are outweighing worries about demand."),
        ("Sample Wire B", "Sample: Crude steadies near weekly high as OPEC weighs output cut", 50, ""),
        ("Sample Wire B", "Sample: Gold steadies as traders weigh interest rate outlook", 90,
         "Gold prices held steady as traders weighed the outlook for interest rates and the dollar. Analysts said investors are waiting for fresh economic data before making large moves."),
        ("Sample Sports", "Sample: Premier League title race tightens after weekend results", 70, "Sports sample."),
    ]
    out = [
        Item(title, "https://example.com/sample-story", src, now - timedelta(minutes=mins), summary)
        for src, title, mins, summary in raw
    ]
    for i, it in enumerate(out):
        if i % 3 != 2:  # leave some without a picture to show the fallback design
            it.image = _art(i)
    return out


def _art(seed):
    """A made-up abstract picture, so the demo can show how cards look with images."""
    h = [210, 25, 150, 340, 260, 190][seed % 6]
    cx1, cy1, r1 = 120 + (seed * 47) % 520, 100 + (seed * 31) % 200, 110 + (seed * 13) % 90
    cx2, cy2, r2 = 700 - (seed * 53) % 400, 300 - (seed * 29) % 150, 80 + (seed * 17) % 80
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450"><defs>'
        '<linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="hsl({h},45%,38%)"/><stop offset="1" stop-color="hsl({(h + 35) % 360},50%,20%)"/>'
        '</linearGradient></defs><rect width="800" height="450" fill="url(#g)"/>'
        f'<circle cx="{cx1}" cy="{cy1}" r="{r1}" fill="hsla({(h + 20) % 360},60%,70%,.18)"/>'
        f'<circle cx="{cx2}" cy="{cy2}" r="{r2}" fill="hsla({(h + 330) % 360},60%,75%,.14)"/>'
        f'<path d="M0 360 Q 200 {300 + (seed * 17) % 60} 400 350 T 800 330 V450 H0Z" fill="hsla({h},40%,12%,.45)"/></svg>'
    )
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def prices():
    return [
        markets.build("brent", "Brent crude", "USD / barrel", [79.1, 80.2, 80.0, 81.1, 80.6, 82.4]),
        markets.build("wti", "WTI crude", "USD / barrel", [75.0, 76.1, 76.4, 77.0, 76.8, 78.1]),
        markets.build("natgas", "Natural gas", "USD / MMBtu", [3.35, 3.30, 3.28, 3.22, 3.23, 3.12]),
        markets.build("gold", "Gold", "USD / ounce", [2625.0, 2631.0, 2628.0, 2635.0, 2638.0, 2640.0]),
        markets.build("silver", "Silver", "USD / ounce", [31.5, 31.4, 31.6, 31.3, 31.36, 31.2]),
        markets.build("usdinr", "USD / INR", "INR per USD", [84.0, 84.05, 84.02, 84.08, 84.05, 84.1]),
    ]


def _series(start, end, n=121, wob=0.04, phase=0.0):
    out = [start * (end / start) ** (i / (n - 1)) * (1 + wob * math.sin(i / 6 + phase)) for i in range(n)]
    out[-1] = end
    return out


def history_data():
    usdinr = 84.1
    com = [
        history.build_commodity("gold", "Gold", "USD / ounce", _series(1250, 2640, wob=0.03), 2640, usdinr),
        history.build_commodity("silver", "Silver", "USD / ounce", _series(17, 31.2, wob=0.08, phase=1), 31.2, usdinr),
        history.build_commodity("brent", "Brent crude", "USD / barrel", _series(48, 82.4, wob=0.12, phase=2), 82.4),
        history.build_commodity("wti", "WTI crude", "USD / barrel", _series(45, 78.1, wob=0.12, phase=3), 78.1),
        history.build_commodity("natgas", "Natural gas", "USD / MMBtu", _series(2.8, 3.12, wob=0.25, phase=4), 3.12),
    ]
    rup = [
        history.build_rupee("USD", "US dollar", "1 US dollar", _series(66, 84.1, wob=0.01), 84.1, 1),
        history.build_rupee("EUR", "euro", "1 euro", _series(75, 91.0, wob=0.03, phase=1), 91.0, 1),
        history.build_rupee("GBP", "British pound", "1 British pound", _series(86, 107.0, wob=0.03, phase=2), 107.0, 1),
        history.build_rupee("JPY", "Japanese yen", "100 Japanese yen", _series(0.62, 0.56, wob=0.04, phase=3), 0.56, 100),
        history.build_rupee("CNY", "Chinese yuan", "1 Chinese yuan", _series(10.0, 11.6, wob=0.02, phase=4), 11.6, 1),
        history.build_rupee("AED", "UAE dirham", "1 UAE dirham", _series(18.0, 22.9, wob=0.01, phase=5), 22.9, 1),
    ]
    return com, rup



def funds():
    today = datetime.now()
    specs = [("Sample Index Fund (Direct, Growth)", 1.14, 182.4), ("Sample Flexi Cap Fund (Direct, Growth)", 1.17, 96.7),
             ("Sample Large Cap Fund (Direct, Growth)", 1.12, 74.3), ("Sample Small Cap Fund (Direct, Growth)", 1.24, 251.9)]
    out = []
    for name, yearly, latest in specs:
        data = []
        for i in range(0, 52 * 6):
            d = today - timedelta(days=7 * i)
            nav = latest * yearly ** (-(i * 7) / 365.25)
            data.append({"date": d.strftime("%d-%m-%Y"), "nav": f"{nav:.4f}"})
        out.append(mf.summarize(name, data))
    return out


def fd():
    sample = [("Sample Bank A", [6.8, 6.9, 6.75, 6.5]), ("Sample Bank B", [7.0, 7.1, 7.0, 6.8]),
              ("Sample Bank C", [6.9, 7.0, 6.9, 6.7]), ("Sample Bank D", [6.7, 6.8, 6.7, 6.5])]
    terms = ["1 year", "2 years", "3 years", "5 years"]
    return {
        "as_of": "a sample date (made-up numbers)", "filled": True, "terms": terms, "note": "",
        "banks": [{"name": n, "rates": dict(zip(terms, r))} for n, r in sample],
    }
