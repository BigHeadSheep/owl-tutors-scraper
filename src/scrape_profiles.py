import re
import json
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup


PROJECT_ROOT = Path(__file__).resolve().parent.parent

URLS_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "tutor_urls.json"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "tutor_profiles.json"
)

ERROR_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "scrape_errors.json"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/154.0 Safari/537.36"
    )
}


def clean_text(text: str) -> str:
    return " ".join(text.split())


def get_section(
    soup: BeautifulSoup,
    heading_text: str,
) -> list:
    """
    Return elements after an H2 heading until the next H2.
    """

    heading = None

    for h2 in soup.find_all("h2"):
        text = clean_text(h2.get_text(" ", strip=True))

        if text.lower() == heading_text.lower():
            heading = h2
            break

    if heading is None:
        return []

    elements = []

    for element in heading.find_all_next():
        if element == heading:
            continue

        if element.name == "h2":
            break

        elements.append(element)

    return elements


def extract_subjects_and_levels(
    soup: BeautifulSoup,
) -> list[dict]:
    section = get_section(
        soup,
        "Subjects & Levels",
    )

    results = []

    for element in section:
        if element.name != "a":
            continue

        subject = clean_text(
            element.get_text(" ", strip=True)
        )

        href = element.get("href", "")

        if not href:
            continue

        if "/tutors/" not in href and "-tutors" not in href:
            continue

        details = None

        next_text = element.next_sibling

        if next_text:
            candidate = clean_text(str(next_text))

            if candidate.startswith("("):
                details = candidate.strip("()")

        results.append(
            {
                "subject": subject,
                "details": details,
            }
        )

    # Remove duplicates while preserving order
    unique = []
    seen = set()

    for item in results:
        key = (
            item["subject"],
            item["details"],
        )

        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique


def extract_qualifications(
    soup: BeautifulSoup,
) -> list[dict]:
    section = get_section(
        soup,
        "Qualifications",
    )

    qualifications = []

    headings = [
        element
        for element in section
        if element.name == "h4"
    ]

    for heading in headings:
        title = clean_text(
            heading.get_text(" ", strip=True)
        )

        values = []

        for sibling in heading.find_all_next():
            if sibling == heading:
                continue

            if sibling.name in ["h2", "h4"]:
                break

            if sibling.name in ["p", "div", "span"]:
                text = clean_text(
                    sibling.get_text(
                        " ",
                        strip=True,
                    )
                )

                if (
                    text
                    and text not in values
                    and text != title
                ):
                    values.append(text)

        year = None
        institution = None

        for value in values:
            if re.fullmatch(r"\d{4}", value):
                year = int(value)

            elif institution is None:
                institution = value

        qualifications.append(
            {
                "qualification": title,
                "year": year,
                "institution": institution,
            }
        )

    return qualifications


def extract_availability(
    soup: BeautifulSoup,
) -> str | None:
    section = get_section(
        soup,
        "Availability",
    )

    for element in section:
        if element.name == "p":
            text = clean_text(
                element.get_text(" ", strip=True)
            )

            if text:
                return text

    return None


def extract_school_entrance(
    soup: BeautifulSoup,
) -> tuple[list[str], str | None]:

    section = get_section(
        soup,
        "School Entrance Experience",
    )

    schools = []
    paragraphs = []

    for element in section:

        # -------------------------
        # School links
        # -------------------------
        if element.name == "a":

            text = clean_text(
                element.get_text(" ", strip=True)
            )

            # Only keep links that are actually school guide links
            if "view guide" not in text.lower():
                continue

            # Remove "- View guide"
            school_name = re.sub(
                r"\s*[-–—]?\s*View guide.*$",
                "",
                text,
                flags=re.IGNORECASE,
            ).strip()

            if (
                school_name
                and school_name not in schools
            ):
                schools.append(school_name)

        # -------------------------
        # Experience text
        # -------------------------
        elif element.name == "p":

            text = clean_text(
                element.get_text(" ", strip=True)
            )

            if not text:
                continue

            excluded_phrases = [
                "ready to discuss tuition",
                "add this tutor",
                "speak to an expert",
                "check availability",
            ]

            if any(
                phrase in text.lower()
                for phrase in excluded_phrases
            ):
                continue

            paragraphs.append(text)

    experience_text = (
        " ".join(paragraphs)
        if paragraphs
        else None
    )

    return schools, experience_text


def extract_bio(
    soup: BeautifulSoup,
) -> str | None:
    """
    Bio is the narrative immediately following
    Teaching Modes & Locations on this profile layout.
    """

    target = None

    for h3 in soup.find_all("h3"):
        text = clean_text(
            h3.get_text(" ", strip=True)
        )

        if "Teaching Modes & Locations" in text:
            target = h3
            break

    if target is None:
        return None

    paragraphs = []

    for element in target.find_all_next():
        if element == target:
            continue

        if element.name == "h2":
            break

        if element.name == "p":
            text = clean_text(
                element.get_text(" ", strip=True)
            )

            if (
                text
                and text.lower() != "online"
            ):
                paragraphs.append(text)

    if not paragraphs:
        return None

    return " ".join(paragraphs)


def extract_teaching_locations(
    soup: BeautifulSoup,
) -> list[str]:
    heading = None

    for h2 in soup.find_all("h2"):
        text = clean_text(
            h2.get_text(" ", strip=True)
        )

        if text.lower().startswith("here's where"):
            heading = h2
            break

    if heading is None:
        return []

    locations = []

    for element in heading.find_all_next():
        if element == heading:
            continue

        if element.name == "h2":
            break

        if element.name == "li":
            text = clean_text(
                element.get_text(" ", strip=True)
            )

            if text and text not in locations:
                locations.append(text)

    return locations


def extract_profile(
    html: str,
    url: str,
) -> dict:
    soup = BeautifulSoup(html, "lxml")

    page_text = clean_text(
        soup.get_text(" ", strip=True)
    )

    name_tag = soup.find("h1")

    name = (
        clean_text(name_tag.get_text())
        if name_tag
        else None
    )

    tutor_id_match = re.search(
        r"/tutor/(\d+)/",
        url,
    )

    tutor_id = (
        tutor_id_match.group(1)
        if tutor_id_match
        else None
    )

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

    rate_match = re.search(
        r"From £([\d,.]+) per hour",
        page_text,
        re.IGNORECASE,
    )

    hourly_rate_from = (
        float(
            rate_match
            .group(1)
            .replace(",", "")
        )
        if rate_match
        else None
    )

    headline = None

    if name_tag:
        for text_node in name_tag.find_all_next(
            string=True
        ):
            candidate = clean_text(
                str(text_node)
            )

            if (
                "Qualified to teach" in candidate
                and candidate != name
            ):
                headline = candidate
                break

    subjects_and_levels = (
        extract_subjects_and_levels(soup)
    )

    subjects = [
        item["subject"]
        for item in subjects_and_levels
    ]

    qualifications = (
        extract_qualifications(soup)
    )

    availability_text = (
        extract_availability(soup)
    )

    schools_prepared_for, (
        school_entrance_experience
    ) = extract_school_entrance(soup)

    bio = extract_bio(soup)

    teaching_locations = (
        extract_teaching_locations(soup)
    )

    badges = []

    for badge in [
        "Oxbridge",
        "Russell Group",
        "Examiner",
        "First",
        "Masters",
        "PhD",
    ]:
        if badge in page_text:
            badges.append(badge)

    return {
        "tutor_id": tutor_id,
        "name": name,
        "profile_url": url,
        "headline": headline,
        "qualified_year": qualified_year,
        "hourly_rate_from": hourly_rate_from,
        "online": "Online" in headline
        if headline
        else False,
        "home": "Home" in headline
        if headline
        else False,
        "enhanced_dbs": (
            "Enhanced DBS Status"
            in page_text
        ),
        "badges": badges,
        "subjects": subjects,
        "subjects_and_levels": (
            subjects_and_levels
        ),
        "qualifications": qualifications,
        "availability_text": (
            availability_text
        ),
        "schools_prepared_for": (
            schools_prepared_for
        ),
        "school_entrance_experience": (
            school_entrance_experience
        ),
        "teaching_locations": (
            teaching_locations
        ),
        "bio": bio,
    }


def load_tutor_urls() -> list[str]:
    with URLS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def load_existing_profiles() -> list[dict]:
    """
    Load previous checkpoint if the scraper
    was interrupted.
    """

    if not OUTPUT_PATH.exists():
        return []

    with OUTPUT_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def save_json(
    data,
    path: Path,
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


def fetch_profile_with_retry(
    url: str,
    max_retries: int = 3,
) -> str:

    for attempt in range(
        1,
        max_retries + 1,
    ):

        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=30,
            )

            response.raise_for_status()

            return response.text

        except requests.RequestException as error:

            print(
                f"    Attempt {attempt} failed: "
                f"{error}"
            )

            if attempt < max_retries:
                time.sleep(3)

    raise RuntimeError(
        f"Failed after {max_retries} attempts."
    )


def main():

    tutor_urls = load_tutor_urls()

    existing_profiles = (
        load_existing_profiles()
    )

    completed_ids = {
        profile["tutor_id"]
        for profile in existing_profiles
        if profile.get("tutor_id")
    }

    profiles = existing_profiles.copy()
    errors = []

    total = len(tutor_urls)

    print(
        f"Found {total} tutor URLs."
    )

    print(
        f"Already completed: "
        f"{len(completed_ids)}"
    )

    print()

    for index, url in enumerate(
        tutor_urls,
        start=1,
    ):

        tutor_id_match = re.search(
            r"/tutor/(\d+)/",
            url,
        )

        tutor_id = (
            tutor_id_match.group(1)
            if tutor_id_match
            else None
        )

        if tutor_id in completed_ids:

            print(
                f"[{index}/{total}] "
                f"Skipping tutor {tutor_id} "
                f"(already scraped)"
            )

            continue

        print(
            f"[{index}/{total}] "
            f"Fetching {url}"
        )

        try:

            html = fetch_profile_with_retry(
                url
            )

            profile = extract_profile(
                html=html,
                url=url,
            )

            profiles.append(profile)

            print(
                f"    OK: "
                f"{profile.get('name')}"
            )

            # Save checkpoint after every tutor
            save_json(
                profiles,
                OUTPUT_PATH,
            )

        except Exception as error:

            print(
                f"    ERROR: {error}"
            )

            errors.append(
                {
                    "tutor_id": tutor_id,
                    "url": url,
                    "error": str(error),
                }
            )

            save_json(
                errors,
                ERROR_PATH,
            )

        # Responsible request rate
        time.sleep(1)

    print()
    print("=" * 60)
    print(
        f"Finished scraping."
    )
    print(
        f"Successful profiles: "
        f"{len(profiles)}"
    )
    print(
        f"Errors: {len(errors)}"
    )
    print(
        f"Profiles saved to: "
        f"{OUTPUT_PATH}"
    )

    if errors:
        print(
            f"Errors saved to: "
            f"{ERROR_PATH}"
        )

    print("=" * 60)


if __name__ == "__main__":
    main()