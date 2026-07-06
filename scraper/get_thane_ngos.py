import requests
from bs4 import BeautifulSoup

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

links = list(set(links))

print(f"Found {len(links)} NGO profile links")

for link in links[:10]:
    print(link)