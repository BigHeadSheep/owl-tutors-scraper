import json
import time
from pathlib import Path
from collections import Counter

import requests


AJAX_URL = "https://owltutors.co.uk/wp-admin/admin-ajax.php"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "tutor_urls.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/154.0 Safari/537.36"
    ),
    "Referer": "https://owltutors.co.uk/tutors/",
}


def fetch_tutor_page(page: int, offset: int) -> dict:
    """
    Fetch one page of tutor search results from Owl Tutors.
    """

    search_params = {
        "page": str(page),
        "offset": str(offset),
    }

    payload = {
        "action": "ot_tutor_search_filter",
        "search": json.dumps(search_params),
    }

    response = requests.post(
        AJAX_URL,
        headers=HEADERS,
        data=payload,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def collect_all_tutor_ids() -> list[str]:
    """
    Collect all tutor IDs by paginating through the search API.
    """

    all_tutor_ids = []

    page = 1
    offset = 0
    total = None

    while True:
        print(
            f"Fetching page {page} "
            f"(offset={offset})..."
        )

        data = fetch_tutor_page(
            page=page,
            offset=offset,
        )

        query_data = data.get("query", {})

        tutor_ids = query_data.get("tutor_ids", [])

        if total is None:
            total = data.get("total")

            print(
                f"API reports {total} tutors in total."
            )

        if not tutor_ids:
            print("No more tutor IDs returned.")
            break

        all_tutor_ids.extend(tutor_ids)

        print(
            f"    Found {len(tutor_ids)} tutors. "
            f"Collected {len(all_tutor_ids)} / {total}"
        )

        if total is not None and len(all_tutor_ids) >= total:
            break

        page += 1
        offset += len(tutor_ids)

        time.sleep(1)

    return all_tutor_ids


def build_tutor_urls(
    tutor_ids: list[str],
) -> list[str]:
    """
    Convert tutor IDs into profile URLs.
    """

    unique_ids = sorted(
        set(tutor_ids),
        key=int,
    )

    return [
        f"https://owltutors.co.uk/tutor/{tutor_id}/"
        for tutor_id in unique_ids
    ]


def save_urls(urls: list[str]) -> None:
    """
    Save tutor profile URLs to JSON.
    """

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            urls,
            file,
            indent=2,
            ensure_ascii=False,
        )


def main():
    print("Starting Owl Tutors tutor collection...")
    print()

    tutor_ids = collect_all_tutor_ids()

    counts = Counter(tutor_ids)

    duplicates = {
        tutor_id: count
        for tutor_id, count in counts.items()
        if count > 1
    }

    print()
    print("Duplicate tutor IDs:", duplicates)

    tutor_urls = build_tutor_urls(tutor_ids)

    save_urls(tutor_urls)

    print()
    print("=" * 50)
    print(
        f"API returned {len(tutor_ids)} tutor records."
    )
    print(
        f"Found {len(tutor_urls)} unique tutor profiles."
    )
    print(f"Saved to: {OUTPUT_PATH}")
    print("=" * 50)


if __name__ == "__main__":
    main()