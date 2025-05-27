#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Search Count Script for Taiwan Tourist Attractions

This script reads a CSV file of Taiwan tourist attractions, performs Google searches
for each attraction to get the search result count, and then filters to keep only
the top 1000 attractions with the highest search counts.
"""

import pandas as pd
import requests
import time
import logging
import os
from typing import List, Dict, Optional
from tqdm import tqdm
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
INPUT_FILE = '景點.csv'
OUTPUT_FILE = '景點_F1000.csv'
LOG_FILE = 'google_search_count.log'

# Google Custom Search API configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SEARCH_ENGINE_ID = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
GOOGLE_SEARCH_URL = 'https://www.googleapis.com/customsearch/v1'

# Request settings
REQUEST_DELAY = 1.0  # Delay between API calls (seconds)
MAX_RETRIES = 3
BATCH_SIZE = 100  # Save progress every N records

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GoogleSearchCounter:
    """Class to handle Google Search result counting."""

    def __init__(self, api_key: str, search_engine_id: str):
        """Initialize with API credentials."""
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.session = requests.Session()

    def get_search_count(self, query: str) -> Optional[int]:
        """
        Get the number of search results for a given query.

        Args:
            query: Search query string

        Returns:
            Number of search results, or None if failed
        """
        params = {
            'key': self.api_key,
            'cx': self.search_engine_id,
            'q': query,
            'num': 1  # We only need the count, not the actual results
        }

        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(
                    GOOGLE_SEARCH_URL, params=params, timeout=10)
                response.raise_for_status()

                data = response.json()

                # Extract total results count
                search_info = data.get('searchInformation', {})
                total_results = search_info.get('totalResults')

                if total_results is not None:
                    return int(total_results)
                else:
                    logger.warning(f"No totalResults found for query: {query}")
                    return 0

            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"Request failed for query '{query}' (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff

            except (KeyError, ValueError, json.JSONDecodeError) as e:
                logger.error(
                    f"Error parsing response for query '{query}': {e}")
                break

        return None

    def search_attractions(self, attractions_df: pd.DataFrame) -> pd.DataFrame:
        """
        Search for all attractions and get their result counts.

        Args:
            attractions_df: DataFrame containing attraction data

        Returns:
            DataFrame with added search_count column
        """
        logger.info(
            f"Starting Google search for {len(attractions_df)} attractions")

        # Add search_count column if it doesn't exist
        if 'search_count' not in attractions_df.columns:
            attractions_df['search_count'] = None

        # Create progress bar
        pbar = tqdm(total=len(attractions_df), desc="Searching attractions")

        for count, (idx, row) in enumerate(attractions_df.iterrows()):
            # Skip if already processed
            if pd.notna(row.get('search_count')):
                pbar.update(1)
                continue

            attraction_name = row['資料名稱']
            location = f"{row.get('縣市名稱', '')} {row.get('行政區(鄉鎮區)名稱', '')}"

            # Create search query
            query = f"{attraction_name} {location} 台灣 景點"

            # Get search count
            search_count = self.get_search_count(query)

            if search_count is not None:
                attractions_df.at[idx, 'search_count'] = search_count
                logger.info(f"'{attraction_name}': {search_count:,} results")
            else:
                attractions_df.at[idx, 'search_count'] = 0
                logger.warning(f"Failed to get count for '{attraction_name}'")

            # Save progress periodically
            if (count + 1) % BATCH_SIZE == 0:
                self.save_progress(attractions_df, f"progress_{count + 1}.csv")
                logger.info(f"Saved progress at {count + 1} records")

            pbar.update(1)
            time.sleep(REQUEST_DELAY)

        pbar.close()
        logger.info("Google search completed")
        return attractions_df

    def save_progress(self, df: pd.DataFrame, filename: str):
        """Save current progress to a file."""
        try:
            df.to_csv(filename, index=False, encoding='utf-8-sig')
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")


def load_attractions_data(file_path: str) -> pd.DataFrame:
    """Load attractions data from CSV file."""
    try:
        # Try different encodings
        for encoding in ['utf-8-sig', 'utf-8', 'big5', 'gbk']:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                logger.info(
                    f"Successfully loaded {len(df)} attractions from {file_path} with {encoding} encoding")
                return df
            except UnicodeDecodeError:
                continue

        # If all encodings fail, raise an error
        raise ValueError(
            f"Could not read {file_path} with any supported encoding")

    except Exception as e:
        logger.error(f"Error loading attractions data: {e}")
        raise


def filter_top_attractions(df: pd.DataFrame, top_n: int = 1000) -> pd.DataFrame:
    """
    Filter attractions to keep only the top N by search count.

    Args:
        df: DataFrame with search_count column
        top_n: Number of top attractions to keep

    Returns:
        Filtered DataFrame
    """
    # Remove rows with null or zero search counts
    valid_df = df[df['search_count'].notna() & (df['search_count'] > 0)].copy()

    # Sort by search count (descending)
    sorted_df = valid_df.sort_values('search_count', ascending=False)

    # Take top N
    top_df = sorted_df.head(top_n)

    logger.info(
        f"Filtered to top {len(top_df)} attractions from {len(df)} total")
    return top_df


def save_results(df: pd.DataFrame, output_file: str):
    """Save results to CSV file."""
    try:
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        logger.info(f"Results saved to {output_file}")

        # Print some statistics
        logger.info(f"Total attractions in output: {len(df)}")
        if 'search_count' in df.columns:
            logger.info(
                f"Search count range: {df['search_count'].min():,} - {df['search_count'].max():,}")
            logger.info(
                f"Average search count: {df['search_count'].mean():.0f}")

    except Exception as e:
        logger.error(f"Error saving results: {e}")
        raise


def check_api_credentials():
    """Check if Google API credentials are available."""
    if not GOOGLE_API_KEY:
        logger.error("GOOGLE_API_KEY not found in environment variables")
        logger.info("Please set your Google API key in a .env file:")
        logger.info("GOOGLE_API_KEY=your_api_key_here")
        return False

    if not SEARCH_ENGINE_ID:
        logger.error(
            "GOOGLE_SEARCH_ENGINE_ID not found in environment variables")
        logger.info(
            "Please set your Google Custom Search Engine ID in a .env file:")
        logger.info("GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here")
        return False

    return True


def main():
    """Main function."""
    logger.info("Starting Google Search Count script")

    # Check API credentials
    if not check_api_credentials():
        logger.error("Missing API credentials. Exiting.")
        return

    # Load attractions data
    try:
        attractions_df = load_attractions_data(INPUT_FILE)
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        return

    # Initialize Google Search Counter (credentials already checked)
    if GOOGLE_API_KEY and SEARCH_ENGINE_ID:
        search_counter = GoogleSearchCounter(GOOGLE_API_KEY, SEARCH_ENGINE_ID)
    else:
        return

    # Perform Google searches
    try:
        attractions_with_counts = search_counter.search_attractions(
            attractions_df)
    except Exception as e:
        logger.error(f"Error during Google search: {e}")
        return

    # Filter top 1000 attractions
    try:
        top_attractions = filter_top_attractions(attractions_with_counts, 1000)
    except Exception as e:
        logger.error(f"Error filtering attractions: {e}")
        return

    # Save results
    try:
        save_results(top_attractions, OUTPUT_FILE)
    except Exception as e:
        logger.error(f"Error saving results: {e}")
        return

    logger.info("Script completed successfully")


if __name__ == "__main__":
    main()
