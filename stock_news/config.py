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

