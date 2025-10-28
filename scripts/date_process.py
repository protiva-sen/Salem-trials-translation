import os
import re
import csv
import pandas as pd

FINAL_FOLDER = "data/final_sub_swps"
INDEX_FILE = "data/metadata/trials_index.csv"
OUTPUT_CSV = "data/metadata/trials_summary.csv"

# --- Load Accused/Topic mapping safely ---
index_df = pd.read_csv(INDEX_FILE)

# Try to find SWP column automatically (now handles uppercase/lowercase)
possible_cols = ["SWP No.", "SWP_no", "SWP_No", "SWP", "swp_no"]
swp_col = next((c for c in index_df.columns if c in possible_cols), None)
if swp_col is None:
    raise KeyError(f"❌ Could not find any SWP column in metadata file. Found columns: {list(index_df.columns)}")

# Find accused/topic column
accused_col = next((c for c in index_df.columns if "Accused" in c or "Topic" in c), None)
if accused_col is None:
    raise KeyError(f"❌ Could not find accused/topic column in metadata file. Found columns: {list(index_df.columns)}")

# Build mapping — normalize SWP numbers
index_map = {}
for _, row in index_df.iterrows():
    swp_val = str(row[swp_col]).strip()
    if pd.isna(swp_val) or not swp_val:
        continue
    main_num_match = re.search(r'(\d+)', swp_val)
    if main_num_match:
        main_num = main_num_match.group(1).zfill(3)  # standardize to 3 digits (e.g., 005)
        index_map[main_num] = str(row[accused_col]).strip()

# --- Regex patterns ---
swp_pattern = re.compile(r'(SWP No\. ?\d+\.\d+)', re.IGNORECASE)

clean_legal_type = re.compile(r'[\(\)]')
prepositions = {"of", "for", "to", "from", "pertaining"}

rows = []

def normalize_legal_type(raw_line):
    if not raw_line:
        return ""
    line = clean_legal_type.sub("", raw_line).strip()
    words = [w.lower() for w in line.split() if w.lower() not in prepositions]
    if not words:
        return ""
    return words[0].capitalize()

date_pattern = re.compile(
    r"""
    \[                         # opening bracket
    \s*
    (?:\+{1,2}\s*)?            # optional leading + or ++ and space
    (January|February|March|April|May|June|July|August|September|October|November|December)
    (?:\s+\d{1,2})?            # optional day (e.g., 31)
    (?:,\s*\d{4}|\s+\d{4})     # comma+year or space+year (handles "May 31, 1692" and "February 1692")
    \s*                        # optional whitespace
    [\.\?\,]*                  # optional trailing punctuation (.,? , etc.) possibly multiple
    \s*
    \]                         # closing bracket
    """,
    re.IGNORECASE | re.VERBOSE,
)

def clean_dates_from_text(text: str, return_all: bool = False) -> str:
    """
    Extracts and normalizes dates found in bracketed forms.
    - Strips leading +/++ and trailing punctuation (., ?, spaces) while keeping the date.
    - Returns a comma-joined string of all dates found when return_all=True.
    - By default returns the first matched date.
    Examples returned: "May 31, 1692", "February 1692", "September 7, 1692"
    """
    matches = list(re.finditer(date_pattern, text))
    if not matches:
        return ""

    cleaned_dates = []
    for m in matches:
        raw = m.group(0)            # full bracketed match, e.g. "[+ May 31, 1692 ?]"
        # remove brackets, leading +/++, trailing punctuation and extra spaces
        s = raw.strip("[]").strip()
        s = re.sub(r'^\+{1,2}\s*', '', s)   # drop leading + or ++
        s = re.sub(r'[\.\?,\s]*$', '', s)   # drop trailing .,? and spaces
        s = re.sub(r'\s+', ' ', s).strip()  # collapse multiple spaces
        cleaned_dates.append(s)

    if return_all:
        # join multiple dates with comma + space
        return ", ".join(cleaned_dates)
    else:
        return cleaned_dates[0]
    
for fname in os.listdir(FINAL_FOLDER):
    if not fname.endswith(".txt"):
        continue

    with open(os.path.join(FINAL_FOLDER, fname), "r", encoding="utf-8") as f:
        content = f.read()

    lines = [line.strip() for line in content.splitlines() if line.strip()]

    # --- SWP No ---
    swp_no = ""
    idx = 0
    for i, line in enumerate(lines):
        match = swp_pattern.match(line)
        if match:
            swp_no = match.group(1)
            idx = i
            break

    if not swp_no:
        print(f"⚠️ No SWP number found in {fname}")
        continue

    # Extract main number (e.g., from SWP No. 5.1 → 005)
    main_match = re.search(r'SWP No\. ?(\d+)', swp_no, re.IGNORECASE)
    main_num = main_match.group(1).zfill(3) if main_match else None

    # --- Legal proceeding type ---
    legal_type = ""
    if idx + 1 < len(lines):
        legal_type = normalize_legal_type(lines[idx + 1])

    # --- Dates ---
    date = clean_dates_from_text(content)

    # --- Accused/topic from metadata ---
    accused = index_map.get(main_num, "")

    # --- Trial text (remove SWP No. line only) ---
    trial_text = " ".join(lines[idx + 1:]).strip()

    rows.append([swp_no, accused, date, legal_type, trial_text])

# --- Sort rows numerically by SWP number ---
def swp_sort_key(row):
    m = re.search(r'(\d+)\.(\d+)', row[0])
    if m:
        return (int(m.group(1)), int(m.group(2)))
    return (9999, 9999)

rows.sort(key=swp_sort_key)

# --- Write CSV ---
os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["SWP_No", "Accused_or_Topic", "Date", "Legal_Proceeding", "Trial_Text"])
    writer.writerows(rows)

print(f"✅ CSV file created successfully: {OUTPUT_CSV}")
