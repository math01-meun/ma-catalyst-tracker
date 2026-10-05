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
        "https://www.prnewswire.com/rss/health-latest-news/pharmaceuticals-list.rss",
        "https://www.prnewswire.com/rss/financial-services-latest-news/acquisitions-mergers-and-takeovers-list.rss",
    ],
    "EURONEXT": [
        "https://www.actusnews.com/rss",
    ],
}

# Each wire feed only holds its latest 20 items (~1 day on the busy biotech
# feeds), so the scraper runs every few hours. Google News search catches what
# the wires don't carry: Business Wire, company newsrooms (Novartis, Merck...),
# Reuters/Fierce coverage. Only items with a disclosed $ value are kept.
GOOGLE_NEWS_QUERIES = [
    '(biotech OR pharma OR biopharma) (acquire OR acquisition OR merger OR "tender offer") (billion OR million) when:3d',
    '(biotech OR pharma OR biopharma) ("license agreement" OR "licensing deal" OR "licensing agreement" OR "option agreement") (upfront OR milestones) when:3d',
    '(pharma OR biotech) (collaboration OR alliance OR "equity investment") upfront (billion OR million) when:3d',
]

# Curated trackers merged on every run as a backstop for anything the feeds miss.
BIOBUCKS_MA_URL = "https://www.biobucks.co/biotech-ma-tracker-2026"
BIOBUCKS_BDL_URL = "https://www.biobucks.co/biotech-bdl-tracker-2026"
# Licensing deals are imported from this date on; set to START_DATE to backfill
# the whole 2026 BD&L tracker.
BIOBUCKS_BDL_START = "2026-09-25"

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
    "license and option", "option agreement", "expand alliance", "expands alliance",
    "expand global alliance", "equity investment", "take private", "taken private",
    "go-private", "to be acquired", "completes acquisition", "agreement to acquire",
]

# Headlines that match the deal keywords but are never deals.
EXCLUDE_KEYWORDS = [
    "own shares", "share buyback", "share repurchase", "class action",
    "shareholder alert", "investor alert", "equity alert", "investigation of",
    "investigating", "on behalf of shareholders", "law firm", "halper sadeh",
    "fairness of the", "dutch auction", "self-tender", "issuer tender", "real estate", "senior living", "energy investment",
]

SECTOR_BUCKETS = {
    "Oncology": ["oncology", "cancer", "tumor", "immuno-oncology"],
    "Neurology": ["neurology", "neuroscience", "alzheimer", "parkinson", "cns"],
    "Cardiovascular / Metabolic": ["cardiovascular", "metabolic", "diabetes", "obesity", "glp-1", "cholesterol", "pcsk9"],
    "Immunology": ["immunology", "autoimmune", "inflammation", "inflammatory", "lupus", "dermatitis", "il-4", "il-13", "il-33"],
    "Rare Disease": ["rare disease", "orphan drug", "genetic disease"],
    "Other Biotech": ["biotech", "pharmaceutical", "therapeutics", "clinical-stage", "biopharmaceutical", "biotechnology", "pharma", "drugmaker", "biosimilar", "cdmo"],
}

DEAL_SIZE_BUCKETS = {
    "mega": 5000000000,
    "mid": 1000000000,
    "small": 0,
}
