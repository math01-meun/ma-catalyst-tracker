import feedparser
import json
import re
import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import WIRE_SOURCES, KEYWORDS, SECTOR_BUCKETS

# Flux deja specifiques au secteur biotech/pharma - pas besoin de re-filtrer par secteur
PRE_FILTERED_SOURCES = [
    "globenewswire.com/rss/industry/4573",
    "globenewswire.com/rss/industry/4577",
    "prnewswire.com/rss/health-latest-news/biotechnology",
]

MIN_DEAL_VALUE = 500_000  # seuil minimum : 500K$ - filtre le bruit extreme uniquement

def matches_deal_keyword(text):
    text_lower = text.lower()
    return any(kw in text_lower for kw in KEYWORDS)

def match_sector(text):
    text_lower = text.lower()
    for bucket, words in SECTOR_BUCKETS.items():
        if any(w in text_lower for w in words):
            return bucket
    return None

def is_pre_filtered(url):
    return any(marker in url for marker in PRE_FILTERED_SOURCES)

def extract_deal_value(text):
    """Cherche des montants du type $739 million, $1.9 billion, $200M, $970K, etc."""
    patterns = [
        (r'\$\s?([\d,.]+)\s*billion', 1_000_000_000),
        (r'\$\s?([\d,.]+)\s*million', 1_000_000),
        (r'\$\s?([\d,.]+)\s*B\b', 1_000_000_000),
        (r'\$\s?([\d,.]+)\s*M\b', 1_000_000),
        (r'\$\s?([\d,.]+)\s*K\b', 1_000),
        (r'\$\s?([\d,.]+)\s*thousand', 1_000),
    ]
    for pattern, multiplier in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            number = float(match.group(1).replace(',', ''))
            return number * multiplier
    return None

def scrape_us_wires():
    results = []
    for url in WIRE_SOURCES["US"]:
        feed = feedparser.parse(url)
        pre_filtered = is_pre_filtered(url)

        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            full_text = f"{title} {summary}"

            if not matches_deal_keyword(full_text):
                continue

            if pre_filtered:
                sector = match_sector(full_text) or "Other Biotech"
            else:
                sector = match_sector(full_text)
                if not sector:
                    continue

            deal_value = extract_deal_value(full_text)

            # Exclut seulement si un montant est detecte ET qu'il est sous le seuil
            # Si aucun montant detecte, on garde quand meme (mieux vaut inclure que rater)
            if deal_value is not None and deal_value < MIN_DEAL_VALUE:
                continue

            results.append({
                "market": "US",
                "sector": sector,
                "title": title,
                "deal_value": deal_value,
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "status": "reported",
            })
    return results

if __name__ == "__main__":
    data = scrape_us_wires()
    print(f"{len(data)} deals matches found")
    for d in data:
        value_str = f"${d['deal_value']/1_000_000:.2f}M" if d['deal_value'] else "montant non detecte"
        print(f"[{d['sector']}] ({value_str}) {d['title']}")
