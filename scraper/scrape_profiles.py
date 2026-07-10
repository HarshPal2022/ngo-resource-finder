import os
import re
import time
import html
import pandas as pd
import requests

from bs4 import BeautifulSoup

from config import (
    HEADERS,
    LINKS_FILE,
    RAW_DATA_FILE,
    REQUEST_DELAY,
)

from utils.parser import parse_entry

MAX_RETRIES = 3

session = requests.Session()
session.headers.update(HEADERS)


def decode_cfemail(encoded):
    if not encoded:
        return ""

    try:
        key = int(encoded[:2], 16)

        email = ""

        for i in range(2, len(encoded), 2):
            email += chr(int(encoded[i:i+2], 16) ^ key)

        return email

    except Exception:
        return ""


def extract_meta_description(soup):

    tag = soup.find("meta", attrs={"property": "og:description"})

    if not tag:
        return []

    content = tag.get("content", "")

    content = html.unescape(content)

    content = content.replace("&#8217;", "'")

    content = re.sub(r"\s+", " ", content)

    fields = [
        "Add",
        "Phone",
        "Tel",
        "Mobile",
        "Email",
        "Website",
        "Contact Person",
        "Purpose",
        "Aim/Objective/Mission",
        "Aims/Objectives/Mission"
    ]
    pattern = "(" + "|".join(re.escape(f) for f in fields) + r")\s*:?"

    parts = re.split(pattern, content)

    lines = []
    i = 1

    while i < len(parts):

        field = parts[i].strip()

        value = parts[i + 1].strip()

        value = re.split(pattern, value)[0].strip()

        lines.append(f"{field}: {value}")

        i += 2

    return lines


def scrape_profile(url):

    for attempt in range(MAX_RETRIES):

        try:

            response = session.get(
                url,
                timeout=15
            )

            response.raise_for_status()
            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            title = soup.find(
                "h1",
                class_="entry-title"
            )

            name = title.get_text(strip=True) if title else ""

            entry = soup.find(
                "div",
                class_="entry clearfix"
            )

            lines = []

            if entry:

                lines = [
                    x.strip()
                    for x in entry.get_text(
                        "\n",
                        strip=True
                    ).split("\n")
                    if x.strip()
                ]

            meta_lines = extract_meta_description(soup)

            if meta_lines:
                lines = meta_lines
            data = parse_entry(lines)
            # -------------------
            # Decode Cloudflare Email
            # -------------------

            cf = soup.select_one("a.__cf_email__")

            if cf:

                encoded = cf.get("data-cfemail")

                email = decode_cfemail(encoded)

                if email:
                    data["email"] = email

            # -------------------
            # Website
            # -------------------

            if not data.get("website"):

                for a in soup.find_all("a", href=True):

                    href = a["href"].strip()

                    if (
                        href.startswith("http")
                        and "ngosindia.org" not in href
                    ):

                        data["website"] = href
                        break

            data["name"] = name

            data["url"] = url

            return data

        except Exception:

            if attempt == MAX_RETRIES - 1:
                raise

            time.sleep(2* attempt)

    return None


def main():

    print("=" * 60)
    print("NGOConnect AI - Profile Scraper")
    print("=" * 60)

    if not os.path.exists(LINKS_FILE):
        raise FileNotFoundError(LINKS_FILE)

    links = pd.read_csv(LINKS_FILE)

    ngos = []

    total = len(links)

    failed = 0

    print(f"\nTotal NGO Profiles : {total}\n")

    for index, row in links.iterrows():

        district = row["district"]

        url = row["profile_url"]

        print(f"[{index+1}/{total}] {district}")

        try:

            ngo = scrape_profile(url)

            ngo["district"] = district

            ngos.append(ngo)

            print(f"✓ {ngo['name']}")

        except Exception as e:

            failed += 1

            print("✗ Failed")
            print(url)
            print(e)

        time.sleep(REQUEST_DELAY)

    df = pd.DataFrame(ngos)

    columns = [
        "district",
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

    os.makedirs("data", exist_ok=True)

    df.to_csv(
        RAW_DATA_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n" + "=" * 60)
    print("Scraping Completed")
    print("=" * 60)
    print(f"Successful : {len(df)}")
    print(f"Failed     : {failed}")
    print(f"Saved      : {RAW_DATA_FILE}")


if __name__ == "__main__":
    main()