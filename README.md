# Global Brief

Short, Inshorts-style news cards for your sir's watch list, plus gold, silver and oil comparisons, the rupee,
mutual funds and FD rates. One page that works on phone and laptop. Free data only, no AI.

## The look

- **Phone:** each story is a full-screen card, like Inshorts. Swipe up for the next one. Each card has a picture, a topic label,
  a bold headline, a short summary (about 60 words) and, underneath, **Read more at (source)**, which opens the original story.
  The first card is the **Brief** (the top stories to know right now); tap one to jump to it.
- **Laptop:** a clean news wall with a large lead story. Click any card to read it, then use the arrow keys for the next one.
- **Cards / List** switches between the swipe view and a compact list. A red **LIVE** strip scrolls the biggest headlines.
- **Day / Night** button at the top. Text is black on white; night mode is white on near-black.

## Menu

| Tab | What it shows |
|---|---|
| World | What world leaders and big players are doing across every sector (US, China, Russia, UAE, Iran, Israel and more), plus big deals. **No India stories.** |
| India | Maharashtra leaders, national leaders, and major national party news (BJP, Congress and others). Stories mainly about India also land here. |
| Markets | Gold, silver and oil: price now vs 1, 5 and 10 years ago, a one-line summary, and news on these assets |
| Money | The rupee against major currencies, mutual funds, FD rates, and bond / savings news |

**Freshness rule.** World and India show stories from the **last 3 hours**. The **top 3 stories of the last 24 hours** in each tab
stay with a blue **TOP OF THE DAY** tag, even when older. The first 10 show, and the rest are behind **More top stories**
(at most 20 per tab, and no more than 5 on one topic). On a quiet hour the list is shorter.

**Catalyst / deal focus.** Stories about acquisitions, mergers, stakes, investments and approvals are boosted, and so are
stories naming the people in `watch.json`. Those names only find and rank news, and have no sections of their own.

---

## Put it online: private code + Netlify (recommended)

Your **code stays private** on GitHub. GitHub rebuilds the page every hour and sends it to Netlify, which hosts the link.

1. **Netlify:** create a free account at netlify.com. Click **Add new site, Deploy manually** and drop any small file
   (or this project's `site` folder) to create an empty site. Open **Site configuration** and copy the **Site ID**.
   Optionally change the site name under **Domain management** to something hard to guess.
2. **Netlify token:** click your avatar, **User settings, Applications, Personal access tokens, New access token**. Copy it.
3. **GitHub:** create a new repository and tick **Private**. Upload the project with GitHub Desktop (**File, Add local repository**,
   then **Commit to main**, then **Publish repository**, keeping **Keep this code private** ticked).
4. In the repository open **Settings, Secrets and variables, Actions, New repository secret**. Add two secrets:
   `NETLIFY_AUTH_TOKEN` (the token) and `NETLIFY_SITE_ID` (the Site ID).
5. Open the **Actions** tab, choose **Update and publish Global Brief**, click **Run workflow**. After a few minutes your
   `.netlify.app` link shows the page. Send it to your sirs; on a phone use **Add to Home Screen**.

The page tells search engines not to list it, but **anyone who has the link can open it** (a password on Netlify needs a paid plan).
The page contains only public news.

### If something goes wrong
- A red cross in **Actions**: open the run and read the error. A failed build never replaces the last good page.
- Hourly runs use GitHub's free minutes for private repositories. Each run takes a minute or two, which should fit the free
  monthly allowance, but check GitHub's current limits. If it runs short, change the schedule in `.github/workflows/publish.yml`
  (for example `"7 */2 * * *"` for every 2 hours).
- Netlify's free plan has limits that change over time, and every hourly update counts as a deploy. Check Netlify's pricing page.

---

## Run it on one computer instead (optional)

```
pip install -r requirements.txt
python app.py
```
Open http://localhost:8000. Others on the same Wi-Fi can open the address printed in the terminal.
Try the layout with made-up data: `python app.py --demo`.
To add a login: `BRIEF_USERS="sir1:pass1,sir2:pass2" python app.py` (Windows PowerShell: `$env:BRIEF_USERS="sir1:pass1,sir2:pass2"; python app.py`).

---

## Things you will edit

| File | What it controls |
|---|---|
| `watch.json` | The people and countries used to find and rank news (they have no sections of their own). Add a name with its `aliases` (words that identify it in a headline) and `queries` (what to search for). |
| `fd_rates.json` | **FD rates. These are not automatic.** Type each bank's rates and the date, and commit the change on GitHub (open the file, click the pencil, edit, commit). |
| `funds.json` | Which mutual funds to show. Names are searched on mfapi.in; if one shows "Not found", simplify the name. |
| `feeds.json` | News sources. Dead feeds are skipped and listed at the bottom of the page. |
| `rules.json` | Topic words (including deal and party words), scoring, and the `selection` block: `fresh_hours` (3), `top_of_day` (3), `top_window_hours` (24), `total` (20 per tab), `show_first` (10), `per_topic` (5), `min_score` (9). |

## Honest limits

- **Summaries come from the short description in each feed.** The app does not yet open the full article pages. Cards from Google News searches have a headline only until that is built.
- **Pictures are loaded from the publishers' own servers.** A publisher can change or block an image, in which case the card
  shows the topic graphic. Some feeds only provide small images, which can look soft on a large phone screen.
- **Summaries are the publisher's own text, trimmed.** Searches on Google News return headlines only, so those cards
  have no summary. Cards from sources that publish a description do.
- **Rules cannot understand a story.** They can mis-tag, and a name like "Modi" or "Shah" can match an unrelated person.
  Every card links to the original so it can be checked.
- **Prices come from Yahoo Finance's public endpoint** (unofficial, may be delayed or occasionally fail). A rupee price
  for gold and silver is the international price converted, so local rates differ because of duty and tax.
  If an asset cannot be fetched it is left out.
- **Mutual fund data** comes from the free mfapi.in service (AMFI data). Returns are past performance.
- **There is no free source for FD rates or the 10-year bond yield**, so FD rates are typed in by hand and bonds are news only.
- **Leader names change.** The countries use job titles in some searches ("Iran president") so they stay correct,
  but check `watch.json` now and then.
- Free sources can change or disappear, and publishers' terms apply. This is meant for private reading by a small team.
