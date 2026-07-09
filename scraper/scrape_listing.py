import os
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup

from config import (
    DISTRICTS_FILE,
    HEADERS,
    LINKS_FILE,
    REQUEST_DELAY,
)

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def get_page_url(base_url, page):

    if page == 1:
        return base_url

    return f"{base_url}?lcp_page0={page}#lcp_instance_0"


def extract_links(soup):

    links = set()

    for a in soup.find_all("a", href=True):

        href = a["href"]

        if "/maharashtra-ngos/" in href:
            links.add(href)

    return links


def scrape_district(district, base_url):

    print("\n" + "=" * 60)
    print(f"District : {district}")

    page = 1

    district_links = set()

    while True:

        url = get_page_url(base_url, page)

        print(f"Page {page}")

        try:

            response = SESSION.get(url, timeout=30)
            response.raise_for_status()

        except Exception as e:

            print(e)
            break

        soup = BeautifulSoup(response.text, "html.parser")

        page_links = extract_links(soup)

        new_links = page_links - district_links

        print(
            f"Found {len(page_links)} | New {len(new_links)}"
        )

        if len(new_links) == 0:
            break

        district_links.update(new_links)

        page += 1

        time.sleep(REQUEST_DELAY)

    print(f"Total NGOs : {len(district_links)}")

    rows = []

    for link in sorted(district_links):

        rows.append({
            "district": district,
            "profile_url": link
        })

    return rows


def main():

    print("=" * 60)
    print("NGOConnect AI - Maharashtra Listing Scraper")
    print("=" * 60)

    if not os.path.exists(DISTRICTS_FILE):
        raise FileNotFoundError(DISTRICTS_FILE)

    districts = pd.read_csv(DISTRICTS_FILE)

    all_links = []

    for _, row in districts.iterrows():

        district = row["district"]
        url = row["url"]

        if district.lower() == "mumbai suburban":

            print("\nSkipping Mumbai Suburban")
            continue

        if district.lower() == "mumbai":

            url = "https://ngosindia.org/mumbai/"

        try:

            rows = scrape_district(
                district,
                url
            )

            all_links.extend(rows)

        except Exception as e:

            print(e)

    df = pd.DataFrame(all_links)

    df.drop_duplicates(
        subset=["profile_url"],
        inplace=True
    )

    df.sort_values(
        ["district", "profile_url"],
        inplace=True
    )

    os.makedirs("data", exist_ok=True)

    df.to_csv(
        LINKS_FILE,
        index=False
    )

    print("\n" + "=" * 60)
    print(f"Districts : {df['district'].nunique()}")
    print(f"NGO Links : {len(df)}")
    print(f"Saved -> {LINKS_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()