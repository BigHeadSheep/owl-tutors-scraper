import argparse
import json
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_profiles(input_path: Path) -> list[dict]:
    with input_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def save_report(
    report: dict,
    output_path: Path,
) -> None:

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )


def find_missing(
    profiles: list[dict],
    field: str,
) -> list[str]:
    """
    Return tutor IDs where a field is missing,
    None, empty string, or empty list.
    """

    missing_ids = []

    for profile in profiles:
        value = profile.get(field)

        if value in [None, "", []]:
            missing_ids.append(
                profile.get("tutor_id")
            )

    return missing_ids


def find_duplicate_ids(
    profiles: list[dict],
) -> dict[str, int]:
    tutor_ids = [
        profile.get("tutor_id")
        for profile in profiles
        if profile.get("tutor_id")
    ]

    counts = Counter(tutor_ids)

    return {
        tutor_id: count
        for tutor_id, count in counts.items()
        if count > 1
    }


def find_invalid_years(
    profiles: list[dict],
) -> list[dict]:
    """
    Flag obviously implausible qualified years.
    """

    issues = []

    for profile in profiles:
        year = profile.get(
            "qualified_year"
        )

        if year is None:
            continue

        if year < 1950 or year > 2030:
            issues.append(
                {
                    "tutor_id": profile.get(
                        "tutor_id"
                    ),
                    "name": profile.get(
                        "name"
                    ),
                    "qualified_year": year,
                }
            )

    return issues


def find_invalid_rates(
    profiles: list[dict],
) -> list[dict]:
    """
    Flag obviously implausible hourly rates.
    """

    issues = []

    for profile in profiles:
        rate = profile.get(
            "hourly_rate_from"
        )

        if rate is None:
            continue

        if rate <= 0 or rate > 1000:
            issues.append(
                {
                    "tutor_id": profile.get(
                        "tutor_id"
                    ),
                    "name": profile.get(
                        "name"
                    ),
                    "hourly_rate_from": rate,
                }
            )

    return issues


def find_blank_qualifications(
    profiles: list[dict],
) -> list[dict]:
    issues = []

    for profile in profiles:

        qualifications = (
            profile.get(
                "qualifications",
                [],
            )
        )

        for index, qualification in enumerate(
            qualifications
        ):

            title = qualification.get(
                "qualification"
            )

            if not title or not title.strip():
                issues.append(
                    {
                        "tutor_id": (
                            profile.get(
                                "tutor_id"
                            )
                        ),
                        "name": (
                            profile.get(
                                "name"
                            )
                        ),
                        "qualification_index": (
                            index
                        ),
                        "qualification": (
                            qualification
                        ),
                    }
                )

    return issues


def find_bio_prefix_issues(
    profiles: list[dict],
) -> list[dict]:
    """
    Detect teaching-mode labels accidentally
    included at the start of bios.
    """

    suspicious_prefixes = [
        "Home ",
        "Residential ",
        "Home Residential ",
        "Residential Home ",
    ]

    issues = []

    for profile in profiles:

        bio = profile.get("bio")

        if not bio:
            continue

        for prefix in suspicious_prefixes:

            if bio.startswith(prefix):
                issues.append(
                    {
                        "tutor_id": (
                            profile.get(
                                "tutor_id"
                            )
                        ),
                        "name": (
                            profile.get(
                                "name"
                            )
                        ),
                        "prefix": prefix.strip(),
                        "bio_start": bio[:120],
                    }
                )

                break

    return issues


def find_duplicates_in_list_field(
    profiles: list[dict],
    field: str,
) -> list[dict]:

    issues = []

    for profile in profiles:

        values = profile.get(
            field,
            [],
        )

        if not values:
            continue

        counts = Counter(values)

        duplicates = {
            value: count
            for value, count in counts.items()
            if count > 1
        }

        if duplicates:
            issues.append(
                {
                    "tutor_id": (
                        profile.get(
                            "tutor_id"
                        )
                    ),
                    "name": (
                        profile.get(
                            "name"
                        )
                    ),
                    "duplicates": duplicates,
                }
            )

    return issues


def build_report(
    profiles: list[dict],
) -> dict:

    fields_to_check = [
        "tutor_id",
        "name",
        "profile_url",
        "headline",
        "qualified_year",
        "hourly_rate_from",
        "subjects",
        "qualifications",
        "availability_text",
        "bio",
    ]

    missing_fields = {}

    for field in fields_to_check:

        ids = find_missing(
            profiles,
            field,
        )

        missing_fields[field] = {
            "count": len(ids),
            "tutor_ids": ids,
        }

    report = {
        "summary": {
            "total_profiles": (
                len(profiles)
            ),
            "unique_tutor_ids": (
                len(
                    {
                        profile.get(
                            "tutor_id"
                        )
                        for profile
                        in profiles
                        if profile.get(
                            "tutor_id"
                        )
                    }
                )
            ),
        },

        "duplicate_tutor_ids": (
            find_duplicate_ids(
                profiles
            )
        ),

        "missing_fields": (
            missing_fields
        ),

        "invalid_qualified_years": (
            find_invalid_years(
                profiles
            )
        ),

        "invalid_hourly_rates": (
            find_invalid_rates(
                profiles
            )
        ),

        "blank_qualifications": (
            find_blank_qualifications(
                profiles
            )
        ),

        "bio_prefix_issues": (
            find_bio_prefix_issues(
                profiles
            )
        ),

        "duplicate_schools": (
            find_duplicates_in_list_field(
                profiles,
                "schools_prepared_for",
            )
        ),

        "duplicate_teaching_locations": (
            find_duplicates_in_list_field(
                profiles,
                "teaching_locations",
            )
        ),
    }

    return report


def print_summary(
    report: dict,
    output_path: Path,
) -> None:

    print()
    print("=" * 60)
    print("OWL TUTORS DATA QUALITY REPORT")
    print("=" * 60)

    summary = report["summary"]

    print(
        f"Total profiles: "
        f"{summary['total_profiles']}"
    )

    print(
        f"Unique tutor IDs: "
        f"{summary['unique_tutor_ids']}"
    )

    duplicate_ids = (
        report[
            "duplicate_tutor_ids"
        ]
    )

    print(
        f"Duplicate tutor IDs: "
        f"{len(duplicate_ids)}"
    )

    print()
    print("Missing fields")
    print("-" * 60)

    for field, data in (
        report[
            "missing_fields"
        ].items()
    ):

        print(
            f"{field:25} "
            f"{data['count']}"
        )

    print()
    print("Other issues")
    print("-" * 60)

    print(
        "Invalid qualified years: "
        f"{len(report['invalid_qualified_years'])}"
    )

    print(
        "Invalid hourly rates: "
        f"{len(report['invalid_hourly_rates'])}"
    )

    print(
        "Blank qualification rows: "
        f"{len(report['blank_qualifications'])}"
    )

    print(
        "Bio prefix issues: "
        f"{len(report['bio_prefix_issues'])}"
    )

    print(
        "Profiles with duplicate schools: "
        f"{len(report['duplicate_schools'])}"
    )

    print(
        "Profiles with duplicate locations: "
        f"{len(report['duplicate_teaching_locations'])}"
    )

    print()
    print(
        f"Full report saved to:\n"
        f"{output_path}"
    )

    print("=" * 60)


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Validate Owl Tutors profile data."
        )
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to input JSON file.",
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Path to validation report JSON.",
    )

    args = parser.parse_args()

    input_path = Path(args.input)

    output_path = Path(args.output)

    if not input_path.is_absolute():
        input_path = (
            PROJECT_ROOT
            / input_path
        )

    if not output_path.is_absolute():
        output_path = (
            PROJECT_ROOT
            / output_path
        )

    print(
        f"Loading profiles from:\n"
        f"{input_path}"
    )

    profiles = load_profiles(
        input_path
    )

    report = build_report(
        profiles
    )

    save_report(
        report,
        output_path,
    )

    print_summary(
        report,
        output_path,
    )


if __name__ == "__main__":
    main()