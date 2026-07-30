# Configuration multi-marches - MA Catalyst Tracker
# Aucune donnee Nanobiotix - projet personnel

START_DATE = "2026-01-01"

MARKETS = {
    "US": {"source": "EDGAR", "language": "en"},
    "UK": {"source": "RNS", "language": "en"},
    "EURONEXT": {"source": "Regulated Information", "language": "multi"},
    "GERMANY": {"source": "DGAP/EQS Ad-hoc", "language": "de"},
    "SWITZERLAND": {"source": "SIX Ad-hoc", "language": "en/de/fr"},
    "JAPAN": {"source": "TDnet", "language": "ja"},
}

DEAL_SIZE_BUCKETS = {
    "mega": 5000000000,
    "mid": 1000000000,
    "small": 0,
}
