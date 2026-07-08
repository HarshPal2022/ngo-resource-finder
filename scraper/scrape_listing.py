import os
import requests
import pandas as pd
from bs4 import BeautifulSoup

# ----------------------------
# Configuration
# ----------------------------
STATE = "maharashtra"
DISTRICT = "thane"

URL = f"https://ngosindia.org/{STATE}/{DISTRICT}-ngos/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36"
    )
}

print(f"Scraping NGO listing page...")
print(URL)

response = requests.get(URL, headers=HEADERS, timeout=20)

if response.status_code != 200:
    raise Exception(f"Failed to fetch page. Status Code: {response.status_code}")

soup = BeautifulSoup(response.text, "html.parser")

links = []

for a in soup.find_all("a", href=True):

    href = a["href"]

    if "/maharashtra-ngos/" in href:
        links.append(href)

# Remove duplicates
links = sorted(set(links))

print(f"\nFound {len(links)} NGO profile links.")

# Create data folder
os.makedirs("data", exist_ok=True)

output_file = f"data/{DISTRICT}_links.csv"

df = pd.DataFrame({
    "profile_url": links
})

df.to_csv(output_file, index=False)

print(f"Saved links to {output_file}")