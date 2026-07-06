import requests
import pandas as pd
from bs4 import BeautifulSoup
import os

URL = "https://ngosindia.org/maharashtra/thane-ngos/"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(URL, headers=headers)

print("Status:", response.status_code)

soup = BeautifulSoup(response.text, "html.parser")

links = []

for a in soup.find_all("a", href=True):
    href = a["href"]

    if "/maharashtra-ngos/" in href:
        links.append(href)

# Remove duplicates
links = sorted(list(set(links)))

print(f"Found {len(links)} NGO profile links")

# Create data folder if it doesn't exist
os.makedirs("data", exist_ok=True)

# Save to CSV
df = pd.DataFrame({"profile_url": links})

df.to_csv("data/thane_links.csv", index=False)

print("Saved to data/thane_links.csv")