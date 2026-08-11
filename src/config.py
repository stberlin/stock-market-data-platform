STOCK_SYMBOLS = [
    "QNC",
    "AAPL",
    "TSLA",
    "GOOGL",
    "IREN",
    "NVDA",
    "MU",
    "PL",
    "QBTS",
    "RGTI",
    "NTLA",
    "CRWV",
    "NBIS",
]

API_INTERVAL = "5min"
API_OUTPUT_SIZE = 100
API_MAX_RETRIES = 3

RATE_LIMIT_SLEEP_SECONDS = 60
SYMBOL_REQUEST_DELAY_SECONDS = 8

# Alert Configuration
ALERT_DROP_THRESHOLD = -3
ALERT_LOOKBACK_MINUTES = 30

# Company Mapping
COMPANY_NAMES = {
    "QNC": "Quantum eM.",
    "AAPL": "Apple",
    "TSLA": "Tesla",
    "GOOGL": "Alphabet",
    "IREN": "IREN",
    "NVDA": "NVIDIA",
    "MU": "Micron",
    "PL": "Planet Labs",
    "QBTS": "D-Wave",
    "RGTI": "Rigetti",
    "NTLA": "Intellia",
    "CRWV": "CoreWeave",
    "NBIS": "Nebius",
}
