import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import os

# --- Directory and File Constants ---
OUTPUT_DIR = "data/raw_trials"
META_FILE = "data/metadata/trials_index.csv"
BASE_URL = "https://salem.lib.virginia.edu"
URL_TO_SCRAPE = "https://salem.lib.virginia.edu/category/swp.html"
# ------------------------------------

def extract_swp_metadata(url):
    """
    Scrapes the URL to extract SWP metadata using a highly generalized method 
    by targeting a nearby, unique heading text.
    """
    print(f"Starting metadata extraction from: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status() 
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # 1. Find the unique header text near the list to anchor our search
    # This text is "Salem Witchcraft Papers" or a similar heading.
    header = soup.find(lambda tag: tag.name in ['h1', 'h2', 'h3', 'strong'] and 'Salem Witchcraft Papers' in tag.get_text())

    if not header:
        print("Error: Could not find the anchor text 'Salem Witchcraft Papers' on the page.")
        return None

    # 2. Use .find_next('ul') to locate the unordered list immediately following the header
    list_container = header.find_next('ul')

    if not list_container:
        print("Error: Found the header, but could not find the immediate following <ul> list.")
        return None
        
    # 3. Find all list items (<li>) within that list
    swp_entries = list_container.find_all('li')
    
    if not swp_entries:
        print("Found the list container, but no list items (<li>) inside it.")
        return None
        
    trial_data = []

    # 4. Iterate through entries and extract data
    for entry in swp_entries:
        link_tag = entry.find('a')
        
        if link_tag:
            full_text = link_tag.get_text(strip=True)
            relative_path = link_tag.get('href')
            absolute_url = BASE_URL + relative_path
            
            # Regex to separate SWP No. from the rest (handles 006, 044a, etc.)
            match = re.match(r"(SWP No\. \d+[a-z]?):\s*(.*)", full_text)
            
            if match:
                swp_no = match.group(1).replace('SWP No. ', '').strip() 
                accused_name = match.group(2).strip()
            else:
                swp_no = full_text.split(':')[0].replace('SWP No. ', '').strip() if 'SWP No.' in full_text else full_text
                accused_name = full_text
            
            entry_description = entry.get_text(strip=True).replace(full_text, '').strip()

            fate = ""
            if any(term in entry_description for term in ["Executed", "Died", "Pressed"]):
                fate = entry_description
                
            trial_data.append({
                "SWP_No": swp_no,
                "Accused_Name_or_Topic": accused_name,
                "Fate": fate,
                "Trial_Document_URL": absolute_url
            })
            
    return trial_data

# The rest of your script (download_trial_documents and Main Execution) 
# remains the same and should now run correctly with this updated function.

def download_trial_documents(metadata_list, output_dir):
    """
    Downloads the content of each trial document URL and saves it as an HTML file.
    """
    os.makedirs(output_dir, exist_ok=True)
    print(f"\nStarting document download to: {output_dir}")
    
    download_count = 0
    for record in metadata_list:
        swp_no = record['SWP_No']
        url = record['Trial_Document_URL']
        filename = f"{swp_no.replace(' ', '_').replace(':', '')}.html"
        filepath = os.path.join(output_dir, filename)
        
        try:
            doc_response = requests.get(url)
            doc_response.raise_for_status()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(doc_response.text)
                
            download_count += 1
            print(f"  -> Downloaded {swp_no} to {filepath}")
            
        except requests.exceptions.RequestException as e:
            print(f"  -> ERROR downloading {swp_no} from {url}: {e}")
            
    print(f"\nSuccessfully downloaded {download_count} trial documents.")


# --- Main Execution ---

# 1. Ensure directories exist
os.makedirs(os.path.dirname(META_FILE), exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 2. Extract Metadata
all_trials_metadata = extract_swp_metadata(URL_TO_SCRAPE)

if all_trials_metadata:
    # 3. Save Metadata to CSV
    df = pd.DataFrame(all_trials_metadata)
    df.to_csv(META_FILE, index=False)
    print(f"\n✅ Metadata saved to: **{META_FILE}** ({len(df)} records)")

    # 4. Download Raw Trial Documents
    download_trial_documents(all_trials_metadata, OUTPUT_DIR)

    print("\nExtraction and saving process complete!")