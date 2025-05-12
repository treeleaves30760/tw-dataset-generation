import pandas as pd
import requests
import os
from pathlib import Path
import time
from tqdm import tqdm

def download_attraction_json(csv_path):
    # Create attractions directory if it doesn't exist
    attractions_dir = Path('attractions')
    attractions_dir.mkdir(exist_ok=True)
    
    # Read the CSV file
    df = pd.read_csv(csv_path)
    
    # Get the unique identifiers column
    unique_ids = df['唯一識別碼']
    
    # Base URL for the JSON files
    base_url = 'https://media.taiwan.net.tw/zh-tw/portal/travel/json/'
    
    # Download JSON for each attraction with progress bar
    for unique_id in tqdm(unique_ids, desc="Downloading JSON files"):
        # Construct the full URL
        url = f'{base_url}{unique_id}'
        
        # Create the output file path
        output_file = attractions_dir / f'{unique_id}.json'
        
        # Skip if file already exists
        if output_file.exists():
            continue
        
        try:
            # Download the JSON file
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for bad status codes
            
            # Save the JSON file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            # Add a small delay to avoid overwhelming the server
            time.sleep(0.5)
            
        except requests.exceptions.RequestException as e:
            print(f'\nError downloading {url}: {e}')
        except Exception as e:
            print(f'\nUnexpected error for {url}: {e}')

if __name__ == '__main__':
    csv_path = '景點.csv'
    download_attraction_json(csv_path)
