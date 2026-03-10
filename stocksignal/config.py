GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
YAHOO_SEARCH_URL = "https://query1.finance.yahoo.com/v1/finance/search"

MAX_RECORDS = 250
MIN_KEYWORD_LEN = 3

EXAMPLE_COMMANDS = [
    'MSFT -k "guidance, investigation" -d 5 -l 40',
    '"NVIDIA" -k "ai, chips, guidance"',
    'AAPL -k "earnings, outlook" -d 2',
    '"Tesla" --allow-non-english -l 15',
    '"Bank of America" -k "downgrade, investigation" -d 10 -l 40',
    '"Meta" -k "privacy, regulation" -d 7',
]

# (symbol, display_label) for ticker dropdown
POPULAR_TICKERS: list[tuple[str, str]] = [
    ("AAPL", "Apple (AAPL)"),
    ("MSFT", "Microsoft (MSFT)"),
    ("GOOGL", "Alphabet / Google (GOOGL)"),
    ("AMZN", "Amazon (AMZN)"),
    ("NVDA", "NVIDIA (NVDA)"),
    ("META", "Meta Platforms (META)"),
    ("TSLA", "Tesla (TSLA)"),
    ("BRK.B", "Berkshire Hathaway (BRK.B)"),
    ("JPM", "JPMorgan Chase (JPM)"),
    ("V", "Visa (V)"),
    ("JNJ", "Johnson & Johnson (JNJ)"),
    ("WMT", "Walmart (WMT)"),
    ("PG", "Procter & Gamble (PG)"),
    ("MA", "Mastercard (MA)"),
    ("UNH", "UnitedHealth (UNH)"),
    ("HD", "Home Depot (HD)"),
    ("DIS", "Walt Disney (DIS)"),
    ("PYPL", "PayPal (PYPL)"),
    ("BAC", "Bank of America (BAC)"),
    ("XOM", "Exxon Mobil (XOM)"),
    ("CVX", "Chevron (CVX)"),
    ("ABBV", "AbbVie (ABBV)"),
    ("PEP", "PepsiCo (PEP)"),
    ("KO", "Coca-Cola (KO)"),
    ("COST", "Costco (COST)"),
    ("AVGO", "Broadcom (AVGO)"),
    ("ORCL", "Oracle (ORCL)"),
    ("ADBE", "Adobe (ADBE)"),
    ("CRM", "Salesforce (CRM)"),
    ("NFLX", "Netflix (NFLX)"),
    ("AMD", "AMD (AMD)"),
    ("INTC", "Intel (INTC)"),
    ("QCOM", "Qualcomm (QCOM)"),
    ("TXN", "Texas Instruments (TXN)"),
    ("IBM", "IBM (IBM)"),
    ("GE", "General Electric (GE)"),
    ("BA", "Boeing (BA)"),
    ("CAT", "Caterpillar (CAT)"),
    ("HON", "Honeywell (HON)"),
    ("UPS", "UPS (UPS)"),
    ("MCD", "McDonald's (MCD)"),
    ("NKE", "Nike (NKE)"),
    ("SBUX", "Starbucks (SBUX)"),
    ("TMUS", "T-Mobile (TMUS)"),
    ("VZ", "Verizon (VZ)"),
    ("T", "AT&T (T)"),
    ("CMCSA", "Comcast (CMCSA)"),
    ("PM", "Philip Morris (PM)"),
    ("MRK", "Merck (MRK)"),
    ("LLY", "Eli Lilly (LLY)"),
    ("ABT", "Abbott (ABT)"),
    ("DHR", "Danaher (DHR)"),
    ("BMY", "Bristol-Myers Squibb (BMY)"),
    ("AMGN", "Amgen (AMGN)"),
    ("GILD", "Gilead (GILD)"),
    ("REGN", "Regeneron (REGN)"),
    ("LMT", "Lockheed Martin (LMT)"),
    ("RTX", "RTX (RTX)"),
    ("DE", "Deere (DE)"),
    ("SPY", "SPDR S&P 500 (SPY)"),
    ("QQQ", "Invesco QQQ (QQQ)"),
]
CUSTOM_OPTION_VALUE = "__custom__"
CUSTOM_OPTION_LABEL = "— Type or search —"

# Full ticker list: CSV with columns Symbol, Security Name (or similar)
# NASDAQ listings from GitHub datasets; fallback to POPULAR_TICKERS if fetch fails
TICKER_LIST_CSV_URL = "https://raw.githubusercontent.com/datasets/nasdaq-listings/main/data/nasdaq-listed.csv"
