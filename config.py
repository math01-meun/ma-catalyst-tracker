# Configuration - MA Catalyst Tracker
# Sources : communiques de presse (wires) uniquement, pas de SEC/EDGAR
# Marches couverts : US + Euronext

START_DATE = "2026-01-01"

WIRE_SOURCES = {
    "US": [
        "https://www.globenewswire.com/rss/industry/4573-Biotechnology",
        "https://www.globenewswire.com/rss/industry/4577-Pharmaceuticals",
        # Broader Health Care umbrella + adjacent industries: catches deals whose
        # press release is filed here instead of under Biotechnology/Pharmaceuticals
        # specifically (e.g. gene-therapy or diagnostics platform sales).
        "https://www.globenewswire.com/rss/industry/4000-Health%20Care",
        "https://www.globenewswire.com/rss/industry/4533-Health%20Care%20Providers",
        "https://www.globenewswire.com/rss/industry/4535-Medical%20Equipment",
        "https://www.globenewswire.com/rss/industry/4537-Medical%20Supplies",
        "https://www.globenewswire.com/rss/subjectcode/27-Mergers%20and%20Acquisitions",
        # Bankruptcy / Restructuring subject feeds: this is how the Eli Lilly /
        # Sangamo asset-auction deal was reported, not as an "M&A" story.
        "https://www.globenewswire.com/rss/subjectcode/5-Bankruptcy",
        "https://www.globenewswire.com/rss/subjectcode/37-Restructuring%2f%20Recapitalization",
        "https://www.prnewswire.com/rss/health-latest-news/biotechnology-list.rss",
    ],
    "EURONEXT": [
        "https://www.actusnews.com/rss",
    ],
}

KEYWORDS = [
    "acquisition", "to acquire", "acquires", "definitive agreement",
    "merger", "to be acquired", "tender offer", "business combination",
    "licensing agreement", "license agreement", "exclusive license",
    "collaboration agreement", "royalty agreement", "strategic partnership",
    "upfront payment", "milestone payments",
    # Distressed / bankruptcy M&A language -- deals like Eli Lilly buying
    # Sangamo's platforms out of Chapter 11 use this vocabulary instead of
    # "acquisition"/"merger".
    "asset purchase agreement", "asset purchase", "stalking horse",
    "chapter 11", "bankruptcy", "asset auction", "winning bidder",
    "successful bidder", "section 363", "auction process", "spin out",
    "spinout", "divest", "divestiture",
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
