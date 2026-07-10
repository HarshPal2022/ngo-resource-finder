import re

# Field names that may appear on the NGO pages
FIELDS = [
    "Add",
    "Phone",
    "Tel",
    "Mobile",
    "Email",
    "Website",
    "Contact Person",
    "Purpose",
    "Aim/Objective/Mission",
    "Aims/Objectives/Mission",
]


def clean_text(text: str) -> str:
    """
    Clean extracted text.
    """

    if text is None:
        return ""

    text = (
        text.replace("\xa0", " ")
        .replace("😕", "")
        .replace("?", "")
        .replace("•", " ")
    )

    return " ".join(text.split()).strip()


def normalize_field_name(text):
    """
    Normalize labels like:
        Add :
        Add.:
        Add.
        Add
    into
        Add

    Also handles:
        Aim/Objective/Mission
        Aims/Objectives/Mission
    """

    text = clean_text(text)

    if ":" in text:
        text = text.split(":", 1)[0]

    text = text.replace(".", "").strip()

    return text


def extract_field(lines, field_name):
    """
    Extract all lines belonging to a field until the next field starts.
    """

    capture = False
    collected = []

    for line in lines:

        line = clean_text(line)

        if not line:
            continue

        normalized = normalize_field_name(line)

        if normalized == normalize_field_name(field_name):

            capture = True

            if ":" in line:

                value = line.split(":", 1)[1].strip()

                if value:
                    collected.append(value)

            continue

        if capture:

            is_new_field = False

            for field in FIELDS:

                if normalize_field_name(line) == normalize_field_name(field):
                    is_new_field = True
                    break

            if is_new_field:
                break

            if line.lower() in ("tweet", "related"):
                break

            collected.append(line)

    return "\n".join(collected).strip()


def extract_phone_numbers(text):
    """
    Extract all phone numbers.
    """

    if not text:
        return ""

    text = text.replace("\n", " ")

    matches = re.findall(
        r"\+?\d[\d\s\-()]{6,}\d",
        text,
    )

    numbers = []

    for match in matches:

        number = re.sub(r"[^\d+]", "", match)

        if number:
            numbers.append(number)

    numbers = list(dict.fromkeys(numbers))

    return ", ".join(numbers)


def extract_emails(text):
    """
    Extract email addresses.
    """

    if not text:
        return ""

    emails = re.findall(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text,
    )

    emails = list(dict.fromkeys(emails))

    return ", ".join(emails)


def extract_websites(text):
    """
    Extract website URLs.
    """

    if not text:
        return ""

    websites = re.findall(
        r"(https?://\S+|www\.\S+)",
        text,
    )

    cleaned = []

    for site in websites:

        site = site.rstrip(".,)")

        if not site.startswith("http"):
            site = "https://" + site

        cleaned.append(site)

    cleaned = list(dict.fromkeys(cleaned))

    return ", ".join(cleaned)


def parse_entry(lines):
    """
    Parse NGO information from extracted lines.
    """

    address = clean_text(
        extract_field(lines, "Add")
    )

    phone = extract_phone_numbers(
        extract_field(lines, "Phone")
    )

    if not phone:
        phone = extract_phone_numbers(
            extract_field(lines, "Tel")
        )

    mobile = extract_phone_numbers(
        extract_field(lines, "Mobile")
    )

    email = extract_emails(
        extract_field(lines, "Email")
    )

    website = extract_websites(
        extract_field(lines, "Website")
    )

    contact_person = clean_text(
        extract_field(lines, "Contact Person")
    )

    purpose = clean_text(
        extract_field(lines, "Purpose")
    )

    mission = clean_text(
        extract_field(lines, "Aims/Objectives/Mission")
    )

    if not mission:
        mission = clean_text(
            extract_field(lines, "Aim/Objective/Mission")
        )

    return {
        "address": address,
        "phone": phone,
        "mobile": mobile,
        "email": email,
        "website": website,
        "contact_person": contact_person,
        "purpose": purpose,
        "mission": mission,
    }