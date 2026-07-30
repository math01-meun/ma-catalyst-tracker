# Configuration - MA Catalyst Tracker
# Sources : communiques de presse (wires) uniquement
# Marches couverts : US + Euronext

START_DATE = "2026-01-01"

WIRE_SOURCES = {
    "US": [
        "https://www.globenewswire.com/rss/industry/4573-Biotechnology",
        "https://www.globenewswire.com/rss/industry/4577-Pharmaceuticals",
        "https://www.globenewswire.com/rss/subjectcode/27-Mergers%20and%20Acquisitions",
        "https://www.prnewswire.com/rss/health-latest-news/biotechnology-list.rss",
    ],
    "EURONEXT": [
        "https://www.actusnews.com/rss",
    ],
}

KEYWORDS = [
    "acquisition", "to acquire", "acquires", "definitive agreement",
    "merger", "to be acquired", "tender offer", "business combination",
]

SECTOR_BUCKETS = {
    "Oncology": ["oncology", "cancer", "tumor", "immuno-oncology"],
    "Neurology": ["neurology", "neuroscience", "alzheimer", "parkinson", "cns"],
    "Cardiovascular / Metabolic": ["cardiovascular", "metabolic", "diabetes", "obesity", "glp-1"],
    "Rare Disease": ["rare disease", "orphan drug", "genetic disease"],
    "Other Biotech": ["biotech", "pharmaceutical", "therapeutics", "clinical-stage", "biopharmaceutical"],
}

DEAL_SIZE_BUCKETS = {
    "mega": 5000000000,
    "mid": 1000000000,
    "small": 0,
}
