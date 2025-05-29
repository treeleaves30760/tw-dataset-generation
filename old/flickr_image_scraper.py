import os
import csv
import time
import requests
import re
from pathlib import Path
import logging
from urllib.parse import urlencode
import json
from tqdm import tqdm
import random
import flickrapi
from dotenv import load_dotenv
from urllib.request import urlretrieve

# 載入環境變數
load_dotenv()

# 配置logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("flickr_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class FlickrImageScraper:
    def __init__(self, api_key=None, api_secret=None):
        """
        初始化 Flickr 圖片爬取器
        需要 Flickr API key 和 secret
        """
        self.api_key = api_key or os.getenv(
            "FLICKR_API_KEY") or os.getenv("FLICKER_API_KEY")
        self.api_secret = api_secret or os.getenv(
            "FLICKR_API_SECRET") or os.getenv("FLICKER_API_SECRET")

        if not self.api_key or not self.api_secret:
            logger.error(
                "未提供 Flickr API 憑證！請設置 FLICKR_API_KEY 和 FLICKR_API_SECRET 環境變數")
            self.flickr = None
        else:
            try:
                self.flickr = flickrapi.FlickrAPI(
                    api_key=self.api_key,
                    secret=self.api_secret,
                    format='parsed-json'
                )
                logger.info("成功初始化 Flickr API 客戶端")
            except Exception as e:
                logger.error(f"初始化 Flickr API 失敗: {str(e)}")
                self.flickr = None

        # 圖片儲存基礎目錄
        self.base_dir = "./Flickr_image_data"
        self.ensure_directory_exists(self.base_dir)

    def sanitize_filename(self, name):
        """將字串轉換為有效的檔案名稱，移除無效字元"""
        sanitized = re.sub(r'[\\/*?:"<>|]', '_', name)
        return sanitized

    def ensure_directory_exists(self, directory):
        """確保目錄存在，不存在則創建"""
        Path(directory).mkdir(parents=True, exist_ok=True)

    def download_images_for_attraction(self, attraction_name, max_images=100):
        """
        為指定景點下載圖片，參考範例程式碼的邏輯
        """
        if not self.flickr:
            logger.error("Flickr API 未初始化，無法下載圖片")
            return False

        logger.info(f"開始處理景點: {attraction_name}")

        # 創建景點資料夾
        folder_name = self.sanitize_filename(attraction_name)
        attraction_dir = os.path.join(self.base_dir, folder_name)

        # 檢查資料夾是否已存在且有圖片
        if os.path.exists(attraction_dir):
            existing_images = len([f for f in os.listdir(attraction_dir)
                                  if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
            if existing_images >= max_images:
                logger.info(f"{attraction_name} 已有 {existing_images} 張圖片，跳過")
                return True
        else:
            self.ensure_directory_exists(attraction_dir)
            existing_images = 0

        needed_images = max_images - existing_images
        logger.info(f"{attraction_name} 需要下載 {needed_images} 張圖片")

        page = 1
        photos_downloaded = 0

        with tqdm(total=needed_images, desc=f"下載 {attraction_name} 圖片") as pbar:
            while photos_downloaded < needed_images:
                try:
                    logger.info(f"搜尋 {attraction_name} 的圖片，第 {page} 頁")

                    # 使用 Flickr API 搜尋照片，不添加額外文字
                    photos = self.flickr.photos.search(
                        text=attraction_name,
                        extras='url_c,url_m,url_o',  # 獲取不同尺寸的 URL
                        per_page=500,
                        page=page,
                        sort='relevance',
                        content_type=1,  # 只搜尋照片
                        media='photos',
                        safe_search=1   # 安全搜尋
                    )

                    if not photos['photos']['photo']:
                        logger.warning(f"沒有找到更多 {attraction_name} 的照片")
                        break

                    logger.info(f"找到 {len(photos['photos']['photo'])} 張照片")

                    for photo in photos['photos']['photo']:
                        if photos_downloaded >= needed_images:
                            break

                        try:
                            # 優先使用高解析度圖片
                            url = photo.get('url_o') or photo.get(
                                'url_c') or photo.get('url_m')

                            if url:
                                # 構建檔案名稱
                                image_index = existing_images + photos_downloaded + 1
                                filename = os.path.join(
                                    attraction_dir,
                                    f"{folder_name}_{image_index}.jpg"
                                )

                                # 下載圖片
                                urlretrieve(url, filename)
                                photos_downloaded += 1
                                pbar.update(1)

                                logger.info(f"已下載: {filename}")

                                # 添加延遲避免請求過快
                                time.sleep(random.uniform(0.3, 0.8))

                            else:
                                logger.warning(
                                    f"照片沒有可用的 URL: {photo.get('id', 'unknown')}")

                        except Exception as e:
                            logger.error(f"下載圖片時發生錯誤: {str(e)}")
                            continue

                    page += 1

                except Exception as e:
                    if "flickr" in str(e).lower():
                        logger.error(f"Flickr API 錯誤: {str(e)}")
                    else:
                        logger.error(f"未預期的錯誤: {str(e)}")
                    break

        logger.info(f"完成處理 {attraction_name}: 下載了 {photos_downloaded} 張新圖片")
        return photos_downloaded > 0

    def process_csv_file(self, csv_file_path, max_images_per_attraction=100):
        """處理 CSV 檔案中的所有景點"""
        if not os.path.exists(csv_file_path):
            logger.error(f"CSV 檔案不存在: {csv_file_path}")
            return

        if not self.flickr:
            logger.error("Flickr API 未初始化，無法處理")
            return

        attractions = []

        # 讀取 CSV 檔案
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                # 檢測是否有標題行
                first_line = file.readline().strip()
                file.seek(0)

                reader = csv.reader(file)

                # 如果第一行包含 "景點" 等關鍵字，跳過標題行
                if any(keyword in first_line.lower() for keyword in ['景點', 'attraction', '名稱', '資料名稱']):
                    next(reader)
                else:
                    file.seek(0)
                    reader = csv.reader(file)

                for row in reader:
                    if row and len(row) > 0:
                        # 嘗試從不同欄位獲取景點名稱
                        attraction_name = None
                        if len(row) >= 4:  # 如果有多個欄位，嘗試第4欄（資料名稱）
                            attraction_name = row[3].strip()
                        if not attraction_name:  # 如果第4欄沒有，使用第1欄
                            attraction_name = row[0].strip()

                        if attraction_name:
                            attractions.append(attraction_name)

        except Exception as e:
            logger.error(f"讀取 CSV 檔案失敗: {str(e)}")
            return

        logger.info(f"從 CSV 檔案讀取到 {len(attractions)} 個景點")

        # 處理每個景點
        successful_count = 0
        failed_count = 0

        for attraction in tqdm(attractions, desc="處理景點"):
            try:
                success = self.download_images_for_attraction(
                    attraction, max_images_per_attraction)
                if success:
                    successful_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                logger.error(f"處理景點 {attraction} 時發生錯誤: {str(e)}")
                failed_count += 1

            # 景點間的延遲
            time.sleep(random.uniform(1, 2))

        logger.info(f"處理完成: 成功 {successful_count} 個景點，失敗 {failed_count} 個景點")


def main():
    """主函數"""
    # 設定 CSV 檔案路徑（相對於專案根目錄）
    csv_file_path = "../景點_F1000.csv"

    # 檢查 API 憑證
    api_key = os.getenv("FLICKR_API_KEY") or os.getenv("FLICKER_API_KEY")
    api_secret = os.getenv("FLICKR_API_SECRET") or os.getenv(
        "FLICKER_API_SECRET")

    if not api_key or not api_secret:
        logger.error("未設置 Flickr API 憑證！")
        logger.error("請在 .env 檔案中設置 FLICKR_API_KEY 和 FLICKR_API_SECRET")
        logger.error("或者設置 FLICKER_API_KEY 和 FLICKER_API_SECRET （相容舊版本）")
        return

    # 初始化爬取器
    scraper = FlickrImageScraper(api_key=api_key, api_secret=api_secret)

    # 開始處理
    logger.info("開始從 Flickr 爬取景點圖片...")
    scraper.process_csv_file(csv_file_path, max_images_per_attraction=100)
    logger.info("Flickr 圖片爬取完成")


if __name__ == "__main__":
    main()
