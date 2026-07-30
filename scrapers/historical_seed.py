import requests
import re
import json
from datetime import datetime, timezone

# Sources statiques contenant des deals biotech/pharma 2026 en texte redige
HISTORICAL_ARTICLES = [
    "https://lifesciencedaily.news/biotech-ma-2026-every-1b-deal-so-far-and-what-is-driving-them/",
]

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def fetch_article_text(url):
    response = requests.get(url, headers=HEADERS, timeout=15)
    return response.text

def extract_deals_from_text(text, source_url):
    """Cherche des motifs du type: 'X acquired/acquiring/agreed to acquire Y for $Z billion/million'"""
    results = []

    # Nettoie le HTML basique pour ne garder que du texte
    text_clean = re.sub(r'<[^>]+>', ' ', text)
    text_clean = re.sub(r'\s+', ' ', text_clean)

    # Motifs de deals: [Acquereur] ... acquire/acquired/acquiring ... [Cible] ... for $[montant]
    pattern = r'([A-Z][a-zA-Z&\.\s]{2,40}?)\s+(?:agreed to acquire|acquiring|acquired|to acquire)\s+([A-Z][a-zA-Z&\.\s]{2,50}?)\s+for\s+(?:up to\s+)?\$?([\d,.]+)\s*(billion|million)'

    for match in re.finditer(pattern, text_clean, re.IGNORECASE):
        acquirer = match.group(1).strip()
        target = match.group(2).strip()
        amount = float(match.group(3).replace(',', ''))
        unit = match.group(4).lower()
        value = amount * (1_000_000_000 if unit == 'billion' else 1_000_000)

        results.append({
            "market": "US",
            "acquirer": acquirer,
            "target": target,
            "deal_value": value,
            "title": f"{acquirer} to acquire {target}",
            "source": source_url,
            "status": "historical",
        })
    return results

def scrape_historical():
    all_results = []
    for url in HISTORICAL_ARTICLES:
        try:
            text = fetch_article_text(url)
            deals = extract_deals_from_text(text, url)
            all_results.extend(deals)
        except Exception as e:
            print(f"Erreur sur {url}: {e}")
    return all_results

if __name__ == "__main__":
    data = scrape_historical()
    print(f"{len(data)} deals historiques trouves")
    for d in data:
        print(f"${d['deal_value']/1_000_000:.0f}M - {d['title']}")
