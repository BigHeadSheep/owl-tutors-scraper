import json
import re
from datetime import datetime
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "tutor_profiles_clean.json"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "owl_tutors.xlsx"
)


# ============================================================
# Configuration
# ============================================================

PRIORITY_SUBJECTS = [
    "7 Plus",
    "8 Plus",
    "11 Plus",
    "13 Plus",
    "16 Plus",
    "Other School Entrance",
    "University Admissions",
    "English",
    "Maths",
    "SEN",
    "Science",
    "Biology",
    "Chemistry",
    "Physics",
    "Economics",
    "Business",
    "History",
    "Geography",
    "French",
    "Spanish",
    "German",
    "Latin",
    "Mandarin",
    "Computer Science",
    "Psychology",
    "Politics",
    "Music",
    "Art",
]

PRIORITY_BADGES = [
    "Oxbridge",
    "Russell Group",
    "First",
    "Masters",
    "PhD",
    "Examiner",
]


# ============================================================
# Load data
# ============================================================

def load_profiles() -> list[dict]:
    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


# ============================================================
# Helper functions
# ============================================================

def yes_no(value: bool) -> str:
    return "Yes" if value else "No"


def join_list(
    values: list[str] | None,
) -> str:
    if not values:
        return ""

    return "; ".join(values)


def get_primary_role(
    headline: str | None,
) -> str | None:
    """
    Extract the role before the first bullet.

    Example:
    'Primary education teacher • Qualified to teach in 2008 • Online'
    ->
    'Primary education teacher'
    """

    if not headline:
        return None

    return headline.split("•")[0].strip()


def classify_availability(
    text: str | None,
) -> str:
    """
    Convert free-text availability into a simple category.
    """

    if not text:
        return "Unknown"

    lower = text.lower()

    if (
        "not able to take on any more students"
        in lower
        or "waiting list" in lower
    ):
        return "Waitlist"

    if (
        "only has space for" in lower
        or "accommodate" in lower
        or "space for 1 more" in lower
        or "space for 2 more" in lower
    ):
        return "Limited availability"

    if (
        "check availability" in lower
        or "add this tutor to your request"
        in lower
    ):
        return "Check availability"

    return "Available / unspecified"


def qualification_summary(
    qualifications: list[dict] | None,
) -> str:
    if not qualifications:
        return ""

    parts = []

    for qualification in qualifications:

        title = qualification.get(
            "qualification"
        )

        year = qualification.get(
            "year"
        )

        institution = qualification.get(
            "institution"
        )

        section = title or ""

        if institution:
            section += f" — {institution}"

        if year:
            section += f" ({year})"

        if section:
            parts.append(section)

    return "; ".join(parts)


def extract_postcodes(
    locations: list[str] | None,
) -> str:
    """
    Extract UK-style postcode districts appearing in
    teaching location strings.

    Examples:
    SW6, SW7, W8, SE21, E1
    """

    if not locations:
        return ""

    found = []

    pattern = re.compile(
        r"\b(?:"
        r"EC\d+[A-Z]?|"
        r"WC\d+[A-Z]?|"
        r"SW\d+[A-Z]?|"
        r"SE\d+[A-Z]?|"
        r"NW\d+[A-Z]?|"
        r"NE\d+[A-Z]?|"
        r"W\d+[A-Z]?|"
        r"E\d+[A-Z]?|"
        r"N\d+[A-Z]?"
        r")\b",
        re.IGNORECASE,
    )

    for location in locations:
        matches = pattern.findall(
            location
        )

        for postcode in matches:
            postcode = postcode.upper()

            if postcode not in found:
                found.append(postcode)

    return "; ".join(found)


def get_all_subjects(
    profiles: list[dict],
) -> list[str]:

    subject_set = set()

    for profile in profiles:
        subject_set.update(
            profile.get(
                "subjects",
                [],
            )
        )

    ordered = []

    for subject in PRIORITY_SUBJECTS:
        if subject in subject_set:
            ordered.append(subject)

    remaining = sorted(
        subject_set
        - set(ordered)
    )

    return ordered + remaining


def get_all_badges(
    profiles: list[dict],
) -> list[str]:

    badge_set = set()

    for profile in profiles:
        badge_set.update(
            profile.get(
                "badges",
                [],
            )
        )

    ordered = []

    for badge in PRIORITY_BADGES:
        if badge in badge_set:
            ordered.append(badge)

    remaining = sorted(
        badge_set
        - set(ordered)
    )

    return ordered + remaining


# ============================================================
# Main Tutors table
# ============================================================

def build_tutors_table(
    profiles: list[dict],
) -> pd.DataFrame:

    current_year = (
        datetime.now().year
    )

    all_subjects = get_all_subjects(
        profiles
    )

    all_badges = get_all_badges(
        profiles
    )

    rows = []

    for profile in profiles:

        qualified_year = profile.get(
            "qualified_year"
        )

        years_qualified = (
            current_year
            - qualified_year
            if qualified_year
            else None
        )

        subjects = profile.get(
            "subjects",
            [],
        )

        badges = profile.get(
            "badges",
            [],
        )

        qualifications = profile.get(
            "qualifications",
            [],
        )

        schools = profile.get(
            "schools_prepared_for",
            [],
        )

        locations = profile.get(
            "teaching_locations",
            [],
        )

        row = {
            # ----------------------------
            # Identity
            # ----------------------------
            "Tutor ID": (
                profile.get(
                    "tutor_id"
                )
            ),
            "Name": (
                profile.get(
                    "name"
                )
            ),
            "Primary Role": (
                get_primary_role(
                    profile.get(
                        "headline"
                    )
                )
            ),

            # ----------------------------
            # Cost / experience
            # ----------------------------
            "Hourly Rate (£)": (
                profile.get(
                    "hourly_rate_from"
                )
            ),
            "Qualified Year": (
                qualified_year
            ),
            "Years Qualified": (
                years_qualified
            ),

            # ----------------------------
            # Availability
            # ----------------------------
            "Availability Status": (
                classify_availability(
                    profile.get(
                        "availability_text"
                    )
                )
            ),
            "Availability Details": (
                profile.get(
                    "availability_text"
                )
            ),

            # ----------------------------
            # Teaching mode
            # ----------------------------
            "Online": yes_no(
                bool(
                    profile.get(
                        "online"
                    )
                )
            ),
            "Home Tuition": yes_no(
                bool(
                    profile.get(
                        "home"
                    )
                )
            ),
            "Enhanced DBS": yes_no(
                bool(
                    profile.get(
                        "enhanced_dbs"
                    )
                )
            ),
        }

        # ----------------------------
        # Badge flags
        # ----------------------------

        for badge in all_badges:
            row[
                f"Badge: {badge}"
            ] = yes_no(
                badge in badges
            )

        row["Badges Summary"] = (
            join_list(
                badges
            )
        )

        # ----------------------------
        # Subject flags
        # ----------------------------

        for subject in all_subjects:
            row[
                f"Subject: {subject}"
            ] = yes_no(
                subject in subjects
            )

        row["Subjects Summary"] = (
            join_list(
                subjects
            )
        )

        # ----------------------------
        # Qualifications
        # ----------------------------

        row[
            "No. Qualifications"
        ] = len(
            qualifications
        )

        row[
            "Qualifications Summary"
        ] = qualification_summary(
            qualifications
        )

        # ----------------------------
        # School experience
        # ----------------------------

        row[
            "No. Schools Prepared For"
        ] = len(
            schools
        )

        row[
            "Schools Prepared For"
        ] = join_list(
            schools
        )

        row[
            "School Entrance Experience"
        ] = profile.get(
            "school_entrance_experience"
        )

        # ----------------------------
        # Locations
        # ----------------------------

        row[
            "Teaching Locations"
        ] = join_list(
            locations
        )

        row[
            "Teaching Postcodes"
        ] = extract_postcodes(
            locations
        )

        # Useful personal-analysis flag
        row[
            "Covers SW6"
        ] = yes_no(
            "SW6"
            in extract_postcodes(
                locations
            ).split("; ")
        )

        # ----------------------------
        # Long text
        # ----------------------------

        row["Bio"] = (
            profile.get(
                "bio"
            )
        )

        row["Headline"] = (
            profile.get(
                "headline"
            )
        )

        row["Profile URL"] = (
            profile.get(
                "profile_url"
            )
        )

        rows.append(row)

    dataframe = pd.DataFrame(
        rows
    )

    dataframe = dataframe.sort_values(
        by=[
            "Hourly Rate (£)",
            "Name",
        ],
        na_position="last",
    ).reset_index(
        drop=True
    )

    return dataframe


# ============================================================
# Qualifications table
# ============================================================

def build_qualifications_table(
    profiles: list[dict],
) -> pd.DataFrame:

    rows = []

    for profile in profiles:

        for qualification in (
            profile.get(
                "qualifications",
                [],
            )
        ):

            rows.append(
                {
                    "Tutor ID": (
                        profile.get(
                            "tutor_id"
                        )
                    ),
                    "Name": (
                        profile.get(
                            "name"
                        )
                    ),
                    "Qualification": (
                        qualification.get(
                            "qualification"
                        )
                    ),
                    "Year": (
                        qualification.get(
                            "year"
                        )
                    ),
                    "Institution": (
                        qualification.get(
                            "institution"
                        )
                    ),
                    "Profile URL": (
                        profile.get(
                            "profile_url"
                        )
                    ),
                }
            )

    dataframe = pd.DataFrame(
        rows
    )

    if not dataframe.empty:
        dataframe = dataframe.sort_values(
            by=[
                "Name",
                "Year",
            ],
            na_position="last",
        )

    return dataframe


# ============================================================
# Subjects table
# ============================================================

def build_subjects_table(
    profiles: list[dict],
) -> pd.DataFrame:

    rows = []

    for profile in profiles:

        for subject in (
            profile.get(
                "subjects_and_levels",
                [],
            )
        ):

            rows.append(
                {
                    "Tutor ID": (
                        profile.get(
                            "tutor_id"
                        )
                    ),
                    "Name": (
                        profile.get(
                            "name"
                        )
                    ),
                    "Subject": (
                        subject.get(
                            "subject"
                        )
                    ),
                    "Details": (
                        subject.get(
                            "details"
                        )
                    ),
                    "Profile URL": (
                        profile.get(
                            "profile_url"
                        )
                    ),
                }
            )

    dataframe = pd.DataFrame(
        rows
    )

    if not dataframe.empty:
        dataframe = dataframe.sort_values(
            by=[
                "Subject",
                "Name",
            ]
        )

    return dataframe


# ============================================================
# Schools table
# ============================================================

def build_schools_table(
    profiles: list[dict],
) -> pd.DataFrame:

    rows = []

    for profile in profiles:

        for school in (
            profile.get(
                "schools_prepared_for",
                [],
            )
        ):

            rows.append(
                {
                    "Tutor ID": (
                        profile.get(
                            "tutor_id"
                        )
                    ),
                    "Name": (
                        profile.get(
                            "name"
                        )
                    ),
                    "School": school,
                    "Hourly Rate (£)": (
                        profile.get(
                            "hourly_rate_from"
                        )
                    ),
                    "Profile URL": (
                        profile.get(
                            "profile_url"
                        )
                    ),
                }
            )

    dataframe = pd.DataFrame(
        rows
    )

    if not dataframe.empty:
        dataframe = dataframe.sort_values(
            by=[
                "School",
                "Name",
            ]
        )

    return dataframe


# ============================================================
# Locations table
# ============================================================

def build_locations_table(
    profiles: list[dict],
) -> pd.DataFrame:

    rows = []

    for profile in profiles:

        for location in (
            profile.get(
                "teaching_locations",
                [],
            )
        ):

            rows.append(
                {
                    "Tutor ID": (
                        profile.get(
                            "tutor_id"
                        )
                    ),
                    "Name": (
                        profile.get(
                            "name"
                        )
                    ),
                    "Teaching Location": (
                        location
                    ),
                    "Postcodes": (
                        extract_postcodes(
                            [location]
                        )
                    ),
                    "Hourly Rate (£)": (
                        profile.get(
                            "hourly_rate_from"
                        )
                    ),
                    "Profile URL": (
                        profile.get(
                            "profile_url"
                        )
                    ),
                }
            )

    dataframe = pd.DataFrame(
        rows
    )

    if not dataframe.empty:
        dataframe = dataframe.sort_values(
            by=[
                "Name",
                "Teaching Location",
            ]
        )

    return dataframe


# ============================================================
# Data Notes
# ============================================================

def build_notes_table(
    profiles: list[dict],
) -> pd.DataFrame:

    rows = [
        {
            "Item": "Dataset",
            "Description": (
                "Publicly available Owl Tutors "
                "tutor profile information."
            ),
        },
        {
            "Item": "Tutor count",
            "Description": (
                f"{len(profiles)} unique tutor profiles."
            ),
        },
        {
            "Item": "Generated",
            "Description": (
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M"
                )
            ),
        },
        {
            "Item": "Hourly Rate (£)",
            "Description": (
                "Minimum advertised hourly rate "
                "shown on the tutor profile."
            ),
        },
        {
            "Item": "Years Qualified",
            "Description": (
                "Current calendar year minus "
                "Qualified Year. Blank where the "
                "source profile does not provide "
                "a qualification year."
            ),
        },
        {
            "Item": "Availability Status",
            "Description": (
                "Derived from the tutor's public "
                "availability text. Used only as "
                "a convenient filtering category."
            ),
        },
        {
            "Item": "Badge columns",
            "Description": (
                "Yes/No indicators derived from "
                "the badge list on each profile."
            ),
        },
        {
            "Item": "Subject columns",
            "Description": (
                "Yes/No indicators derived from "
                "the Subjects & Levels section."
            ),
        },
        {
            "Item": "Covers SW6",
            "Description": (
                "Yes when SW6 appears explicitly "
                "in the tutor's advertised home "
                "teaching locations."
            ),
        },
        {
            "Item": "Missing data",
            "Description": (
                "Missing source information is "
                "left blank rather than inferred."
            ),
        },
        {
            "Item": "Raw data",
            "Description": (
                "data/raw/tutor_profiles.json"
            ),
        },
        {
            "Item": "Clean data",
            "Description": (
                "data/processed/"
                "tutor_profiles_clean.json"
            ),
        },
    ]

    return pd.DataFrame(rows)


# ============================================================
# Excel formatting
# ============================================================

def format_main_sheet(
    writer,
    dataframe: pd.DataFrame,
) -> None:

    workbook = writer.book
    worksheet = writer.sheets[
        "Tutors"
    ]

    header_format = (
        workbook.add_format(
            {
                "bold": True,
                "font_color": "#FFFFFF",
                "bg_color": "#1F4E78",
                "border": 1,
                "align": "center",
                "valign": "vcenter",
            }
        )
    )

    identity_header = (
        workbook.add_format(
            {
                "bold": True,
                "font_color": "#FFFFFF",
                "bg_color": "#1F4E78",
                "border": 1,
                "align": "center",
                "valign": "vcenter",
            }
        )
    )

    badge_header = (
        workbook.add_format(
            {
                "bold": True,
                "font_color": "#FFFFFF",
                "bg_color": "#7030A0",
                "border": 1,
                "align": "center",
                "valign": "vcenter",
            }
        )
    )

    subject_header = (
        workbook.add_format(
            {
                "bold": True,
                "font_color": "#FFFFFF",
                "bg_color": "#548235",
                "border": 1,
                "align": "center",
                "valign": "vcenter",
            }
        )
    )

    detail_header = (
        workbook.add_format(
            {
                "bold": True,
                "font_color": "#FFFFFF",
                "bg_color": "#7F6000",
                "border": 1,
                "align": "center",
                "valign": "vcenter",
            }
        )
    )

    yes_format = (
        workbook.add_format(
            {
                "bg_color": "#E2F0D9",
                "font_color": "#375623",
                "align": "center",
            }
        )
    )

    no_format = (
        workbook.add_format(
            {
                "font_color": "#A6A6A6",
                "align": "center",
            }
        )
    )

    money_format = (
        workbook.add_format(
            {
                "num_format": "£0",
                "align": "center",
            }
        )
    )

    center_format = (
        workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
            }
        )
    )

    text_format = (
        workbook.add_format(
            {
                "valign": "top",
            }
        )
    )

    wrap_format = (
        workbook.add_format(
            {
                "text_wrap": True,
                "valign": "top",
            }
        )
    )

    # ------------------------------------------------
    # Headers
    # ------------------------------------------------

    for column_index, column_name in enumerate(
        dataframe.columns
    ):

        if column_name.startswith(
            "Badge:"
        ):
            fmt = badge_header

        elif column_name.startswith(
            "Subject:"
        ):
            fmt = subject_header

        elif column_name in [
            "Qualifications Summary",
            "Schools Prepared For",
            "School Entrance Experience",
            "Teaching Locations",
            "Bio",
            "Headline",
            "Profile URL",
        ]:
            fmt = detail_header

        elif column_name in [
            "Tutor ID",
            "Name",
            "Primary Role",
            "Hourly Rate (£)",
            "Qualified Year",
            "Years Qualified",
            "Availability Status",
            "Availability Details",
            "Online",
            "Home Tuition",
            "Enhanced DBS",
        ]:
            fmt = identity_header

        else:
            fmt = header_format

        worksheet.write(
            0,
            column_index,
            column_name,
            fmt,
        )

    # ------------------------------------------------
    # Freeze/filter
    # ------------------------------------------------

    worksheet.freeze_panes(
        1,
        3,
    )

    worksheet.set_row(
        0,
        32,
    )

    # ------------------------------------------------
    # Column widths
    # ------------------------------------------------

    for col_index, column in enumerate(
        dataframe.columns
    ):

        if column == "Tutor ID":
            width = 10

        elif column == "Name":
            width = 18

        elif column == "Primary Role":
            width = 25

        elif column == "Hourly Rate (£)":
            width = 16

        elif column in [
            "Qualified Year",
            "Years Qualified",
        ]:
            width = 14

        elif column == "Availability Status":
            width = 20

        elif column == "Availability Details":
            width = 45

        elif column in [
            "Online",
            "Home Tuition",
            "Enhanced DBS",
            "Covers SW6",
        ]:
            width = 14

        elif column.startswith(
            "Badge:"
        ):
            width = 15

        elif column.startswith(
            "Subject:"
        ):
            width = 17

        elif column in [
            "Badges Summary",
            "Subjects Summary",
        ]:
            width = 35

        elif column in [
            "No. Qualifications",
            "No. Schools Prepared For",
        ]:
            width = 20

        elif column == "Qualifications Summary":
            width = 55

        elif column == "Schools Prepared For":
            width = 60

        elif column == "School Entrance Experience":
            width = 38

        elif column == "Teaching Locations":
            width = 60

        elif column == "Teaching Postcodes":
            width = 32

        elif column == "Bio":
            width = 70

        elif column == "Headline":
            width = 45

        elif column == "Profile URL":
            width = 38

        else:
            width = 18

        worksheet.set_column(
            col_index,
            col_index,
            width,
            text_format,
        )

    # ------------------------------------------------
    # Special number formats
    # ------------------------------------------------

    if "Hourly Rate (£)" in dataframe.columns:
        col = dataframe.columns.get_loc(
            "Hourly Rate (£)"
        )

        worksheet.set_column(
            col,
            col,
            16,
            money_format,
        )

    for column in [
        "Qualified Year",
        "Years Qualified",
        "No. Qualifications",
        "No. Schools Prepared For",
    ]:
        if column in dataframe.columns:

            col = dataframe.columns.get_loc(
                column
            )

            worksheet.set_column(
                col,
                col,
                18,
                center_format,
            )

    # ------------------------------------------------
    # Wrap selected text columns
    # ------------------------------------------------

    for column in [
        "Availability Details",
        "Qualifications Summary",
        "Schools Prepared For",
        "Teaching Locations",
        "Teaching Postcodes",
    ]:

        if column in dataframe.columns:

            col = dataframe.columns.get_loc(
                column
            )

            worksheet.set_column(
                col,
                col,
                None,
                wrap_format,
            )

    # Keep row heights manageable
    for row_number in range(
        1,
        len(dataframe) + 1,
    ):
        worksheet.set_row(
            row_number,
            30,
        )

    # ------------------------------------------------
    # Conditional formatting
    # ------------------------------------------------

    first_data_row = 1
    last_data_row = len(
        dataframe
    )

    for col_index, column in enumerate(
        dataframe.columns
    ):

        if (
            column.startswith("Badge:")
            or column.startswith("Subject:")
            or column
            in [
                "Online",
                "Home Tuition",
                "Enhanced DBS",
                "Covers SW6",
            ]
        ):

            worksheet.conditional_format(
                first_data_row,
                col_index,
                last_data_row,
                col_index,
                {
                    "type": "text",
                    "criteria": "containing",
                    "value": "Yes",
                    "format": yes_format,
                },
            )

            worksheet.conditional_format(
                first_data_row,
                col_index,
                last_data_row,
                col_index,
                {
                    "type": "text",
                    "criteria": "containing",
                    "value": "No",
                    "format": no_format,
                },
            )

    # Rate colour scale
    rate_col = dataframe.columns.get_loc(
        "Hourly Rate (£)"
    )

    worksheet.conditional_format(
        first_data_row,
        rate_col,
        last_data_row,
        rate_col,
        {
            "type": "3_color_scale",
            "min_color": "#E2F0D9",
            "mid_color": "#FFF2CC",
            "max_color": "#F4CCCC",
        },
    )

    # ------------------------------------------------
    # Availability status colours
    # ------------------------------------------------

    availability_col = (
        dataframe.columns.get_loc(
            "Availability Status"
        )
    )

    available_format = (
        workbook.add_format(
            {
                "bg_color": "#E2F0D9",
                "font_color": "#375623",
            }
        )
    )

    limited_format = (
        workbook.add_format(
            {
                "bg_color": "#FFF2CC",
                "font_color": "#7F6000",
            }
        )
    )

    waitlist_format = (
        workbook.add_format(
            {
                "bg_color": "#F4CCCC",
                "font_color": "#9C0006",
            }
        )
    )

    worksheet.conditional_format(
        first_data_row,
        availability_col,
        last_data_row,
        availability_col,
        {
            "type": "text",
            "criteria": "containing",
            "value": "Available / unspecified",
            "format": available_format,
        },
    )

    worksheet.conditional_format(
        first_data_row,
        availability_col,
        last_data_row,
        availability_col,
        {
            "type": "text",
            "criteria": "containing",
            "value": "Limited availability",
            "format": limited_format,
        },
    )

    worksheet.conditional_format(
        first_data_row,
        availability_col,
        last_data_row,
        availability_col,
        {
            "type": "text",
            "criteria": "containing",
            "value": "Waitlist",
            "format": waitlist_format,
        },
    )

    # ------------------------------------------------
    # Turn main dataset into Excel table
    # ------------------------------------------------

    worksheet.add_table(
        0,
        0,
        len(dataframe),
        len(dataframe.columns) - 1,
        {
            "name": "TutorsTable",
            "style": (
                "Table Style Medium 2"
            ),
            "columns": [
                {
                    "header": column
                }
                for column
                in dataframe.columns
            ],
        },
    )


def format_detail_sheet(
    writer,
    sheet_name: str,
    dataframe: pd.DataFrame,
) -> None:

    workbook = writer.book
    worksheet = writer.sheets[
        sheet_name
    ]

    header_format = (
        workbook.add_format(
            {
                "bold": True,
                "font_color": "#FFFFFF",
                "bg_color": "#4472C4",
                "border": 1,
                "align": "center",
                "valign": "vcenter",
            }
        )
    )

    text_format = (
        workbook.add_format(
            {
                "valign": "top",
            }
        )
    )

    money_format = (
        workbook.add_format(
            {
                "num_format": "£0",
            }
        )
    )

    for column_index, column in enumerate(
        dataframe.columns
    ):
        worksheet.write(
            0,
            column_index,
            column,
            header_format,
        )

    worksheet.freeze_panes(
        1,
        2,
    )

    worksheet.set_row(
        0,
        26,
    )

    for col_index, column in enumerate(
        dataframe.columns
    ):

        if column == "Tutor ID":
            width = 10

        elif column == "Name":
            width = 20

        elif column in [
            "Qualification",
            "Institution",
            "Teaching Location",
        ]:
            width = 45

        elif column == "School":
            width = 40

        elif column == "Subject":
            width = 25

        elif column == "Details":
            width = 45

        elif column == "Profile URL":
            width = 38

        elif column == "Hourly Rate (£)":
            width = 16

        else:
            width = 16

        worksheet.set_column(
            col_index,
            col_index,
            width,
            text_format,
        )

    if (
        "Hourly Rate (£)"
        in dataframe.columns
    ):

        col = dataframe.columns.get_loc(
            "Hourly Rate (£)"
        )

        worksheet.set_column(
            col,
            col,
            16,
            money_format,
        )

    if not dataframe.empty:

        safe_name = (
            re.sub(
                r"[^A-Za-z0-9]",
                "",
                sheet_name,
            )
            + "Table"
        )

        worksheet.add_table(
            0,
            0,
            len(dataframe),
            len(dataframe.columns) - 1,
            {
                "name": safe_name,
                "style": (
                    "Table Style Medium 2"
                ),
                "columns": [
                    {
                        "header": column
                    }
                    for column
                    in dataframe.columns
                ],
            },
        )


def format_notes_sheet(
    writer,
    dataframe: pd.DataFrame,
) -> None:

    workbook = writer.book
    worksheet = writer.sheets[
        "Data Notes"
    ]

    title_format = (
        workbook.add_format(
            {
                "bold": True,
                "font_size": 16,
                "font_color": "#FFFFFF",
                "bg_color": "#1F4E78",
                "align": "left",
                "valign": "vcenter",
            }
        )
    )

    header_format = (
        workbook.add_format(
            {
                "bold": True,
                "font_color": "#FFFFFF",
                "bg_color": "#4472C4",
                "border": 1,
            }
        )
    )

    wrap_format = (
        workbook.add_format(
            {
                "text_wrap": True,
                "valign": "top",
            }
        )
    )

    worksheet.merge_range(
        "A1:B1",
        "Owl Tutors Dataset — Data Notes",
        title_format,
    )

    worksheet.set_row(
        0,
        30,
    )

    worksheet.write(
        1,
        0,
        "Item",
        header_format,
    )

    worksheet.write(
        1,
        1,
        "Description",
        header_format,
    )

    worksheet.set_column(
        "A:A",
        28,
    )

    worksheet.set_column(
        "B:B",
        90,
        wrap_format,
    )

    worksheet.freeze_panes(
        2,
        0,
    )


# ============================================================
# Export workbook
# ============================================================

def export_excel(
    profiles: list[dict],
) -> None:

    tutors = build_tutors_table(
        profiles
    )

    qualifications = (
        build_qualifications_table(
            profiles
        )
    )

    subjects = build_subjects_table(
        profiles
    )

    schools = build_schools_table(
        profiles
    )

    locations = build_locations_table(
        profiles
    )

    notes = build_notes_table(
        profiles
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with pd.ExcelWriter(
        OUTPUT_PATH,
        engine="xlsxwriter",
    ) as writer:

        tutors.to_excel(
            writer,
            sheet_name="Tutors",
            index=False,
        )

        qualifications.to_excel(
            writer,
            sheet_name="Qualifications",
            index=False,
        )

        subjects.to_excel(
            writer,
            sheet_name="Subjects",
            index=False,
        )

        schools.to_excel(
            writer,
            sheet_name="Schools",
            index=False,
        )

        locations.to_excel(
            writer,
            sheet_name="Locations",
            index=False,
        )

        notes.to_excel(
            writer,
            sheet_name="Data Notes",
            index=False,
            startrow=1,
        )

        format_main_sheet(
            writer,
            tutors,
        )

        format_detail_sheet(
            writer,
            "Qualifications",
            qualifications,
        )

        format_detail_sheet(
            writer,
            "Subjects",
            subjects,
        )

        format_detail_sheet(
            writer,
            "Schools",
            schools,
        )

        format_detail_sheet(
            writer,
            "Locations",
            locations,
        )

        format_notes_sheet(
            writer,
            notes,
        )


# ============================================================
# Main
# ============================================================

def main():

    print(
        f"Loading cleaned profiles from:\n"
        f"{INPUT_PATH}"
    )

    profiles = load_profiles()

    print()
    print(
        f"Loaded {len(profiles)} "
        f"tutor profiles."
    )

    print()
    print(
        "Building analysis-friendly "
        "Excel workbook..."
    )

    export_excel(
        profiles
    )

    print()
    print("=" * 60)
    print("EXCEL EXPORT COMPLETE")
    print("=" * 60)

    print(
        f"Tutors exported: "
        f"{len(profiles)}"
    )

    print()

    print(
        f"Workbook saved to:\n"
        f"{OUTPUT_PATH}"
    )

    print()
    print(
        "Sheets:"
    )

    print(
        "  - Tutors"
    )
    print(
        "  - Qualifications"
    )
    print(
        "  - Subjects"
    )
    print(
        "  - Schools"
    )
    print(
        "  - Locations"
    )
    print(
        "  - Data Notes"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()