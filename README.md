# Owl Tutors Scraper

A Python data pipeline for collecting, validating, cleaning, and exporting publicly available tutor profile information from Owl Tutors.

The project is designed to turn Owl Tutors profile data into a structured dataset that is easy to inspect, filter, compare, and analyse in Excel.

## Project Overview

The pipeline currently:

1. Collects tutor IDs from the Owl Tutors search backend.
2. Converts tutor IDs into profile URLs.
3. Scrapes each tutor profile.
4. Validates the raw dataset.
5. Cleans known parsing artefacts.
6. Validates the cleaned dataset.
7. Exports an analysis-friendly Excel workbook.

At the time of development, the Owl Tutors backend returned:

- 197 tutor records
- 196 unique tutor profiles
- 1 duplicated tutor ID in the backend results

The final cleaned dataset therefore contains 196 unique tutor profiles.

## Extracted Fields

The scraper collects information including:

- Tutor ID
- Name
- Profile URL
- Teaching headline
- Primary teaching role
- Year qualified
- Hourly rate
- Online tuition availability
- Home tuition availability
- Enhanced DBS status
- Tutor badges
- Subjects and school entrance levels
- Qualifications
- Availability text
- Schools prepared for
- School entrance experience
- Teaching locations
- Tutor biography

## Project Structure

```text
owl-tutors-scraper/
│
├── data/
│   ├── raw/
│   │   ├── tutor_urls.json
│   │   └── tutor_profiles.json
│   │
│   └── processed/
│       ├── tutor_profiles_clean.json
│       ├── validation_raw.json
│       ├── validation_clean.json
│       └── owl_tutors.xlsx
│
├── src/
│   ├── __init__.py
│   ├── collect_urls.py
│   ├── scrape_profiles.py
│   ├── validate_profiles.py
│   ├── clean_profiles.py
│   ├── export_excel.py
│   └── utils.py
│
├── main.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Pipeline

```text
Owl Tutors search backend
        ↓
collect_urls.py
        ↓
tutor_urls.json
        ↓
scrape_profiles.py
        ↓
tutor_profiles.json
        ↓
validate_profiles.py
        ↓
clean_profiles.py
        ↓
tutor_profiles_clean.json
        ↓
validate_profiles.py
        ↓
export_excel.py
        ↓
owl_tutors.xlsx
```

## 1. Collect Tutor URLs

`src/collect_urls.py` queries the Owl Tutors search backend.

The backend is paginated using `page` and `offset`. The collector:

- retrieves all tutor records
- identifies duplicate tutor IDs
- removes duplicates
- converts tutor IDs into profile URLs

Example profile URL:

```text
https://owltutors.co.uk/tutor/12345/
```

Output:

```text
data/raw/tutor_urls.json
```

## 2. Scrape Tutor Profiles

`src/scrape_profiles.py` visits each profile URL and extracts structured data.

The scraper includes:

- request delays
- retry handling
- progress reporting
- checkpoint saving
- resume support
- error logging

Profiles are saved after each successful request so the process can resume if interrupted.

Output:

```text
data/raw/tutor_profiles.json
```

## 3. Validate Raw Data

`src/validate_profiles.py` performs a data quality audit.

Checks include:

- duplicate tutor IDs
- missing names
- missing profile URLs
- missing headlines
- missing qualification years
- missing subjects
- invalid hourly rates
- invalid qualification years
- blank qualification rows
- duplicate school entries
- duplicate teaching locations
- biography prefix issues

The raw dataset initially contained a small number of parsing artefacts, including blank qualification rows and biography prefixes such as `Home` and `Residential`.

Output:

```text
data/processed/validation_raw.json
```

## 4. Clean Tutor Profiles

`src/clean_profiles.py` performs conservative cleaning.

Cleaning includes:

- removing blank qualification rows
- removing duplicate list entries
- normalising whitespace
- removing accidental biography prefixes such as:
  - `Home`
  - `Residential`
  - `Home Residential`
- preserving genuine missing values rather than guessing them

For example:

```text
Home Kelly qualified as a teacher...
```

becomes:

```text
Kelly qualified as a teacher...
```

Output:

```text
data/processed/tutor_profiles_clean.json
```

## 5. Validate Clean Data

The cleaned dataset is validated again.

Current clean validation result:

```text
Total profiles: 196
Unique tutor IDs: 196
Duplicate tutor IDs: 0
Invalid qualified years: 0
Invalid hourly rates: 0
Blank qualification rows: 0
Bio prefix issues: 0
Profiles with duplicate schools: 0
Profiles with duplicate locations: 0
```

Some source fields remain missing where Owl Tutors does not provide the information. These values are intentionally left blank rather than inferred.

Output:

```text
data/processed/validation_clean.json
```

## 6. Export to Excel

`src/export_excel.py` converts the cleaned JSON dataset into an analysis-friendly Excel workbook.

Output:

```text
data/processed/owl_tutors.xlsx
```

The workbook contains six sheets.

### Tutors

The main analysis sheet contains one tutor per row.

It includes:

- Tutor ID
- Name
- Primary role
- Hourly rate
- Qualified year
- Years qualified
- Availability status
- Availability details
- Online tuition
- Home tuition
- Enhanced DBS
- Tutor badge flags
- Subject flags
- Qualification summary
- School entrance experience
- Schools prepared for
- Teaching locations
- Teaching postcodes
- SW6 coverage flag
- Biography
- Profile URL

Important badges are expanded into separate Yes/No columns, including:

- Oxbridge
- Russell Group
- First
- Masters
- PhD
- Examiner

Subjects and entrance levels are also expanded into separate Yes/No columns, including:

- 7 Plus
- 8 Plus
- 11 Plus
- 13 Plus
- Other School Entrance
- University Admissions
- English
- Maths
- SEN
- Science
- Biology
- Chemistry
- Physics
- Economics
- and other subjects present in the dataset

This makes the workbook easy to filter and compare.

### Qualifications

One row per tutor qualification, including:

- Tutor ID
- Name
- Qualification
- Year
- Institution
- Profile URL

### Subjects

One row per tutor-subject combination.

### Schools

One row per tutor-school combination for schools the tutor has experience preparing pupils for.

### Locations

One row per tutor teaching location, including extracted postcode districts where available.

### Data Notes

Contains dataset definitions, generation information, field descriptions, and data-handling notes.

## Installation

Clone the repository:

```bash
git clone https://github.com/BigHeadSheep/owl-tutors-scraper.git
```

Move into the project directory:

```bash
cd owl-tutors-scraper
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it.

### Windows

```bash
.venv\Scripts\activate
```

### macOS / Linux

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Run the pipeline

```bash
python main.py
```

If raw data already exists, the pipeline reuses it and runs the validation, cleaning, and Excel export stages.

### Refresh all source data

```bash
python main.py --refresh
```

This reruns the full workflow:

```text
collect tutor URLs
→ scrape all profiles
→ validate raw data
→ clean profiles
→ validate clean data
→ export Excel
```

## Running Individual Components

Collect tutor URLs:

```bash
python src/collect_urls.py
```

Scrape tutor profiles:

```bash
python src/scrape_profiles.py
```

Validate raw profiles:

```bash
python src/validate_profiles.py --input data/raw/tutor_profiles.json --output data/processed/validation_raw.json
```

Clean profiles:

```bash
python src/clean_profiles.py
```

Validate cleaned profiles:

```bash
python src/validate_profiles.py --input data/processed/tutor_profiles_clean.json --output data/processed/validation_clean.json
```

Export Excel:

```bash
python src/export_excel.py
```

## Data Philosophy

Raw and processed data are kept separate.

```text
data/raw/
```

contains scraped source data.

```text
data/processed/
```

contains cleaned, validated, and analysis-ready outputs.

The cleaning process is intentionally conservative. Missing source information is not estimated or filled unless it can be derived directly and unambiguously.

## Responsible Scraping

This project is intended for personal research and data analysis.

The scraper:

- accesses publicly available tutor pages
- uses request delays
- avoids aggressive concurrent requests
- includes retry handling
- saves checkpoints to reduce unnecessary repeat requests
- does not attempt to bypass authentication
- does not access private or restricted data

Users should review the target website's terms, policies, and robots.txt before running or adapting the scraper.

## Technologies

- Python
- Requests
- BeautifulSoup
- lxml
- pandas
- XlsxWriter
- JSON
- pathlib
- argparse

## Possible Future Improvements

Potential extensions include:

- automated scheduled refreshes
- historical snapshots
- tutor ranking models
- school-specific experience scores
- subject-specific shortlists
- geographic filtering
- change tracking between refreshes
- automated comparison reports

## Disclaimer

This repository is an independent personal research project and is not affiliated with, endorsed by, or operated by Owl Tutors.

All tutor information is collected from publicly available webpages and remains the property of its respective owners.
