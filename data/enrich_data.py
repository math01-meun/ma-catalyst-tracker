import json

with open("catalysts.json", encoding="utf-8") as f:
    data = json.load(f)

TICKER_MAP = {
    "Argenx": "ARGX", "Forte Biosciences": "FBRX", "Eli Lilly": "LLY",
    "Vertex Pharmaceuticals": "VRTX", "Vertex": "VRTX", "Novartis": "NVS",
    "AbbVie": "ABBV", "Merck": "MRK", "Merck KGaA, Darmstadt, Germany": "MRK.DE",
    "Gilead Sciences": "GILD", "Biogen": "BIIB", "GSK": "GSK", "Pfizer": "PFE",
    "Zymeworks": "ZYME", "Theravance Biopharma": "TBPH",
    "United Therapeutics": "UTHR", "Tarsus Pharmaceuticals": "TARS",
    "Crinetics Pharmaceuticals": "CRNX", "KalVista Pharmaceuticals": "KALV",
    "Terns Pharmaceuticals": "TERN", "Nuvalent": "NUVL",
    "Apogee Therapeutics": "APGE", "Bio-Techne": "TECH",
    "Catalyst Pharmaceuticals": "CPRX", "Soleno Therapeutics": "SLNO",
    "Day One Biopharmaceuticals": "DAWN", "Apellis Pharmaceuticals": "APLS",
    "Centessa Pharmaceuticals": "CNTA", "Arcellx": "ACLX",
    "RAPT Therapeutics": "RAPT", "Ventyx Biosciences": "VTYX",
    "XOMA Royalty": "XOMA", "Esperion Therapeutics": "ESPR",
    "Personalis": "PSNL", "Tempus AI": "TEM", "PolyPeptide Group": "PPGN.SW",
    "Kira Pharmaceuticals": "KRRA", "AtaiBeckley (atai Beckley)": "ATAI",
    "Ligand Pharmaceuticals": "LGND",
}

for deal in data["deals"]:
    target = deal.get("target", "")
    deal["ticker"] = TICKER_MAP.get(target)

# Ajoute le deal Forte manquant s'il n'y est pas deja
if not any(d.get("target") == "Forte Biosciences" for d in data["deals"]):
    data["deals"].insert(0, {
        "target": "Forte Biosciences",
        "acquirer": "Argenx",
        "status": "Public",
        "date": "27 Jul 2026",
        "deal_value_usd": 2200000000,
        "deal_value_text": "~US$2.2B",
        "premium": "~41%",
        "therapeutic_area": "Immunology",
        "ticker": "FBRX",
        "link": "",
    })

with open("catalysts.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"{len(data['deals'])} deals au total, Forte ajoute, tickers enrichis")
