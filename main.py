import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent

URLS_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "tutor_urls.json"
)

RAW_PROFILES_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "tutor_profiles.json"
)

CLEAN_PROFILES_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "tutor_profiles_clean.json"
)

RAW_VALIDATION_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "validation_raw.json"
)

CLEAN_VALIDATION_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "validation_clean.json"
)


def run_command(
    command: list[str],
) -> None:

    print()
    print("=" * 70)
    print(
        "Running:",
        " ".join(command),
    )
    print("=" * 70)

    subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=True,
    )


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Run the Owl Tutors scraping "
            "and cleaning pipeline."
        )
    )

    parser.add_argument(
        "--refresh",
        action="store_true",
        help=(
            "Force fresh URL collection "
            "and profile scraping."
        ),
    )

    args = parser.parse_args()

    python = sys.executable

    print()
    print("=" * 70)
    print("OWL TUTORS DATA PIPELINE")
    print("=" * 70)

    # --------------------------------------------------
    # Step 1: Collect tutor URLs
    # --------------------------------------------------

    if (
        args.refresh
        or not URLS_PATH.exists()
    ):

        print()
        print(
            "Step 1/5: "
            "Collecting tutor URLs..."
        )

        run_command(
            [
                python,
                "src/collect_urls.py",
            ]
        )

    else:

        print()
        print(
            "Step 1/5: "
            "Tutor URLs already exist. "
            "Skipping."
        )

    # --------------------------------------------------
    # Step 2: Scrape profiles
    # --------------------------------------------------

    if (
        args.refresh
        or not RAW_PROFILES_PATH.exists()
    ):

        print()
        print(
            "Step 2/5: "
            "Scraping tutor profiles..."
        )

        run_command(
            [
                python,
                "src/scrape_profiles.py",
            ]
        )

    else:

        print()
        print(
            "Step 2/5: "
            "Raw tutor profiles already exist. "
            "Skipping."
        )

    # --------------------------------------------------
    # Step 3: Validate raw profiles
    # --------------------------------------------------

    print()
    print(
        "Step 3/5: "
        "Validating raw profiles..."
    )

    run_command(
        [
            python,
            "src/validate_profiles.py",
            "--input",
            "data/raw/tutor_profiles.json",
            "--output",
            "data/processed/validation_raw.json",
        ]
    )

    # --------------------------------------------------
    # Step 4: Clean profiles
    # --------------------------------------------------

    print()
    print(
        "Step 4/5: "
        "Cleaning profiles..."
    )

    run_command(
        [
            python,
            "src/clean_profiles.py",
        ]
    )

    # --------------------------------------------------
    # Step 5: Validate clean profiles
    # --------------------------------------------------

    print()
    print(
        "Step 5/5: "
        "Validating cleaned profiles..."
    )

    run_command(
        [
            python,
            "src/validate_profiles.py",
            "--input",
            "data/processed/tutor_profiles_clean.json",
            "--output",
            "data/processed/validation_clean.json",
        ]
    )

    print()
    print("=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)

    print(
        f"Raw profiles:\n"
        f"{RAW_PROFILES_PATH}"
    )

    print()

    print(
        f"Clean profiles:\n"
        f"{CLEAN_PROFILES_PATH}"
    )

    print()

    print(
        f"Raw validation:\n"
        f"{RAW_VALIDATION_PATH}"
    )

    print()

    print(
        f"Clean validation:\n"
        f"{CLEAN_VALIDATION_PATH}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()