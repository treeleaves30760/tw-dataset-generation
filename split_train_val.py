#!/usr/bin/env python3
"""
Script to split image data into train and validation sets.
Splits the first 90% of images for each attraction into train set,
and the remaining 10% into validation set.
"""

import os
import shutil
import sys
from pathlib import Path
import math


def split_train_val(source_dir, train_dir, val_dir, train_ratio=0.9):
    """
    Split images from source directory into train and validation directories.

    Args:
        source_dir (str): Path to source directory containing attraction folders
        train_dir (str): Path to output train directory
        val_dir (str): Path to output validation directory
        train_ratio (float): Ratio of images to use for training (default: 0.9)
    """
    source_path = Path(source_dir)
    train_path = Path(train_dir)
    val_path = Path(val_dir)

    # Create output directories if they don't exist
    train_path.mkdir(parents=True, exist_ok=True)
    val_path.mkdir(parents=True, exist_ok=True)

    if not source_path.exists():
        print(f"Error: Source directory '{source_dir}' does not exist!")
        return False

    print(f"Source directory: {source_path}")
    print(f"Train directory: {train_path}")
    print(f"Validation directory: {val_path}")
    print(f"Train ratio: {train_ratio:.1%}")
    print("-" * 50)

    total_attractions = 0
    total_train_images = 0
    total_val_images = 0

    # Process each attraction directory
    for attraction_dir in source_path.iterdir():
        if not attraction_dir.is_dir():
            continue

        attraction_name = attraction_dir.name
        print(f"Processing: {attraction_name}")

        # Get all image files in the attraction directory
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.gif']:
            image_files.extend(attraction_dir.glob(ext))
            image_files.extend(attraction_dir.glob(ext.upper()))

        # Sort files to ensure consistent ordering
        image_files.sort()

        if not image_files:
            print(f"  No image files found in {attraction_name}")
            continue

        # Calculate split point
        total_images = len(image_files)
        train_count = math.floor(total_images * train_ratio)
        val_count = total_images - train_count

        print(
            f"  Total images: {total_images}, Train: {train_count}, Val: {val_count}")

        # Create attraction directories in train and val folders
        train_attraction_dir = train_path / attraction_name
        val_attraction_dir = val_path / attraction_name

        train_attraction_dir.mkdir(parents=True, exist_ok=True)
        if val_count > 0:
            val_attraction_dir.mkdir(parents=True, exist_ok=True)

        # Copy train images (first 90%)
        for i in range(train_count):
            src_file = image_files[i]
            dst_file = train_attraction_dir / src_file.name
            shutil.copy2(src_file, dst_file)

        # Copy validation images (remaining 10%)
        for i in range(train_count, total_images):
            src_file = image_files[i]
            dst_file = val_attraction_dir / src_file.name
            shutil.copy2(src_file, dst_file)

        total_attractions += 1
        total_train_images += train_count
        total_val_images += val_count

    print("-" * 50)
    print(f"Summary:")
    print(f"  Processed {total_attractions} attractions")
    print(f"  Train images: {total_train_images}")
    print(f"  Validation images: {total_val_images}")
    print(f"  Total images: {total_train_images + total_val_images}")
    print(
        f"  Actual train ratio: {total_train_images/(total_train_images + total_val_images):.1%}")

    return True


def main():
    # Define paths
    source_dir = "Data_F1000/google_search_image_data"
    train_dir = "Data_F1000/google_search_image_data_train"
    val_dir = "Data_F1000/google_search_image_data_val"

    print("Image Data Splitting Script")
    print("=" * 50)

    # Check if source directory exists
    if not os.path.exists(source_dir):
        print(f"Error: Source directory '{source_dir}' not found!")
        sys.exit(1)

    # Ask for confirmation before proceeding
    print(f"This will split images from '{source_dir}' into:")
    print(f"  - Train (90%): '{train_dir}'")
    print(f"  - Validation (10%): '{val_dir}'")
    print()

    response = input("Do you want to continue? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("Operation cancelled.")
        sys.exit(0)

    # Perform the split
    success = split_train_val(source_dir, train_dir, val_dir)

    if success:
        print("\nSplit completed successfully!")
    else:
        print("\nSplit failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
