"""
Application configuration
"""

STATE = "maharashtra"
DISTRICT = "thane"

BASE_URL = "https://ngosindia.org"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36"
    )
}

REQUEST_DELAY = 2

INPUT_LINKS = f"data/{DISTRICT}_links.csv"

OUTPUT_DATA = f"data/{DISTRICT}_ngos.csv"