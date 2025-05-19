import os
import json
import time
import requests
import glob
import re
from pathlib import Path
import logging
import googlemaps
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 配置logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("image_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Google Maps API 配置
API_KEY = os.getenv("GOOGLE_API_KEY")  # 從環境變數取得API密鑰

def sanitize_filename(name):
    """將字串轉換為有效的檔案名稱，移除無效字元"""
    sanitized = re.sub(r'[\\/*?:"<>|]', '_', name)
    return sanitized

def ensure_directory_exists(directory):
    """確保目錄存在，不存在則創建"""
    Path(directory).mkdir(parents=True, exist_ok=True)

def count_images_in_directory(directory):
    """計算目錄中的圖片檔案數量"""
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(directory, f'*{ext}')))
    
    return len(image_files)

def download_image(image_url, save_path):
    """從URL下載圖片並儲存"""
    try:
        response = requests.get(image_url, stream=True, timeout=10)
        response.raise_for_status()
        
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        
        logger.info(f"已下載圖片: {save_path}")
        return True
    except Exception as e:
        logger.error(f"下載圖片時發生錯誤 {image_url}: {str(e)}")
        return False

def get_place_photos(gmaps_client, attraction_name):
    """使用Google Maps API搜尋地點並獲取照片"""
    try:
        # 搜尋景點
        search_query = f"{attraction_name} 台灣"
        places_result = gmaps_client.places(search_query)
        
        # 檢查是否有搜尋結果
        if not places_result['results']:
            logger.warning(f"無法在Google Maps找到: {attraction_name}")
            return []
        
        # 取得第一個搜尋結果
        place_id = places_result['results'][0]['place_id']
        
        # 取得地點詳情以獲取照片參考
        place_details = gmaps_client.place(place_id, fields=['photo'])
        
        # 檢查是否有照片
        photos = []
        if 'photos' in place_details['result']:
            for photo in place_details['result']['photos'][:10]:  # 最多處理10張照片
                # 取得照片URL (最大尺寸)
                photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=1600&photoreference={photo['photo_reference']}&key={API_KEY}"
                photos.append(photo_url)
                
        return photos
    except Exception as e:
        logger.error(f"獲取 {attraction_name} 的Google Maps照片時發生錯誤: {str(e)}")
        return []

def process_attractions():
    """處理所有景點檔案並下載圖片"""
    # 檢查API密鑰
    if not API_KEY:
        logger.error("未設置Google API密鑰。請在.env檔案中設置GOOGLE_API_KEY。")
        return
    
    # 初始化Google Maps客戶端
    try:
        gmaps = googlemaps.Client(key=API_KEY)
    except Exception as e:
        logger.error(f"初始化Google Maps客戶端時發生錯誤: {str(e)}")
        return
    
    # 獲取attractions目錄中的所有JSON檔案
    json_files = glob.glob('attractions/*.json')
    logger.info(f"找到{len(json_files)}個景點檔案")
    
    # 創建圖片的基本目錄
    base_dir = "./image_data"
    ensure_directory_exists(base_dir)
    
    # 處理每個JSON檔案
    for json_file in json_files:
        try:
            # 讀取JSON資料
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取景點名稱
            attraction_name = data.get('AttractionName')
            if not attraction_name:
                logger.warning(f"{json_file}中找不到景點名稱，跳過")
                continue
            
            logger.info(f"處理景點: {attraction_name}")
            
            # 淨化景點名稱以用於資料夾名稱
            folder_name = sanitize_filename(attraction_name)
            
            # 為這個景點創建目錄
            attraction_dir = os.path.join(base_dir, folder_name)
            ensure_directory_exists(attraction_dir)
            
            # 檢查目錄中是否已有足夠的圖片
            existing_images = count_images_in_directory(attraction_dir)
            if existing_images >= 10:
                logger.info(f"{attraction_name}已有{existing_images}張圖片，跳過")
                continue
            
            # 使用Google Maps API獲取圖片
            image_urls = get_place_photos(gmaps, attraction_name)
            
            if not image_urls:
                logger.warning(f"無法為{attraction_name}找到任何照片，跳過")
                continue
                
            # 計算還需要下載的圖片數量
            images_to_download = min(10 - existing_images, len(image_urls))
            logger.info(f"{attraction_name}已有{existing_images}張圖片，將下載額外{images_to_download}張")
            
            # 下載圖片
            for i, image_url in enumerate(image_urls[:images_to_download], 1):
                # 定義檔案路徑，新圖片編號從existing_images+1開始
                image_filename = f"{folder_name}_{existing_images + i}.jpg"
                image_path = os.path.join(attraction_dir, image_filename)
                
                # 跳過已存在的圖片
                if os.path.exists(image_path):
                    logger.info(f"{attraction_name}的圖片{existing_images + i}已存在，跳過")
                    continue
                
                # 下載並儲存圖片
                success = download_image(image_url, image_path)
                if success:
                    logger.info(f"已儲存{attraction_name}的圖片 {i}/{images_to_download}")
                else:
                    logger.warning(f"無法儲存{attraction_name}的圖片 {i}/{images_to_download}")
                
                # 短暫延遲避免過快請求
                time.sleep(0.5)
            
            logger.info(f"完成處理{attraction_name}")
            
        except Exception as e:
            logger.error(f"處理檔案{json_file}時發生錯誤: {str(e)}")
            continue
        
        # 景點之間延遲以避免API限制
        time.sleep(1)

def main():
    """主函數"""
    try:
        logger.info("開始圖片擷取程序")
        process_attractions()
        logger.info("圖片擷取程序完成")
    except Exception as e:
        logger.error(f"執行期間發生錯誤: {str(e)}")

if __name__ == "__main__":
    main()
