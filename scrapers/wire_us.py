import feedparser
import json
import re
import sys
import os
from datetime import datetime, timezone
from calendar import timegm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import WIRE_SOURCES, KEYWORDS, SECTOR_BUCKETS

SECTOR_PRE_FILTERED = [
    "globenewswire.com/rss/industry/4573",
    "globenewswire.com/rss/industry/4577",
    "prnewswire.com/rss/health-latest-news/biotechnology",
]
DEAL_PRE_FILTERED = ["globenewswire.com/rss/subjectcode/27"]
MIN_DEAL_VALUE = 500_000
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "catalysts.json")

def matches_deal_keyword(text):
    return any(kw in text.lower() for kw in KEYWORDS)

def match_sector(text):
    text_lower = text.lower()
    for bucket, words in SECTOR_BUCKETS.items():
        if any(w in text_lower for w in words):
            return bucket
    return None

def extract_deal_value(text):
    patterns = [
        (r'\$\s?([\d,.]+)\s*billion', 1_000_000_000),
        (r'\$\s?([\d,.]+)\s*million', 1_000_000),
        (r'\$\s?([\d,.]+)\s*B\b', 1_000_000_000),
        (r'\$\s?([\d,.]+)\s*M\b', 1_000_000),
        (r'\$\s?([\d,.]+)\s*K\b', 1_000),
    ]
    for pattern, multiplier in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(',', '')) * multiplier
    return None

def scrape_new_deals():
    results = []
    for url in WIRE_SOURCES["US"]:
        feed = feedparser.parse(url)
        sector_ok_by_default = any(m in url for m in SECTOR_PRE_FILTERED)
        deal_ok_by_default = any(m in url for m in DEAL_PRE_FILTERED)

        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            full_text = f"{title} {summary}"

            if not deal_ok_by_default and not matches_deal_keyword(full_text):
                continue

            if sector_ok_by_default:
                sector = match_sector(full_text) or "Other Biotech"
            else:
                sector = match_sector(full_text)
                if not sector:
                    continue

            deal_value = extract_deal_value(full_text)
            if deal_value is not None and deal_value < MIN_DEAL_VALUE:
                continue

            # entry.get("published","")[:10] used to just chop the first 10 characters off
            # a string like "Mon, 03 Aug 2026 14:23:00 GMT", producing garbage like "Mon, 03 Au".
            # Use feedparser's pre-parsed struct_time instead, and format to match the
            # "DD Mon YYYY" style used everywhere else in catalysts.json.
            parsed = entry.get("published_parsed")
            date_str = datetime.fromtimestamp(timegm(parsed), tz=timezone.utc).strftime("%d %b %Y") if parsed else None

            results.append({
                "target": title,
                "acquirer": None,
                "date": date_str,
                "deal_value_usd": deal_value,
                "therapeutic_area": sector,
                "link": entry.get("link", ""),
                "status": "reported",
            })
    return results

def load_existing():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"last_updated": None, "deals": []}

def merge_and_save(existing, new_deals):
    existing_links = {d.get("link") for d in existing["deals"] if d.get("link")}
    added = 0
    for d in new_deals:
        if d["link"] and d["link"] not in existing_links:
            existing["deals"].append(d)
            existing_links.add(d["link"])
            added += 1
    existing["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
    return added

if __name__ == "__main__":
    existing = load_existing()
    new_deals = scrape_new_deals()
    added = merge_and_save(existing, new_deals)
    print(f"{added} nouveaux deals ajoutes ({len(existing['deals'])} au total)")
