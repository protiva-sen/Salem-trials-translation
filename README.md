# Salem Trials Translation

This repository contains a small data pipeline for collecting and processing the **Salem Witchcraft Papers (SWP)** corpus from the University of Virginia Salem archive.

It includes scripts to:
- scrape SWP index metadata,
- download raw trial HTML pages,
- split each trial into sub-SWP text files,
- generate a structured summary CSV for analysis.

## Repository structure

- `scripts/scrape_trials.py` — Scrapes SWP metadata and downloads raw trial HTML pages.
- `scripts/trials_text_extract.py` — Extracts and splits raw trial HTML content into sub-SWP `.txt` files.
- `scripts/date_process.py` — Parses extracted files, normalizes fields, and builds a final summary CSV.
- `data/raw_trials/` — Downloaded source HTML files.
- `data/final_sub_swps/` — Split plain-text sub-SWP files.
- `data/metadata/trials_index.csv` — Metadata index from scraping.
- `data/metadata/trials_summary.csv` — Final processed output dataset.

## Requirements

- Python 3.9+
- Recommended: virtual environment

Install dependencies:

```bash
pip install requests beautifulsoup4 pandas
```

## How to run

Run scripts in this order from the repository root:

### 1) Scrape metadata + download raw trial documents

```bash
python scripts/scrape_trials.py
```

This creates/updates:
- `data/metadata/trials_index.csv`
- files in `data/raw_trials/`

### 2) Extract and split sub-SWP text

```bash
python scripts/trials_text_extract.py
```

This creates/updates files in:
- `data/final_sub_swps/`

### 3) Build final summary CSV

```bash
python scripts/date_process.py
```

This creates/updates:
- `data/metadata/trials_summary.csv`

## Output schema (`trials_summary.csv`)

The final CSV contains the following columns:

- `SWP_No` — Sub-document ID (e.g., `SWP No. 5.1`).
- `Accused_or_Topic` — Name/topic matched from index metadata.
- `Date` — Normalized bracketed date extracted from text when available.
- `Legal_Proceeding` — Normalized proceeding type inferred from nearby heading text.
- `Trial_Text` — Main body text for the sub-SWP record.

## Notes

- The scraping source is: `https://salem.lib.virginia.edu/category/swp.html`.
- The scripts are designed for batch processing and write directly to the `data/` folders.
- If source HTML structure changes, you may need to adjust selectors/regex patterns in the scripts.

## License

No explicit license file is currently included in this repository.
