"""
Application Configuration
"""

STATE = "maharashtra"

BASE_URL = "https://ngosindia.org"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36"
    )
}

REQUEST_DELAY = 2

# ===========================
# Data Files
# ===========================

DISTRICTS_FILE = "data/districts.csv"

LINKS_FILE = "data/links.csv"

RAW_DATA_FILE = "data/ngos.csv"

CLEAN_DATA_FILE = "data/cleaned_ngos.csv"