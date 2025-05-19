# TW-Dataset Generator

## Introduction

TW-Dataset Generator is an automated tool for creating a dataset of tourist attractions in Taiwan. This tool automatically downloads attraction information in JSON format and collects images of each attraction from Google Maps, establishing a comprehensive image database of Taiwan's tourist attractions.

The main features of this project include:
- Obtaining attraction information from Taiwan's Tourism Open Multimedia Data Platform
- Downloading and organizing attraction JSON data
- Using Google Maps API to acquire photos of each attraction
- Storing photos in a structured manner

## Installation

```bash
conda create -n tw-dataset python==3.11.10
conda activate tw-dataset
pip install -r requirements.txt
```

## Usage

The usage flow of this project consists of the following steps:

### 1. Download Attraction Data

First, download the attraction CSV file from Taiwan's Tourism Open Multimedia Data Platform:
1. Visit [Tourism and Recreation Theme :: Tourism Open Multimedia Data Platform](https://media.taiwan.net.tw/zh-tw/portal/travel)
2. Download the "景點.csv" (Attractions.csv) file and place it in the project root directory

### 2. Download Attraction JSON Data

Use the `json_downloader.py` tool to download detailed JSON data for each attraction:

```bash
python json_downloader.py
```

This step reads "景點.csv" and downloads corresponding JSON files for each attraction to the `attractions` folder.

### 3. Download Attraction Images

Use the `image_scraper.py` tool to download Google Maps images for each attraction:

1. First, ensure you have set up your Google Maps API key:
   - Create a `.env` file in the project root directory
   - Add to the file: `GOOGLE_API_KEY=your_Google_API_key`

2. Run the image download program:
   ```bash
   python image_scraper.py
   ```

3. The program will process all JSON files in the `attractions` folder, extracting attraction names
4. It uses Google Maps Places API to search for each attraction and download up to 10 photos
5. Photos are saved in the path format `./image_data/<attraction_name>/<attraction_name_number>.jpg`

## License

The data source for this project is [Tourism Open Multimedia Data—Open Multimedia Data in Tourism](https://media.taiwan.net.tw/zh-tw/portal), governed by Taiwan's government open data license terms.

When using the Google Maps API, please comply with the [Google Maps Platform Terms](https://cloud.google.com/maps-platform/terms/).

Note: Google Maps API has usage limits and billing standards. Please ensure you understand these limitations to avoid unexpected charges.

# Taiwan Attraction Image Scraper

This script downloads images for Taiwan attractions using the Google Maps API. It processes JSON files containing attraction information and downloads up to 10 images for each attraction.

## Prerequisites

- Python 3.6+
- Google Maps API Key

## Installation

1. Clone this repository or download the script
2. Install required Python packages:

```bash
pip install requests python-dotenv googlemaps
```

## Configuration

Before running the script, you need to set up your Google API credentials:

1. Get a Google API Key from the [Google Cloud Console](https://console.cloud.google.com/)
2. Activate the Places API and Maps JavaScript API
3. Create a `.env` file:
   ```bash
   cp env.example .env
   ```
4. Edit the `.env` file and add your credentials:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   ```

## Usage

1. Make sure your attraction JSON files are in the `attractions` directory
2. Run the script:

```bash
python image_scraper.py
```

The script will:
1. Process all JSON files in the `attractions` directory
2. Extract the `AttractionName` from each JSON file
3. Search for images using Google Maps Places API
4. Download up to 10 images for each attraction
5. Save images to `./image_data/<attraction_name>/<attraction_name_number>.jpg`

## Notes

- The script logs all activity to both the console and a file named `image_scraper.log`
- If the script encounters errors, check the log file for details
- The Google Maps API has usage limits and billing rates
- Make sure you understand these limitations to avoid unexpected charges

## JSON Structure

The script expects JSON files with the following structure:

```json
{
  "AttractionID": "...",
  "AttractionName": "Name of the attraction",
  ...
}
```

The `AttractionName` field is required. 