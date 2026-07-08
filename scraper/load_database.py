import requests
from bs4 import BeautifulSoup

url = "https://ngosindia.com/"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36"
    )
}

response = requests.get(url, headers=headers)

print("Status:", response.status_code)

if response.status_code == 200:
    with open("page.html", "w", encoding="utf-8") as f:
        f.write(response.text)

    print("HTML saved successfully!")