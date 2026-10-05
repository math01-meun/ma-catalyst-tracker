"""Live parser for the BioBucks M&A and BD&L (licensing) trackers.

Used by wire_us.py on every run as a curated backstop: whatever the wire / news
feeds miss (or catch without a value) gets filled in from here.
"""
import re
import sys
import os
from datetime import datetime

import requests
from bs4 import BeautifulSoup

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import BIOBUCKS_MA_URL, BIOBUCKS_BDL_URL, BIOBUCKS_BDL_START, START_DATE

# Full browser headers: a bare "Mozilla/5.0 (...)" UA gets blocked by some
# hosts (actusnews) when requests come from GitHub Actions. GlobeNewswire is
# the exception, see wire_us.GLOBENEWSWIRE_HEADERS.
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/rss+xml;q=0.8,*/*;q=0.7",
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
}
DATE_RE = re.compile(r"^\d{2} [A-Z][a-z]{2} \d{4}$")
EUR_USD = 1.13  # rough conversion for deals only quoted in euros
# Milestone payments under existing collaborations, not new deals.
SKIP_DEAL_TYPES = ("candidate selection", "milestone", "programme transfer")


def parse_usd(text):
    """'Up to €750M (~US$850M)' -> 850e6, 'US$575M upfront, up to ~US$7.775B' -> 7.775e9.
    Prefers explicit US$ amounts and takes the largest (headline) one."""
    if not text:
        return None
    amounts = re.findall(r'US\$\s?([\d,.]+)\s*(B|M)\b', text)
    rate = 1.0
    if not amounts:
        amounts = re.findall(r'\$\s?([\d,.]+)\s*(B|M)\b', text)
    if not amounts:
        amounts, rate = re.findall(r'€\s?([\d,.]+)\s*(B|M)\b', text), EUR_USD
    values = []
    for num, unit in amounts:
        try:
            values.append(float(num.replace(",", "")) * (1e9 if unit == "B" else 1e6) * rate)
        except ValueError:
            pass
    return round(max(values), -5) if values else None


def _lines(url):
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    text = BeautifulSoup(response.text, "html.parser").get_text(separator="\n")
    return [l.strip() for l in text.split("\n") if l.strip()]


def _field(window, name):
    for j, w in enumerate(window):
        if w == name and j + 1 < len(window):
            return window[j + 1]
    return None


def _after(date_str, iso_start):
    try:
        return datetime.strptime(date_str, "%d %b %Y") >= datetime.strptime(iso_start, "%Y-%m-%d")
    except ValueError:
        return False


def scrape_ma():
    lines = _lines(BIOBUCKS_MA_URL)
    deals = []
    for i, line in enumerate(lines):
        if line not in ("Public", "Private") or i == 0 or i + 1 >= len(lines):
            continue
        date_str = lines[i + 1]
        if not DATE_RE.match(date_str) or not _after(date_str, START_DATE):
            continue
        window = lines[i:i + 25]
        acquirer = _field(window, "Acquirer")
        if not acquirer:
            continue
        value_text = _field(window, "Deal value")
        deals.append({
            "target": lines[i - 1],
            "acquirer": acquirer,
            "status": line,
            "date": date_str,
            "deal_value_usd": parse_usd(value_text),
            "deal_value_text": value_text,
            "premium": _field(window, "Premium"),
            "therapeutic_area": _field(window, "Therapeutic area"),
            "link": BIOBUCKS_MA_URL,
            "source": "biobucks",
        })
    return deals


def scrape_bdl():
    lines = _lines(BIOBUCKS_BDL_URL)
    deals = []
    for i, line in enumerate(lines):
        # Each card starts "Licensee / ↔ / Licensor / Deal type / DD Mon YYYY"
        if line != "↔" or i == 0 or i + 3 >= len(lines):
            continue
        date_str = lines[i + 3]
        if not DATE_RE.match(date_str) or not _after(date_str, BIOBUCKS_BDL_START):
            continue
        if any(k in lines[i + 2].lower() for k in SKIP_DEAL_TYPES):
            continue
        window = lines[i:i + 25]
        upfront = _field(window, "Upfront")
        total = _field(window, "Total potential")
        value = parse_usd(total) or parse_usd(upfront)
        value_text = " / ".join(
            t for t in (f"Upfront {upfront}" if upfront else None, total) if t
        )
        deals.append({
            "target": f"{lines[i + 1]} ({lines[i + 2]})",
            "acquirer": lines[i - 1],
            "status": "Licensing",
            "date": date_str,
            "deal_value_usd": value,
            "deal_value_text": value_text or None,
            "premium": "N/A",
            "therapeutic_area": _field(window, "Therapeutic area"),
            "link": BIOBUCKS_BDL_URL,
            "source": "biobucks",
        })
    return deals


if __name__ == "__main__":
    for name, fn in (("M&A", scrape_ma), ("BD&L", scrape_bdl)):
        found = fn()
        print(f"{name}: {len(found)} deals")
        for d in found[:8]:
            print(f"  {d['date']} | {d['acquirer']} -> {d['target']} | {d['deal_value_usd']}")
