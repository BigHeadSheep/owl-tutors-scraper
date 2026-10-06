import re
import requests
from bs4 import BeautifulSoup


TEST_URL = "https://owltutors.co.uk/tutor/21213/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/154.0 Safari/537.36"
    )
}


def fetch_profile(url: str) -> str:
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    return response.text


def clean_text(text: str) -> str:
    return " ".join(text.split())


def extract_basic_info(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")

    page_text = clean_text(soup.get_text(" ", strip=True))

    # -------------------------
    # Name
    # -------------------------
    name_tag = soup.find("h1")
    name = clean_text(name_tag.get_text()) if name_tag else None

    # -------------------------
    # Tutor ID
    # -------------------------
    tutor_id_match = re.search(r"/tutor/(\d+)/", url)
    tutor_id = tutor_id_match.group(1) if tutor_id_match else None

    # -------------------------
    # Qualified year
    # -------------------------
    qualified_match = re.search(
        r"Qualified to teach in (\d{4})",
        page_text,
        re.IGNORECASE,
    )

    qualified_year = (
        int(qualified_match.group(1))
        if qualified_match
        else None
    )

    # -------------------------
    # Hourly rate
    # -------------------------
    rate_match = re.search(
        r"From £([\d,.]+) per hour",
        page_text,
        re.IGNORECASE,
    )

    hourly_rate_from = (
        float(rate_match.group(1).replace(",", ""))
        if rate_match
        else None
    )

    # -------------------------
    # Teaching mode
    # -------------------------
    online = bool(
        re.search(r"\bOnline\b", page_text)
    )

    home = bool(
        re.search(r"\bHome\b", page_text)
    )

    # -------------------------
    # DBS
    # -------------------------
    enhanced_dbs = (
        "Enhanced DBS Status" in page_text
    )

    # -------------------------
    # Profile headline
    # Example:
    # English teacher • Qualified to teach in 2008 • Online
    # -------------------------
    headline = None

    if name_tag:
        next_text = name_tag.find_next(string=True)

        while next_text:
            candidate = clean_text(str(next_text))

            if (
                candidate
                and candidate != name
                and "Qualified to teach" in candidate
            ):
                headline = candidate
                break

            next_text = next_text.find_next(string=True)

    return {
        "tutor_id": tutor_id,
        "name": name,
        "profile_url": url,
        "headline": headline,
        "qualified_year": qualified_year,
        "hourly_rate_from": hourly_rate_from,
        "online": online,
        "home": home,
        "enhanced_dbs": enhanced_dbs,
    }


def main():
    print(f"Fetching: {TEST_URL}")

    html = fetch_profile(TEST_URL)

    tutor = extract_basic_info(
        html=html,
        url=TEST_URL,
    )

    print()
    print("Parsed tutor information:")
    print("-" * 40)

    for key, value in tutor.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()