#!/usr/bin/env python3
"""
Convert JSONL file to Parquet format.

This script reads the Data_F1000/result.jsonl file and converts it to Parquet format
for better performance and compression.
"""

import json
import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Any
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_jsonl_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Read JSONL file and return list of dictionaries.

    Args:
        file_path (str): Path to the JSONL file

    Returns:
        List[Dict[str, Any]]: List of parsed JSON objects
    """
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if line:  # Skip empty lines
                    try:
                        json_obj = json.loads(line)
                        data.append(json_obj)
                    except json.JSONDecodeError as e:
                        logger.warning(
                            f"Failed to parse JSON on line {line_num}: {e}")
                        continue

        logger.info(f"Successfully read {len(data)} records from {file_path}")
        return data

    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise


def convert_to_parquet(jsonl_file_path: str, output_file_path: str) -> None:
    """
    Convert JSONL file to Parquet format.

    Args:
        jsonl_file_path (str): Path to input JSONL file
        output_file_path (str): Path to output Parquet file
    """
    try:
        # Read JSONL data
        logger.info(f"Reading JSONL file: {jsonl_file_path}")
        data = read_jsonl_file(jsonl_file_path)

        if not data:
            logger.warning("No data found in JSONL file")
            return

        # Convert to DataFrame
        logger.info("Converting data to DataFrame")
        df = pd.DataFrame(data)

        # Display basic information about the data
        logger.info(f"DataFrame shape: {df.shape}")
        logger.info(f"Columns: {list(df.columns)}")

        # Check for any missing values
        missing_values = df.isnull().sum()
        if missing_values.any():
            logger.info("Missing values per column:")
            for col, count in missing_values.items():
                if count > 0:
                    logger.info(f"  {col}: {count}")

        # Save to Parquet
        logger.info(f"Saving DataFrame to Parquet: {output_file_path}")
        df.to_parquet(output_file_path, index=False, engine='pyarrow')

        # Get file sizes for comparison
        input_size = Path(jsonl_file_path).stat().st_size
        output_size = Path(output_file_path).stat().st_size
        compression_ratio = (1 - output_size / input_size) * 100

        logger.info(f"Conversion completed successfully!")
        logger.info(f"Input file size: {input_size / (1024*1024):.2f} MB")
        logger.info(f"Output file size: {output_size / (1024*1024):.2f} MB")
        logger.info(f"Compression ratio: {compression_ratio:.1f}%")

    except Exception as e:
        logger.error(f"Error during conversion: {e}")
        raise


def main():
    """Main function to handle command line arguments and execute conversion."""
    parser = argparse.ArgumentParser(
        description="Convert JSONL file to Parquet format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python convert_jsonl_to_parquet.py
  python convert_jsonl_to_parquet.py --input custom_input.jsonl --output custom_output.parquet
        """
    )

    parser.add_argument(
        '--input', '-i',
        default='Data_F1000/result.jsonl',
        help='Path to input JSONL file (default: Data_F1000/result.jsonl)'
    )

    parser.add_argument(
        '--output', '-o',
        default='Data_F1000/result.parquet',
        help='Path to output Parquet file (default: Data_F1000/result.parquet)'
    )

    args = parser.parse_args()

    # Validate input file exists
    if not Path(args.input).exists():
        logger.error(f"Input file does not exist: {args.input}")
        return 1

    # Create output directory if it doesn't exist
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        convert_to_parquet(args.input, args.output)
        return 0
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
