import os
import re
from bs4 import BeautifulSoup

RAW_FOLDER = "data/raw_trials"       # folder with HTML files
FINAL_OUTPUT_FOLDER = "data/final_sub_swps"  # folder to save all sub-SWPs

os.makedirs(FINAL_OUTPUT_FOLDER, exist_ok=True)

# regex pattern to match sub-SWP headings like "SWP No. 6.1"
pattern = re.compile(r'(SWP No\. \d+\.\d+)', re.IGNORECASE)

# Process each HTML file
for fname in os.listdir(RAW_FOLDER):
    if not fname.endswith(".html"):
        continue

    # --- Extract plain text from HTML ---
    with open(os.path.join(RAW_FOLDER, fname), "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
        doc_divs = soup.find_all("div", class_="doc")
        text_content = "\n\n".join([div.get_text(separator="\n", strip=True) for div in doc_divs])

    # --- Split text into sub-SWPs ---
    splits = pattern.split(text_content)
    sub_swps = []
    for i in range(1, len(splits), 2):
        heading = splits[i].strip()
        body = splits[i + 1].strip() if (i + 1) < len(splits) else ""
        sub_swps.append((heading, body))

    # --- Save each sub-SWP in the final output folder ---
    for heading, body in sub_swps:
        safe_heading = heading.replace(" ", "_").replace(".", "_")
        sub_fname = f"{fname.replace('.html','')}_{safe_heading}.txt"
        with open(os.path.join(FINAL_OUTPUT_FOLDER, sub_fname), "w", encoding="utf-8") as f:
            f.write(f"{heading}\n\n{body}")

    print(f"Processed {fname}: {len(sub_swps)} sub-SWP sections")

print(f"All sub-SWPs saved in '{FINAL_OUTPUT_FOLDER}'")
