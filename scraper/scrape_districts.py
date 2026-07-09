import os
import pandas as pd
from config import BASE_URL, DISTRICTS_FILE, STATE

DISTRICTS = [
    "ahmednagar",
    "akola",
    "amravati",
    "aurangabad",
    "beed",
    "bhandara",
    "buldhana",
    "chandrapur",
    "dhule",
    "gadchiroli",
    "gondia",
    "hingoli",
    "jalgaon",
    "jalna",
    "kolhapur",
    "latur",
    "mumbai",
    "nagpur",
    "nanded",
    "nandurbar",
    "nashik",
    "osmanabad",
    "palghar",
    "parbhani",
    "pune",
    "raigad",
    "ratnagiri",
    "sangli",
    "satara",
    "sindhudurg",
    "solapur",
    "thane",
    "wardha",
    "washim",
    "yavatmal",
]

def format_name(slug):
    return " ".join(word.capitalize() for word in slug.split("-"))

def build_url(slug):

    if slug == "mumbai":
        return f"{BASE_URL}/mumbai/"

    return f"{BASE_URL}/{STATE}/{slug}-ngos/"

def main():

    print("=" * 60)
    print("NGOConnect AI - District Generator")
    print("=" * 60)

    os.makedirs("data", exist_ok=True)

    rows = []
    for slug in DISTRICTS:

        rows.append({
            "district": format_name(slug),
            "url": build_url(slug)
        })

    df = pd.DataFrame(rows)
    df.to_csv(DISTRICTS_FILE, index=False)

    print(f"\nGenerated {len(df)} districts.")
    print(f"Saved -> {DISTRICTS_FILE}")

if __name__ == "__main__":
    main()