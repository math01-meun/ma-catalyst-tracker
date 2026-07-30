import requests
import re
import json
from bs4 import BeautifulSoup

URL = "https://www.biobucks.co/biotech-ma-tracker-2026"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def parse_value(text):
    """Convertit '~US$10.0B' ou 'Up to US$2.3B' ou '~US$900M' en nombre"""
    match = re.search(r'([\d,.]+)\s*(B|M)\b', text)
    if not match:
        return None
    number = float(match.group(1).replace(',', ''))
    return number * (1_000_000_000 if match.group(2) == 'B' else 1_000_000)

def scrape_biobucks():
    response = requests.get(URL, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(separator="\n")
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    deals = []
    i = 0
    while i < len(lines):
        if lines[i] in ("Public", "Private") and i > 0:
            target = lines[i - 1]
            status = lines[i]
            date_line = lines[i + 1] if i + 1 < len(lines) else ""

            deal = {"target": target, "status": status, "date": date_line}

            # Cherche les champs suivants dans une fenetre de 20 lignes
            window = lines[i:i + 20]
            for j, w in enumerate(window):
                if w == "Acquirer" and j + 1 < len(window):
                    deal["acquirer"] = window[j + 1]
                elif w == "Deal value" and j + 1 < len(window):
                    deal["deal_value_text"] = window[j + 1]
                    deal["deal_value_usd"] = parse_value(window[j + 1])
                elif w == "Premium" and j + 1 < len(window):
                    deal["premium"] = window[j + 1]
                elif w == "Therapeutic area" and j + 1 < len(window):
                    deal["therapeutic_area"] = window[j + 1]

            if "acquirer" in deal:
                deals.append(deal)
        i += 1

    return deals

if __name__ == "__main__":
    data = scrape_biobucks()
    print(f"{len(data)} deals trouves")
    output = {"source": URL, "deals": data}
    with open("../data/biobucks_2026.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    for d in data[:10]:
        print(f"{d.get('date')} | {d.get('acquirer')} -> {d.get('target')} | {d.get('deal_value_text')}")
