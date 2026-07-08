import time
import pandas as pd
import requests
from bs4 import BeautifulSoup

from config import HEADERS, INPUT_LINKS, OUTPUT_DATA, REQUEST_DELAY
from utils.parser import parse_entry


def scrape_profile(url):

    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    title = soup.find("h1", class_="entry-title")

    if title:
        name = title.get_text(strip=True)
    else:
        name = ""

    entry = soup.find("div", class_="entry clearfix")

    if entry is None:
        raise Exception("Could not find NGO content.")

    lines = [
        line.strip()
        for line in entry.get_text("\n", strip=True).split("\n")
        if line.strip()
    ]

    data = parse_entry(lines)

    data["name"] = name
    data["url"] = url

    return data


def main():

    links = pd.read_csv(INPUT_LINKS)

    ngos = []

    total = len(links)

    print(f"\nFound {total} NGO profiles.\n")

    for index, row in links.iterrows():

        url = row["profile_url"]

        print(f"[{index+1}/{total}] Scraping...")

        try:

            ngo = scrape_profile(url)

            ngos.append(ngo)

            print(f"✓ {ngo['name']}")

        except Exception as e:

            print(f"✗ Failed: {url}")
            print(e)

        time.sleep(REQUEST_DELAY)

    df = pd.DataFrame(ngos)

    columns = [
        "name",
        "address",
        "phone",
        "mobile",
        "email",
        "website",
        "contact_person",
        "purpose",
        "mission",
        "url",
    ]

    df = df.reindex(columns=columns)

    df.to_csv(OUTPUT_DATA, index=False)

    print("\n---------------------------------------")
    print(f"Saved {len(df)} NGOs")
    print(f"Output -> {OUTPUT_DATA}")
    print("---------------------------------------")


if __name__ == "__main__":
    main()