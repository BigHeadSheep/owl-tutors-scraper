import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "tutor_profiles.json"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "tutor_profiles_clean.json"
)


def load_profiles() -> list[dict]:
    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def save_profiles(
    profiles: list[dict],
) -> None:

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            profiles,
            file,
            indent=2,
            ensure_ascii=False,
        )


def clean_whitespace(
    value: str | None,
) -> str | None:

    if value is None:
        return None

    value = " ".join(
        value.split()
    )

    return value or None


def clean_bio(
    bio: str | None,
) -> str | None:
    """
    Remove teaching-mode labels that were accidentally
    captured at the beginning of the biography.
    """

    bio = clean_whitespace(bio)

    if not bio:
        return None

    prefixes = [
        "Home Residential ",
        "Residential Home ",
        "Home ",
        "Residential ",
        "Online ",
    ]

    changed = True

    while changed:
        changed = False

        for prefix in prefixes:
            if bio.startswith(prefix):
                bio = bio[
                    len(prefix):
                ].strip()

                changed = True
                break

    return bio or None


def clean_qualifications(
    qualifications: list[dict] | None,
) -> list[dict]:

    if not qualifications:
        return []

    cleaned = []

    for qualification in qualifications:

        title = clean_whitespace(
            qualification.get(
                "qualification"
            )
        )

        institution = clean_whitespace(
            qualification.get(
                "institution"
            )
        )

        year = qualification.get(
            "year"
        )

        # Remove completely blank qualification rows
        if (
            title is None
            and institution is None
            and year is None
        ):
            continue

        cleaned.append(
            {
                "qualification": (
                    title
                ),
                "year": year,
                "institution": (
                    institution
                ),
            }
        )

    return cleaned


def clean_string_list(
    values: list[str] | None,
) -> list[str]:

    if not values:
        return []

    cleaned = []
    seen = set()

    for value in values:

        value = clean_whitespace(
            value
        )

        if not value:
            continue

        if value not in seen:
            seen.add(value)
            cleaned.append(value)

    return cleaned


def clean_subjects_and_levels(
    values: list[dict] | None,
) -> list[dict]:

    if not values:
        return []

    cleaned = []
    seen = set()

    for item in values:

        subject = clean_whitespace(
            item.get("subject")
        )

        details = clean_whitespace(
            item.get("details")
        )

        if not subject:
            continue

        key = (
            subject,
            details,
        )

        if key in seen:
            continue

        seen.add(key)

        cleaned.append(
            {
                "subject": subject,
                "details": details,
            }
        )

    return cleaned


def clean_profile(
    profile: dict,
) -> dict:

    cleaned = profile.copy()

    # -------------------------
    # Basic text fields
    # -------------------------

    for field in [
        "name",
        "profile_url",
        "headline",
        "availability_text",
        "school_entrance_experience",
    ]:
        cleaned[field] = (
            clean_whitespace(
                profile.get(field)
            )
        )

    # -------------------------
    # Bio
    # -------------------------

    cleaned["bio"] = clean_bio(
        profile.get("bio")
    )

    # -------------------------
    # Lists
    # -------------------------

    cleaned["badges"] = (
        clean_string_list(
            profile.get("badges")
        )
    )

    cleaned["subjects"] = (
        clean_string_list(
            profile.get("subjects")
        )
    )

    cleaned[
        "schools_prepared_for"
    ] = clean_string_list(
        profile.get(
            "schools_prepared_for"
        )
    )

    cleaned[
        "teaching_locations"
    ] = clean_string_list(
        profile.get(
            "teaching_locations"
        )
    )

    # -------------------------
    # Nested fields
    # -------------------------

    cleaned[
        "subjects_and_levels"
    ] = clean_subjects_and_levels(
        profile.get(
            "subjects_and_levels"
        )
    )

    cleaned[
        "qualifications"
    ] = clean_qualifications(
        profile.get(
            "qualifications"
        )
    )

    return cleaned


def main():

    print(
        f"Loading raw profiles from:\n"
        f"{INPUT_PATH}"
    )

    profiles = load_profiles()

    cleaned_profiles = [
        clean_profile(profile)
        for profile in profiles
    ]

    save_profiles(
        cleaned_profiles
    )

    print()
    print("=" * 60)
    print("CLEANING COMPLETE")
    print("=" * 60)

    print(
        f"Raw profiles: "
        f"{len(profiles)}"
    )

    print(
        f"Clean profiles: "
        f"{len(cleaned_profiles)}"
    )

    print(
        f"Saved to:\n"
        f"{OUTPUT_PATH}"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()