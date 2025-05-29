#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Search Image Scraper for Taiwan Tourist Attractions

This script reads the 景點_F1000.csv file, searches for images of each attraction
using Google Custom Search API, and downloads up to 100 images per attraction
to the Data_F1000/google_search_image_data directory.
"""

import os
import pandas as pd
import requests
import time
import logging
import re
from pathlib import Path
from typing import List, Dict, Optional
from tqdm import tqdm
import json
from dotenv import load_dotenv
from urllib.parse import urljoin, urlparse
from PIL import Image
import io

# Load environment variables
load_dotenv()

# Configuration
INPUT_FILE = '景點_F1000.csv'
OUTPUT_DIR = 'Data_F1000/google_search_image_data'
LOG_FILE = 'google_search_image_scraper.log'

# Google Custom Search API configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SEARCH_ENGINE_ID = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
GOOGLE_SEARCH_URL = 'https://www.googleapis.com/customsearch/v1'

# Request settings
REQUEST_DELAY = 1.0  # Delay between API calls (seconds)
MAX_RETRIES = 3
IMAGES_PER_ATTRACTION = 100
MAX_RESULTS_PER_REQUEST = 10  # Google Custom Search API limit

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


def sanitize_filename(name: str) -> str:
    """Convert string to valid filename, removing invalid characters."""
    sanitized = re.sub(r'[\\/*?:"<>|]', '_', name)
    # Remove extra spaces and limit length
    sanitized = re.sub(r'\s+', '_', sanitized.strip())
    return sanitized[:100]  # Limit filename length


def ensure_directory_exists(directory: str):
    """Ensure directory exists, create if it doesn't."""
    Path(directory).mkdir(parents=True, exist_ok=True)


def count_images_in_directory(directory: str) -> int:
    """Count the number of JPG image files in directory."""
    if not os.path.exists(directory):
        return 0

    count = 0
    for file in os.listdir(directory):
        if file.lower().endswith('.jpg'):
            count += 1

    return count


def is_valid_image_url(url: str) -> bool:
    """Check if URL points to a valid image."""
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False

        # Check file extension
        path = parsed.path.lower()
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        return any(path.endswith(ext) for ext in image_extensions)
    except:
        return False


def download_image(image_url: str, save_path: str) -> bool:
    """Download image from URL, convert to JPG format and save to file."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(
            image_url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()

        # Check if response contains image data
        content_type = response.headers.get('content-type', '').lower()
        if not content_type.startswith('image/'):
            logger.warning(f"URL does not return image content: {image_url}")
            return False

        # Load image data into memory
        image_data = response.content

        try:
            # Open image with PIL
            with Image.open(io.BytesIO(image_data)) as img:
                # Convert to RGB if necessary (for PNG with transparency, etc.)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background for transparent images
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    if img.mode in ('RGBA', 'LA'):
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                # Save as JPG with high quality
                img.save(save_path, 'JPEG', quality=95, optimize=True)

        except Exception as e:
            logger.error(f"Error converting image {image_url}: {str(e)}")
            return False

        # Check if file was created and has content
        if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
            logger.info(f"Downloaded and converted to JPG: {save_path}")
            return True
        else:
            logger.warning(f"Downloaded file is empty: {save_path}")
            if os.path.exists(save_path):
                os.remove(save_path)
            return False

    except Exception as e:
        logger.error(f"Error downloading image {image_url}: {str(e)}")
        if os.path.exists(save_path):
            try:
                os.remove(save_path)
            except:
                pass
        return False


class GoogleImageSearcher:
    """Class to handle Google Image Search using Custom Search API."""

    def __init__(self, api_key: str, search_engine_id: str):
        """Initialize with API credentials."""
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.session = requests.Session()

    def search_images(self, query: str, num_images: int = 100) -> List[str]:
        """
        Search for images using Google Custom Search API.

        Args:
            query: Search query string
            num_images: Number of images to search for

        Returns:
            List of image URLs
        """
        image_urls = []
        start_index = 1

        while len(image_urls) < num_images and start_index <= 91:  # API limit is 100 results total
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': query,
                'searchType': 'image',
                'num': min(MAX_RESULTS_PER_REQUEST, num_images - len(image_urls)),
                'start': start_index,
                'safe': 'active',
                'imgSize': 'large',  # Prefer larger images
                'imgType': 'photo',   # Prefer photos over clipart
                'cr': 'countryTW',    # Restrict to Taiwan region
                'gl': 'tw'            # Geographic location: Taiwan
            }

            try:
                response = self.session.get(
                    GOOGLE_SEARCH_URL, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()
                items = data.get('items', [])

                if not items:
                    logger.info(f"No more images found for query: {query}")
                    break

                for item in items:
                    image_url = item.get('link')
                    if image_url and is_valid_image_url(image_url):
                        image_urls.append(image_url)

                start_index += MAX_RESULTS_PER_REQUEST
                time.sleep(REQUEST_DELAY)

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed for query '{query}': {e}")
                break
            except (KeyError, ValueError, json.JSONDecodeError) as e:
                logger.error(
                    f"Error parsing response for query '{query}': {e}")
                break

        logger.info(f"Found {len(image_urls)} image URLs for query: {query}")
        return image_urls


def process_attractions():
    """Process all attractions from CSV and download images."""
    # Check API credentials
    if not GOOGLE_API_KEY or not SEARCH_ENGINE_ID:
        logger.error(
            "Missing Google API credentials. Please set GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID in .env file.")
        return

    # Load attractions data
    try:
        df = pd.read_csv(INPUT_FILE, encoding='utf-8-sig')
        logger.info(f"Loaded {len(df)} attractions from {INPUT_FILE}")
    except Exception as e:
        logger.error(f"Error loading attractions data: {e}")
        return

    # Initialize Google Image Searcher
    searcher = GoogleImageSearcher(GOOGLE_API_KEY, SEARCH_ENGINE_ID)

    # Ensure output directory exists
    ensure_directory_exists(OUTPUT_DIR)

    # Process each attraction
    success_count = 0
    error_count = 0

    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing attractions"):
        try:
            attraction_name = row['資料名稱']
            logger.info(
                f"Processing attraction {idx}/{len(df)}: {attraction_name}")

            # Create sanitized folder name
            folder_name = sanitize_filename(attraction_name)
            attraction_dir = os.path.join(OUTPUT_DIR, folder_name)
            ensure_directory_exists(attraction_dir)

            # Check if we already have enough images
            existing_images = count_images_in_directory(attraction_dir)
            if existing_images >= IMAGES_PER_ATTRACTION:
                logger.info(
                    f"Skipping {attraction_name}: already has {existing_images} images")
                continue

            # Create search query
            search_query = f"{attraction_name}"
            logger.info(f"Searching for: {search_query}")

            # Search for images
            image_urls = searcher.search_images(
                search_query, IMAGES_PER_ATTRACTION)

            if not image_urls:
                logger.warning(f"No images found for {attraction_name}")
                error_count += 1
                continue

            # Download images
            downloaded_count = 0
            for i, image_url in enumerate(image_urls):
                if existing_images + downloaded_count >= IMAGES_PER_ATTRACTION:
                    break

                # Create filename - always save as JPG
                image_filename = f"{folder_name}_{existing_images + downloaded_count + 1:03d}.jpg"
                image_path = os.path.join(attraction_dir, image_filename)

                # Skip if file already exists
                if os.path.exists(image_path):
                    downloaded_count += 1
                    continue

                # Download image
                if download_image(image_url, image_path):
                    downloaded_count += 1
                    logger.info(
                        f"Downloaded {downloaded_count}/{len(image_urls)} for {attraction_name}")

                # Add delay between downloads
                time.sleep(0.5)

            logger.info(
                f"Completed {attraction_name}: downloaded {downloaded_count} new images")
            success_count += 1

        except Exception as e:
            logger.error(
                f"Error processing attraction {attraction_name}: {str(e)}")
            error_count += 1
            continue

        # Add delay between attractions
        time.sleep(REQUEST_DELAY)

    logger.info(
        f"Processing completed. Success: {success_count}, Errors: {error_count}")


def main():
    """Main function."""
    try:
        logger.info("Starting Google Search Image Scraper")
        process_attractions()
        logger.info("Google Search Image Scraper completed")
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")


if __name__ == "__main__":
    main()
