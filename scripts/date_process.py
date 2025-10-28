import os
import re
import csv

FINAL_FOLDER = "data/final_sub_swps"  # folder with sub-SWP text files
OUTPUT_CSV = "data/trials_summary.csv"

# regex patterns
swp_pattern = re.compile(r'(SWP No\. \d+\.\d+)', re.IGNORECASE)
date_pattern = re.compile(r'\[([^\]]+)\]')  # text in brackets, e.g., [May 31, 1692]

rows = []

for fname in os.listdir(FINAL_FOLDER):
    if not fname.endswith(".txt"):
        continue

    with open(os.path.join(FINAL_FOLDER, fname), "r", encoding="utf-8") as f:
        content = f.read()

    lines = [line.strip() for line in content.splitlines() if line.strip()]

    # SWP No.
    swp_no = ""
    legal_type = ""
    idx = 0
    for i, line in enumerate(lines):
        swp_match = swp_pattern.match(line)
        if swp_match:
            swp_no = swp_match.group(1)
            idx = i
            break

    # Legal proceeding type is the next line after SWP No.
    if idx + 1 < len(lines):
        legal_type = lines[idx + 1]

    # Date (first [ ... ] in file)
    date_match = date_pattern.search(content)
    date = date_match.group(1) if date_match else ""

    # Accused / topic (heuristic: first capitalized name after SWP No. and legal type)
    accused = ""
    for line in lines[idx + 2: idx + 12]:  # look in next ~10 lines
        name_match = re.search(r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)', line)
        if name_match:
            accused = name_match.group(1)
            break

    # Full trial text
    trial_text = content.replace("\n", " ").strip()

    rows.append([swp_no, accused, date, legal_type, trial_text])

# Write to CSV
os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["SWP_No", "Accused_or_Topic", "Date", "Legal_Proceeding", "Trial_Text"])
    writer.writerows(rows)

print(f"CSV file created: {OUTPUT_CSV}")
