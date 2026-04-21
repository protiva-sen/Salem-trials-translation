# Salem Trials Translation

A Python-based ETL pipeline for collecting and structuring the **Salem Witchcraft Papers (SWP)** corpus from the University of Virginia Salem archive.

## What this project does

The pipeline converts web-published SWP records into analysis-ready tabular data:

1. Scrape SWP index metadata.
2. Download source trial HTML pages.
3. Extract plain text and split into sub-SWP records.
4. Build a normalized summary CSV with identifiers, accused/topic, dates, legal proceeding type, and text.

## Data source

- Source website: `https://salem.lib.virginia.edu/category/swp.html`
- Base domain used by scraper: `https://salem.lib.virginia.edu`

## Repository layout

```text
scripts/
  scrape_trials.py        # metadata scrape + raw HTML download
  trials_text_extract.py  # extract/split into sub-SWP text files
  date_process.py         # normalize fields + build summary CSV

data/
  raw_trials/             # downloaded trial HTML pages
  final_sub_swps/         # split plain-text records per sub-SWP
  metadata/
    trials_index.csv      # scraped SWP index metadata
    trials_summary.csv    # final analysis-ready output
```

## Requirements

- Python 3.9+
- Internet connection (for `scrape_trials.py`)

Install dependencies:

```bash
pip install requests beautifulsoup4 pandas
```

## Quickstart

From the repository root, run:

```bash
python scripts/scrape_trials.py
python scripts/trials_text_extract.py
python scripts/date_process.py
```

## Step-by-step pipeline

### 1) Scrape metadata and download raw trial documents

```bash
python scripts/scrape_trials.py
```

Writes:
- `data/metadata/trials_index.csv`
- `data/raw_trials/*.html`

### 2) Extract/split trial text into sub-SWP records

```bash
python scripts/trials_text_extract.py
```

Writes:
- `data/final_sub_swps/*.txt`

### 3) Build summary dataset

```bash
python scripts/date_process.py
```

Writes:
- `data/metadata/trials_summary.csv`

## Output schema

`data/metadata/trials_summary.csv` columns:

- `SWP_No` — Sub-document ID (example: `SWP No. 5.1`).
- `Accused_or_Topic` — Matched from index metadata by normalized SWP number.
- `Date` — Extracted/cleaned bracketed date text.
- `Legal_Proceeding` — Normalized proceeding type inferred from heading context.
- `Trial_Text` — Main text content for the sub-SWP entry.

## Re-running safely

- Scripts overwrite/update files in `data/`.
- If you want a clean rebuild, remove generated outputs first:

```bash
rm -f data/metadata/trials_index.csv data/metadata/trials_summary.csv
rm -f data/raw_trials/*.html
rm -f data/final_sub_swps/*.txt
```

Then run the 3 pipeline scripts again.

## Troubleshooting

- **No metadata scraped / empty index**: upstream page structure may have changed; check parser logic in `scripts/scrape_trials.py`.
- **No sub-SWP splits**: verify expected `SWP No. X.Y` patterns still exist in extracted text (`scripts/trials_text_extract.py`).
- **Missing date/legal fields**: data is pattern-based and may be blank when source text does not match expected formats (`scripts/date_process.py`).

## Scope note

This repository currently focuses on extraction and structuring of the historical corpus. It does **not** include a packaged translation model or API service.
