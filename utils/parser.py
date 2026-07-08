import re


FIELDS = [
    "Add.",
    "Phone",
    "Mobile",
    "Email",
    "Website",
    "Contact Person",
    "Purpose",
    "Aims/Objectives/Mission",
]


def clean_text(text: str) -> str:
    if text is None:
        return ""

    text = (
        text.replace("\xa0", " ")
            .replace("😕", "")
            .replace("?", "")
    )

    return " ".join(text.split()).strip()


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

        if line.startswith(field_name):

            capture = True

            if ":" in line:
                value = line.split(":", 1)[1].strip()

                if value:
                    collected.append(value)

            continue

        if capture:

            if any(line.startswith(field) for field in FIELDS):
                break

            collected.append(line)

    return "\n".join(collected).strip()


def extract_phone_numbers(text):
    """
    Extract phone/mobile numbers while preserving each one separately.
    """

    if not text:
        return ""

    text = text.replace("\n", " ")

    # Find numbers with optional +, spaces, hyphens
    matches = re.findall(r"\+?\d[\d\s\-()]{6,}\d", text)

    numbers = []

    for match in matches:

        number = re.sub(r"[^\d+]", "", match)

        numbers.append(number)

    # Remove duplicates
    numbers = list(dict.fromkeys(numbers))

    return ", ".join(numbers)


def extract_emails(text):

    if not text:
        return ""

    emails = re.findall(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text,
    )

    emails = list(dict.fromkeys(emails))

    return ", ".join(emails)


def extract_websites(text):

    if not text:
        return ""

    websites = re.findall(
        r"(https?://\S+|www\.\S+)",
        text,
    )

    websites = [site.rstrip(".,)") for site in websites]

    websites = list(dict.fromkeys(websites))

    return ", ".join(websites)


def parse_entry(lines):

    address = clean_text(extract_field(lines, "Add."))

    phone = extract_phone_numbers(
        extract_field(lines, "Phone")
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