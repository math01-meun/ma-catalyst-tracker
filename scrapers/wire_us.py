import feedparser
import json
import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import WIRE_SOURCES, KEYWORDS, SECTOR_BUCKETS

def matches_deal_keyword(text):
    text_lower = text.lower()
    return any(kw in text_lower for kw in KEYWORDS)

def match_sector(text):
    text_lower = text.lower()
    for bucket, words in SECTOR_BUCKETS.items():
        if any(w in text_lower for w in words):
            return bucket
    return None

def scrape_us_wires():
    results = []
    for url in WIRE_SOURCES["US"]:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            full_text = f"{title} {summary}"

            if not matches_deal_keyword(full_text):
                continue
            sector = match_sector(full_text)
            if not sector:
                continue

            results.append({
                "market": "US",
                "sector": sector,
                "title": title,
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "status": "reported",
            })
    return results

if __name__ == "__main__":
    data = scrape_us_wires()
    print(f"{len(data)} deals matches found")
    for d in data:
        print(d["title"])
