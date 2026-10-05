import feedparser
import json
import re
import sys
import os
import requests
from datetime import datetime, timezone, timedelta
from calendar import timegm
from urllib.parse import urlencode

from bs4 import BeautifulSoup

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import (WIRE_SOURCES, KEYWORDS, EXCLUDE_KEYWORDS, SECTOR_BUCKETS,
                    GOOGLE_NEWS_QUERIES)
import biobucks_live

SECTOR_PRE_FILTERED = [
    "globenewswire.com/rss/industry/4573",
    "globenewswire.com/rss/industry/4577",
    "globenewswire.com/rss/industry/4000",
    "globenewswire.com/rss/industry/4533",
    "globenewswire.com/rss/industry/4535",
    "globenewswire.com/rss/industry/4537",
    "prnewswire.com/rss/health-latest-news/biotechnology",
    "prnewswire.com/rss/health-latest-news/pharmaceuticals",
]
DEAL_PRE_FILTERED = ["globenewswire.com/rss/subjectcode/27"]
# Bankruptcy/Restructuring feeds are NOT pre-filtered as deal-ok or sector-ok:
# they cover every industry, so a Sangamo-style biotech asset sale still has to
# pass both the (now-expanded) KEYWORDS check and a SECTOR_BUCKETS match on its
# own text, same as any other unfiltered wire item.
MIN_DEAL_VALUE = 500_000
# Google News items are press coverage, not releases: only keep real-sized deals.
MIN_NEWS_DEAL_VALUE = 50_000_000
# Article pages fetched per run to find a value the RSS summary didn't give.
MAX_ARTICLE_FETCHES = 40
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
DATA_FILE = os.environ.get("CATALYSTS_FILE") or os.path.join(os.path.dirname(__file__), "..", "data", "catalysts.json")

# Generic words skipped when reducing a company name to its key token
# ("Eli Lilly and Company (NYSE: LLY)" -> "eli", "The Merck / MSD" -> "merck").
GENERIC_NAME_WORDS = {"the", "a", "an", "inc", "corp", "corporation", "co", "plc", "ag", "sa", "nv"}


def fetch_feed(url):
    # feedparser has no timeout of its own: a single hung feed used to stall the run.
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    return feedparser.parse(response.content)


def matches_deal_keyword(text):
    return any(kw in text.lower() for kw in KEYWORDS)


def is_excluded(text):
    return any(kw in text.lower() for kw in EXCLUDE_KEYWORDS)


def match_sector(text):
    text_lower = text.lower()
    for bucket, words in SECTOR_BUCKETS.items():
        if any(w in text_lower for w in words):
            return bucket
    return None


def extract_deal_value(text):
    """Headline value of the deal: the largest $ amount mentioned, so
    '$300M upfront ... up to $2.6 billion' gives 2.6B rather than 300M."""
    patterns = [
        (r'\$\s?([\d,.]+)\s*billion', 1_000_000_000),
        (r'\$\s?([\d,.]+)\s*million', 1_000_000),
        (r'\$\s?([\d,.]+)\s*B\b', 1_000_000_000),
        (r'\$\s?([\d,.]+)\s*bn\b', 1_000_000_000),
        (r'\$\s?([\d,.]+)\s*M\b', 1_000_000),
        (r'\$\s?([\d,.]+)\s*K\b', 1_000),
    ]
    values = []
    for pattern, multiplier in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            try:
                values.append(float(match.group(1).rstrip('.').replace(',', '')) * multiplier)
            except ValueError:
                pass
    return max(values) if values else None


def extract_parties(title):
    """Best-effort (acquirer, target) from the usual headline shapes."""
    t = re.sub(r"\s+-\s+[^-]+$", "", title)  # Google News appends " - Outlet"
    patterns = [
        (r"^(.+?) to be acquired by (.+?)(?: for| in|,|$)", "target_first"),
        (r"^(.+?) (?:to acquire|acquires|completes acquisition of|agrees to acquire|"
         r"enters into (?:a )?definitive agreement to acquire) (.+?)(?: for| in|,| to |$)", "acquirer_first"),
        (r"^(.+?) and (.+?) (?:enter|announce|sign)", "acquirer_first"),
    ]
    for pattern, order in patterns:
        m = re.search(pattern, t, re.IGNORECASE)
        if m:
            a, b = m.group(1).strip(), m.group(2).strip()
            return (b, a) if order == "target_first" else (a, b)
    return None, None


def article_value(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException:
        return None
    text = BeautifulSoup(response.text, "html.parser").get_text(" ")
    # Deal terms are in the opening paragraphs; further down are unrelated
    # figures (revenue, cash position...).
    return extract_deal_value(" ".join(text.split())[:4000])


def entry_date(entry):
    parsed = entry.get("published_parsed")
    return datetime.fromtimestamp(timegm(parsed), tz=timezone.utc).strftime("%d %b %Y") if parsed else None


def scrape_wires(health):
    results = []
    fetches = 0
    for url in WIRE_SOURCES["US"] + WIRE_SOURCES["EURONEXT"]:
        try:
            feed = fetch_feed(url)
        except requests.RequestException as e:
            health.append((url, f"ERROR {type(e).__name__}"))
            continue
        health.append((url, f"{len(feed.entries)} items"))
        sector_ok_by_default = any(m in url for m in SECTOR_PRE_FILTERED)
        deal_ok_by_default = any(m in url for m in DEAL_PRE_FILTERED)

        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            full_text = f"{title} {summary}"

            if is_excluded(full_text):
                continue
            if not deal_ok_by_default and not matches_deal_keyword(full_text):
                continue

            if sector_ok_by_default:
                sector = match_sector(full_text) or "Other Biotech"
            else:
                sector = match_sector(full_text)
                if not sector:
                    continue

            link = entry.get("link", "")
            deal_value = extract_deal_value(full_text)
            if deal_value is None and link and fetches < MAX_ARTICLE_FETCHES:
                fetches += 1
                deal_value = article_value(link)
            if deal_value is not None and deal_value < MIN_DEAL_VALUE:
                continue

            acquirer, _ = extract_parties(title)
            results.append({
                "target": title,
                "acquirer": acquirer,
                "date": entry_date(entry),
                "deal_value_usd": deal_value,
                "therapeutic_area": sector,
                "link": link,
                "status": "reported",
            })
    return results


def scrape_google_news(health):
    results = []
    for query in GOOGLE_NEWS_QUERIES:
        url = "https://news.google.com/rss/search?" + urlencode(
            {"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"})
        try:
            feed = fetch_feed(url)
        except requests.RequestException as e:
            health.append((f"Google News: {query[:50]}", f"ERROR {type(e).__name__}"))
            continue
        health.append((f"Google News: {query[:50]}", f"{len(feed.entries)} items"))
        for entry in feed.entries:
            title = entry.get("title", "")
            if is_excluded(title) or not matches_deal_keyword(title + " acquire license"):
                continue
            sector = match_sector(title + " " + query)
            value = extract_deal_value(title)
            if value is None or value < MIN_NEWS_DEAL_VALUE:
                continue
            acquirer, _ = extract_parties(title)
            results.append({
                "target": re.sub(r"\s+-\s+[^-]+$", "", title),
                "acquirer": acquirer,
                "date": entry_date(entry),
                "deal_value_usd": value,
                "therapeutic_area": sector or "Other Biotech",
                "link": entry.get("link", ""),
                "status": "reported",
                "source": "news",
            })
    return results


def scrape_biobucks(health):
    results = []
    for name, fn in (("BioBucks M&A", biobucks_live.scrape_ma), ("BioBucks BD&L", biobucks_live.scrape_bdl)):
        try:
            found = fn()
        except requests.RequestException as e:
            health.append((name, f"ERROR {type(e).__name__}"))
            continue
        health.append((name, f"{len(found)} deals"))
        results.extend(found)
    return results


# --- de-duplication -------------------------------------------------------

def name_key(name):
    if not name:
        return None
    name = re.sub(r"\(.*?\)", " ", name.lower())
    words = [w for w in re.findall(r"[a-z0-9]+", name) if w not in GENERIC_NAME_WORDS]
    return words[0] if words else None


def parse_date(s):
    try:
        return datetime.strptime(s, "%d %b %Y")
    except (TypeError, ValueError):
        return None


def close_dates(a, b, days=7):
    da, db = parse_date(a), parse_date(b)
    return bool(da and db and abs((da - db).days) <= days)


def same_value(a, b):
    return bool(a and b and abs(a - b) / max(a, b) <= 0.03)


def is_same_deal(new, old):
    """Different sources describe one deal differently (BioBucks names vs a
    press-release headline vs a Reuters title), so match on company names or
    on the headline value within a few days."""
    if new.get("link") and new.get("link") == old.get("link") and "biobucks.co" not in new["link"]:
        return True
    # Same two parties match at any date (announce -> close can be months apart).
    new_keys = {k for k in (name_key(new.get("acquirer")), name_key(new.get("target"))) if k}
    old_keys = {k for k in (name_key(old.get("acquirer")), name_key(old.get("target"))) if k}
    if len(new_keys) == 2 and new_keys == old_keys:
        return True
    # A headline-only row (target = full title) mentions both parties of a curated deal.
    old_title, new_title = (old.get("target") or "").lower(), (new.get("target") or "").lower()
    if len(new_keys) == 2 and all(k in old_title for k in new_keys):
        return True
    if len(old_keys) == 2 and all(k in new_title for k in old_keys):
        return True
    return close_dates(new.get("date"), old.get("date")) and \
        same_value(new.get("deal_value_usd"), old.get("deal_value_usd"))


def is_curated(deal):
    return deal.get("status") != "reported"


def load_existing():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"last_updated": None, "deals": []}


def merge(existing, new_deals):
    deals = existing["deals"]
    added, upgraded = [], []
    for d in new_deals:
        match = next((old for old in deals if is_same_deal(d, old)), None)
        if match is None:
            deals.append(d)
            added.append(d)
        elif is_curated(d) and not is_curated(match):
            # A curated BioBucks entry replaces the raw headline row, keeping
            # the press-release link, which is more useful than the tracker URL.
            link = match.get("link")
            match.clear()
            match.update(d)
            if link:
                match["link"] = link
            upgraded.append(match)
        elif match.get("deal_value_usd") is None and d.get("deal_value_usd"):
            match["deal_value_usd"] = d["deal_value_usd"]
            upgraded.append(match)
    return added, upgraded


def save(existing):
    existing["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)


def fmt(d):
    v = d.get("deal_value_usd")
    value = f"${v / 1e9:.2f}B" if v and v >= 1e9 else (f"${v / 1e6:.0f}M" if v else "n/d")
    return f"{d.get('date')} | {d.get('acquirer') or '?'} -> {d.get('target')} | {value}"


def write_summary(health, added, upgraded):
    lines = ["## Deal scraper run", "", "### Sources", ""]
    lines += [f"- {'❌' if 'ERROR' in status else '✅'} {src}: {status}" for src, status in health]
    lines += ["", f"### Added ({len(added)})", ""] + [f"- {fmt(d)}" for d in added]
    lines += ["", f"### Upgraded ({len(upgraded)})", ""] + [f"- {fmt(d)}" for d in upgraded]
    report = "\n".join(lines)
    print(report)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(report + "\n")


if __name__ == "__main__":
    health = []
    existing = load_existing()
    # Curated first, so headline rows from the feeds dedupe against named deals.
    new_deals = scrape_biobucks(health) + scrape_wires(health) + scrape_google_news(health)
    added, upgraded = merge(existing, new_deals)
    if added or upgraded:
        save(existing)
    write_summary(health, added, upgraded)
    print(f"{len(added)} nouveaux deals ajoutes, {len(upgraded)} enrichis ({len(existing['deals'])} au total)")
    failed = sum("ERROR" in status for _, status in health)
    if failed > len(health) / 2:
        # Fail the job so GitHub emails the repo owner: the tracker is going blind.
        sys.exit(f"{failed}/{len(health)} sources failed")
