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
        self.api_key = api_key or os.getenv("FLICKR_API_KEY")
        self.api_secret = api_secret or os.getenv("FLICKR_API_SECRET")

        if not self.api_key or not self.api_secret:
            logger.warning("未提供 Flickr API 憑證，將嘗試使用網頁爬取方式")
            self.flickr = None
        else:
            try:
                self.flickr = flickrapi.FlickrAPI(
                    self.api_key, self.api_secret, format='parsed-json')
                logger.info("成功初始化 Flickr API 客戶端")
            except Exception as e:
                logger.error(f"初始化 Flickr API 失敗: {str(e)}")
                self.flickr = None

        # 設置請求 headers (用於網頁爬取備用方案)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

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

    def search_photos_by_api(self, query, per_page=50):
        """使用 Flickr API 搜尋照片"""
        if not self.flickr:
            logger.warning("Flickr API 未初始化，無法使用 API 搜尋")
            return None

        try:
            logger.info(f"使用 Flickr API 搜尋: {query}")

            # 使用 Flickr API 搜尋照片
            photos = self.flickr.photos.search(
                text=query,
                per_page=per_page,
                page=1,
                sort='relevance',
                content_type=1,  # 只搜尋照片
                media='photos',
                safe_search=1,   # 安全搜尋
                extras='url_c,url_m,url_o'  # 獲取不同尺寸的 URL
            )

            if photos['stat'] == 'ok' and 'photo' in photos['photos']:
                logger.info(f"找到 {len(photos['photos']['photo'])} 張照片")
                return photos['photos']['photo']
            else:
                logger.warning(f"API 搜尋沒有結果: {query}")
                return []

        except Exception as e:
            logger.error(f"API 搜尋失敗 {query}: {str(e)}")
            return None

    def get_photo_info(self, photo_id):
        """獲取照片的詳細資訊"""
        if not self.flickr:
            return None

        try:
            info = self.flickr.photos.getInfo(photo_id=photo_id)
            return info
        except Exception as e:
            logger.error(f"獲取照片資訊失敗 {photo_id}: {str(e)}")
            return None

    def get_best_photo_url(self, photo):
        """從照片資料中獲取最佳品質的圖片 URL"""
        # 優先順序：原圖 > 大圖 > 中圖
        url_keys = ['url_o', 'url_c', 'url_m']

        for key in url_keys:
            if key in photo:
                return photo[key]

        # 如果沒有直接的 URL，構建標準 URL
        if all(k in photo for k in ['farm', 'server', 'id', 'secret']):
            return f"https://farm{photo['farm']}.staticflickr.com/{photo['server']}/{photo['id']}_{photo['secret']}_c.jpg"

        return None

    def search_photos_by_web(self, query, limit=20):
        """使用網頁爬取方式搜尋 Flickr 照片（備用方案）"""
        try:
            logger.info(f"使用網頁爬取方式搜尋: {query}")

            # 構建搜尋 URL
            params = {
                'text': f"{query} Taiwan",
                'sort': 'relevance'
            }
            search_url = f"https://www.flickr.com/search/?{urlencode(params)}"

            # 發送請求
            response = requests.get(
                search_url, headers=self.headers, timeout=15)
            response.raise_for_status()

            # 使用正則表達式提取圖片 URL
            image_patterns = [
                r'https://live\.staticflickr\.com/\d+/\d+_[a-f0-9]+_[a-z]\.jpg',
                r'https://farm\d+\.staticflickr\.com/\d+/\d+_[a-f0-9]+_[a-z]\.jpg'
            ]

            all_images = []
            for pattern in image_patterns:
                images = re.findall(pattern, response.text)
                all_images.extend(images)

            # 去重並限制數量
            unique_images = list(set(all_images))[:limit]

            logger.info(f"從網頁找到 {len(unique_images)} 張 {query} 的圖片")
            return unique_images

        except Exception as e:
            logger.error(f"網頁搜尋失敗 {query}: {str(e)}")
            return []

    def download_image(self, image_url, save_path):
        """下載圖片到指定路徑"""
        try:
            response = requests.get(
                image_url, headers=self.headers, stream=True, timeout=15)
            response.raise_for_status()

            # 檢查是否為有效的圖片內容
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                logger.warning(f"URL 不是有效圖片: {image_url}")
                return False

            # 檢查檔案大小（避免下載過小的圖片）
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) < 10000:  # 小於 10KB
                logger.warning(f"圖片檔案過小，跳過: {image_url}")
                return False

            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

            # 檢查下載的檔案大小
            if os.path.getsize(save_path) < 10000:
                os.remove(save_path)
                logger.warning(f"下載的圖片檔案過小，已刪除: {save_path}")
                return False

            logger.info(f"已下載圖片: {save_path}")
            return True

        except Exception as e:
            logger.error(f"下載圖片失敗 {image_url}: {str(e)}")
            if os.path.exists(save_path):
                os.remove(save_path)
            return False

    def scrape_attraction_images(self, attraction_name, max_images=10):
        """為指定景點爬取圖片"""
        logger.info(f"開始處理景點: {attraction_name}")

        # 創建景點資料夾
        folder_name = self.sanitize_filename(attraction_name)
        attraction_dir = os.path.join(self.base_dir, folder_name)
        self.ensure_directory_exists(attraction_dir)

        # 檢查現有圖片數量
        existing_images = len([f for f in os.listdir(attraction_dir)
                              if f.lower().endswith(('.jpg', '.jpeg', '.png'))])

        if existing_images >= max_images:
            logger.info(f"{attraction_name} 已有 {existing_images} 張圖片，跳過")
            return True

        needed_images = max_images - existing_images
        logger.info(f"{attraction_name} 需要下載 {needed_images} 張圖片")

        # 構建搜尋關鍵字
        search_queries = [
            f"{attraction_name} Taiwan",
            f"{attraction_name} 台灣",
            attraction_name
        ]

        photo_urls = []

        # 嘗試使用 Flickr API 搜尋
        if self.flickr:
            for query in search_queries:
                photos = self.search_photos_by_api(
                    query, per_page=max_images * 2)
                if photos:
                    for photo in photos:
                        url = self.get_best_photo_url(photo)
                        if url:
                            photo_urls.append(url)
                    break  # 如果找到結果就停止搜尋

        # 如果 API 沒有結果，使用網頁爬取
        if not photo_urls:
            for query in search_queries:
                photo_urls = self.search_photos_by_web(
                    query, limit=max_images * 2)
                if photo_urls:
                    break

        if not photo_urls:
            logger.warning(f"無法找到 {attraction_name} 的圖片")
            return False

        # 下載圖片
        downloaded_count = 0

        for i, photo_url in enumerate(photo_urls):
            if downloaded_count >= needed_images:
                break

            # 生成檔案名稱
            image_filename = f"{folder_name}_{existing_images + downloaded_count + 1}.jpg"
            image_path = os.path.join(attraction_dir, image_filename)

            # 下載圖片
            if self.download_image(photo_url, image_path):
                downloaded_count += 1
                logger.info(
                    f"{attraction_name}: 已下載 {downloaded_count}/{needed_images} 張圖片")

            # 避免請求過快
            time.sleep(random.uniform(0.5, 1.5))

        logger.info(f"完成處理 {attraction_name}: 下載了 {downloaded_count} 張新圖片")
        return downloaded_count > 0

    def process_csv_file(self, csv_file_path, max_images_per_attraction=10):
        """處理 CSV 檔案中的所有景點"""
        if not os.path.exists(csv_file_path):
            logger.error(f"CSV 檔案不存在: {csv_file_path}")
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
                success = self.scrape_attraction_images(
                    attraction, max_images_per_attraction)
                if success:
                    successful_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                logger.error(f"處理景點 {attraction} 時發生錯誤: {str(e)}")
                failed_count += 1

            # 景點間的延遲
            time.sleep(random.uniform(1, 3))

        logger.info(f"處理完成: 成功 {successful_count} 個景點，失敗 {failed_count} 個景點")


def main():
    """主函數"""
    # 設定 CSV 檔案路徑（相對於專案根目錄）
    csv_file_path = "../景點_F1000.csv"

    # 檢查 API 憑證
    api_key = os.getenv("FLICKR_API_KEY")
    api_secret = os.getenv("FLICKR_API_SECRET")

    if not api_key or not api_secret:
        logger.warning("未設置 Flickr API 憑證！")
        logger.warning("請在 .env 檔案中設置 FLICKR_API_KEY 和 FLICKR_API_SECRET")
        logger.warning("或者程式將使用網頁爬取方式（較不穩定）")

    # 初始化爬取器
    scraper = FlickrImageScraper(api_key=api_key, api_secret=api_secret)

    # 開始處理
    logger.info("開始從 Flickr 爬取景點圖片...")
    scraper.process_csv_file(csv_file_path, max_images_per_attraction=10)
    logger.info("Flickr 圖片爬取完成")


if __name__ == "__main__":
    main()
