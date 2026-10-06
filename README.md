# Owl Tutors Scraper

A Python data collection pipeline for scraping, validating, cleaning, and structuring publicly available tutor profile information from Owl Tutors.

The project collects tutor profile URLs from the Owl Tutors search system, retrieves individual tutor profiles, extracts structured fields, validates the scraped data, and produces a cleaned JSON dataset ready for further analysis or export to Excel.

## Project Overview

The pipeline is designed to collect structured information for all publicly listed Owl Tutors tutor profiles.

At the time of development, the Owl Tutors backend search returned:

- 197 tutor records
- 196 unique tutor profiles
- 1 duplicate tutor ID in the backend search results

The final dataset therefore contains 196 unique tutor profiles.

The scraper currently extracts information such as:

- Tutor ID
- Name
- Profile URL
- Teaching headline
- Year qualified
- Hourly rate
- Online / home tuition availability
- Enhanced DBS status
- Tutor badges
- Subjects
- School entrance levels
- Qualifications
- Availability
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
│       └── validation_clean.json
│
├── src/
│   ├── __init__.py
│   ├── collect_urls.py
│   ├── scrape_profiles.py
│   ├── validate_profiles.py
│   ├── clean_profiles.py
│   └── utils.py
│
├── main.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Pipeline

The full workflow is:

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
final validation
```

### 1. Collect Tutor URLs

`collect_urls.py` queries the Owl Tutors search backend and collects all available tutor IDs.

Tutor IDs are converted into profile URLs such as:

```text
https://owltutors.co.uk/tutor/12345/
```

Duplicate tutor IDs are removed before saving.

Output:

```text
data/raw/tutor_urls.json
```

### 2. Scrape Tutor Profiles

`scrape_profiles.py` visits each tutor profile and extracts structured information.

The scraper includes:

- retry handling
- request delays
- progress reporting
- checkpoint saving
- resume support
- error logging

Profiles are saved after each successful request, meaning the scraper can resume if interrupted.

Output:

```text
data/raw/tutor_profiles.json
```

### 3. Validate Raw Data

`validate_profiles.py` performs a data quality audit.

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

Example validation summary:

```text
Total profiles: 196
Unique tutor IDs: 196
Duplicate tutor IDs: 0

Blank qualification rows: 6
Bio prefix issues: 104
Profiles with duplicate schools: 0
Profiles with duplicate locations: 0
```

### 4. Clean Tutor Profiles

`clean_profiles.py` performs conservative cleaning of the raw dataset.

Cleaning includes:

- removing blank qualification rows
- removing duplicated list entries
- cleaning whitespace
- removing accidental teaching-mode prefixes such as `Home`, `Residential`, and `Home Residential`
- preserving genuine missing values rather than inferring information

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

### 5. Validate Clean Data

The cleaned dataset is validated again.

After cleaning, the dataset contains:

```text
196 profiles
196 unique tutor IDs
0 duplicate tutor IDs
0 blank qualification rows
0 biography prefix issues
0 duplicate school lists
0 duplicate teaching locations
```

Some fields may still be missing where the original Owl Tutors profile does not provide the information. These are intentionally preserved as missing values rather than estimated.

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

Activate the virtual environment.

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

### Run the full pipeline

```bash
python main.py
```

By default, the pipeline reuses existing raw data if available and reruns the validation and cleaning stages.

### Refresh all data

To re-collect the tutor list and scrape all tutor profiles again:

```bash
python main.py --refresh
```

This runs:

```text
collect tutor URLs
→ scrape all profiles
→ validate raw data
→ clean profiles
→ validate clean data
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

## Output Data

The main cleaned dataset is:

```text
data/processed/tutor_profiles_clean.json
```

Each tutor is stored as a structured JSON object.

Example:

```json
{
  "tutor_id": "238",
  "name": "Sarah",
  "profile_url": "https://owltutors.co.uk/tutor/238/",
  "headline": "Primary education teacher • Qualified to teach in 2008 • Online",
  "qualified_year": 2008,
  "hourly_rate_from": 180.0,
  "online": true,
  "home": false,
  "enhanced_dbs": true,
  "badges": [
    "Oxbridge",
    "Russell Group",
    "Masters"
  ],
  "subjects": [
    "7 Plus",
    "8 Plus",
    "11 Plus",
    "Other School Entrance"
  ]
}
```

The full dataset contains additional fields including qualifications, school preparation experience, teaching locations, availability, and biographies.

## Data Philosophy

This project keeps raw and processed data separate.

`data/raw/` contains the scraped source data.

`data/processed/` contains cleaned and validated data.

The cleaning stage is intentionally conservative. Missing source information is not inferred or artificially filled.

## Responsible Scraping

This project is intended for personal research and data analysis.

The scraper:

- accesses publicly available tutor pages
- uses request delays
- avoids aggressive concurrent requests
- includes retry handling
- does not attempt to bypass authentication or access private data

Users should review the target website's terms, policies, and robots.txt before running or adapting the scraper.

## Technologies

- Python
- Requests
- BeautifulSoup
- lxml
- JSON
- pathlib
- argparse

## Future Improvements

Possible future extensions include:

- export to Excel
- subject-level summary tables
- tutor ranking and filtering
- school entrance experience analysis
- qualification categorisation
- location-based tutor filtering
- automated scheduled refreshes
- additional data validation rules

## Disclaimer

This repository is an independent personal research project and is not affiliated with, endorsed by, or operated by Owl Tutors.

All tutor information is collected from publicly available webpages and remains the property of its respective owners.
