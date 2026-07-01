import requests
from bs4 import BeautifulSoup

url = "https://ngosindia.com/"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36"
    )
}

response = requests.get(url, headers=headers, timeout=15)

print("Status Code:", response.status_code)

if response.status_code == 200:
    print("Website is reachable!")
else:
    print("Couldn't access the website.")