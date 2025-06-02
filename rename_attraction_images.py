#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
景點圖片重新命名程式

此程式會迭代景點_F1000.csv中的景點，
在Data_F1000/google_search_image_data中找對應的資料夾，
如果找不到會嘗試將空白替換為下底線，
找到後會將資料夾中的所有圖片重新命名為景點名稱。
"""

import os
import csv
import shutil
import logging
from pathlib import Path

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rename_attraction_images.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


def main():
    """主程式"""
    # 檔案路徑設定
    csv_file = '景點_F1000.csv'
    data_dir = Path('Data_F1000/google_search_image_data_val')

    if not os.path.exists(csv_file):
        logging.error(f"找不到檔案: {csv_file}")
        return

    if not data_dir.exists():
        logging.error(f"找不到目錄: {data_dir}")
        return

    # 讀取CSV檔案
    attractions = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                attraction_name = row.get('資料名稱', '').strip()
                if attraction_name:
                    attractions.append(attraction_name)

        logging.info(f"從CSV讀取到 {len(attractions)} 個景點")
    except Exception as e:
        logging.error(f"讀取CSV檔案時發生錯誤: {e}")
        return

    # 統計變數
    found_count = 0
    renamed_count = 0
    not_found_count = 0

    # 處理每個景點
    for attraction_name in attractions:
        logging.info(f"處理景點: {attraction_name}")

        # 先嘗試原始名稱
        folder_path = data_dir / attraction_name
        folder_found = False

        if folder_path.exists() and folder_path.is_dir():
            folder_found = True
            logging.info(f"找到資料夾: {folder_path}")
        else:
            # 嘗試將空白替換為下底線
            modified_name = attraction_name.replace(' ', '_')
            folder_path = data_dir / modified_name

            if folder_path.exists() and folder_path.is_dir():
                folder_found = True
                logging.info(f"找到資料夾 (替換空白後): {folder_path}")

        if folder_found:
            found_count += 1
            # 重新命名資料夾中的圖片
            images_renamed = rename_images_in_folder(
                folder_path, attraction_name)
            if images_renamed > 0:
                renamed_count += images_renamed
                logging.info(f"成功重新命名 {images_renamed} 張圖片")
        else:
            not_found_count += 1
            logging.warning(f"找不到對應的資料夾: {attraction_name}")

    # 輸出統計結果
    logging.info("=" * 50)
    logging.info("處理完成統計:")
    logging.info(f"總景點數: {len(attractions)}")
    logging.info(f"找到資料夾: {found_count}")
    logging.info(f"找不到資料夾: {not_found_count}")
    logging.info(f"重新命名圖片總數: {renamed_count}")
    logging.info("=" * 50)


def rename_images_in_folder(folder_path, attraction_name):
    """
    重新命名資料夾中的所有圖片

    Args:
        folder_path (Path): 資料夾路徑
        attraction_name (str): 景點名稱

    Returns:
        int: 重新命名的圖片數量
    """
    # 支援的圖片副檔名
    image_extensions = {'.jpg', '.jpeg', '.png',
                        '.gif', '.bmp', '.webp', '.tiff', '.tif'}

    # 取得所有圖片檔案
    image_files = []
    for file_path in folder_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            image_files.append(file_path)

    if not image_files:
        logging.warning(f"資料夾 {folder_path} 中沒有找到圖片檔案")
        return 0

    # 排序檔案以確保一致的命名順序
    image_files.sort()

    renamed_count = 0
    for index, old_file_path in enumerate(image_files, 1):
        try:
            # 產生新的檔案名稱
            file_extension = old_file_path.suffix
            new_filename = f"{attraction_name}_{index:03d}{file_extension}"
            new_file_path = old_file_path.parent / new_filename

            # 如果新檔名已存在，跳過
            if new_file_path.exists() and new_file_path != old_file_path:
                logging.warning(f"檔案 {new_filename} 已存在，跳過重新命名")
                continue

            # 重新命名檔案
            if old_file_path != new_file_path:
                shutil.move(str(old_file_path), str(new_file_path))
                renamed_count += 1
                logging.debug(f"重新命名: {old_file_path.name} -> {new_filename}")

        except Exception as e:
            logging.error(f"重新命名檔案 {old_file_path} 時發生錯誤: {e}")

    return renamed_count


if __name__ == "__main__":
    main()
