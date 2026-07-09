import os
import re
import pandas as pd
import numpy as np

# =====================================================
# Configuration
# =====================================================

INPUT_FILE = "data/thane_ngos.csv"
OUTPUT_FILE = "data/cleaned_ngos.csv"
DISTRICT = "Thane"

# =====================================================
# Helper Functions
# =====================================================

def clean_text(text):
    if pd.isna(text):
        return np.nan

    text = str(text)
    text = text.replace("\xa0", " ")
    text = text.replace("Tweet Related", "")
    text = text.replace("😕", "")
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    if text == "":
        return np.nan

    return text

def split_purpose_mission(purpose, mission):

    purpose = clean_text(purpose)
    mission = clean_text(mission)
    if pd.notna(purpose):
        if "Aim/Objective/Mission" in purpose:
            parts = re.split(
                r"Aim\/Objective\/Mission\s*:",
                purpose,
                flags=re.IGNORECASE,
            )
            if len(parts) == 2:
                purpose = clean_text(parts[0])
                mission = clean_text(parts[1])

    return purpose, mission

def clean_phone(phone):
    if pd.isna(phone):
        return np.nan

    phone = str(phone)
    phone = phone.replace(";", ",")
    phone = phone.replace("/", ",")

    numbers = []

    for item in phone.split(","):
        item = item.strip()
        digits = re.sub(r"\D", "", item)

        if digits != "":
            numbers.append(digits)
    numbers = list(dict.fromkeys(numbers))

    if not numbers:
        return np.nan
    return ",".join(numbers)


def clean_website(site):
    if pd.isna(site):
        return np.nan

    site = str(site).strip()
    if site == "":
        return np.nan
    if not site.startswith(("http://", "https://")):
        site = "https://" + site

    return site


def clean_email(email):
    if pd.isna(email):
        return np.nan
    email = str(email).strip().lower()
    if email == "":
        return np.nan
    return email

def clean_address(address):

    if pd.isna(address):
        return np.nan
    address = str(address)
    address = address.replace("\n", " ")
    address = address.replace("\r", " ")
    address = re.sub(r"\s+", " ", address)
    address = address.strip()

    if address == "":
        return np.nan
    return address


# =====================================================
# Main Cleaning
# =====================================================

def main():
    print("=" * 60)
    print("NGOConnect AI - Data Cleaning")
    print("=" * 60)
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"{INPUT_FILE} not found.")

    df = pd.read_csv(INPUT_FILE)
    print(f"\nLoaded {len(df)} records.")

    # -------------------------------------------------
    # Remove duplicate NGOs
    # -------------------------------------------------

    before = len(df)
    df.drop_duplicates(subset=["url"], inplace=True)
    after = len(df)
    print(f"Removed {before-after} duplicate records.")

    # -------------------------------------------------
    # Clean text fields
    # -------------------------------------------------

    text_columns = [
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
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].apply(clean_text)

    # -------------------------------------------------
    # Split Purpose / Mission
    # -------------------------------------------------

    purposes = []
    missions = []
    for p, m in zip(df["purpose"], df["mission"]):
        p2, m2 = split_purpose_mission(p, m)
        purposes.append(p2)
        missions.append(m2)
    df["purpose"] = purposes
    df["mission"] = missions

    # -------------------------------------------------
    # Standardize Fields
    # -------------------------------------------------

    df["phone"] = df["phone"].apply(clean_phone)
    df["mobile"] = df["mobile"].apply(clean_phone)
    df["website"] = df["website"].apply(clean_website)
    df["email"] = df["email"].apply(clean_email)
    df["address"] = df["address"].apply(clean_address)

    # -------------------------------------------------
    # Remove Invalid Rows
    # -------------------------------------------------

    before = len(df)
    df = df[df["name"].notna()]
    after = len(df)
    print(f"Removed {before-after} invalid rows.")

    # -------------------------------------------------
    # Add District
    # -------------------------------------------------

    df["district"] = DISTRICT

    # -------------------------------------------------
    # Reorder Columns
    # -------------------------------------------------

    columns = [
        "name",
        "district",
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
    df = df[columns]
    # -------------------------------------------------
    # Sort
    # -------------------------------------------------
    df = df.sort_values("name")
    # -------------------------------------------------
    # Save
    # -------------------------------------------------

    os.makedirs("data", exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"\nSaved cleaned dataset to:")
    print(OUTPUT_FILE)
    print(f"\nFinal NGO Count : {len(df)}")
    print("\nCleaning completed successfully.")

if __name__ == "__main__":
    main()