from google import genai
from dotenv import load_dotenv
import os
import pandas as pd
import json
from pathlib import Path
import glob

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 讀取CSV檔案
csv_path = "../景點_F1000.csv"
attractions_df = pd.read_csv(csv_path)

# 設定路徑
google_search_base_path = "../Data_F1000/google_search_image_data"
output_path = "../Data_F1000/result.jsonl"

# 讀取已處理的記錄，避免重複處理
processed_images = set()
if os.path.exists(output_path):
    with open(output_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                processed_images.add(record.get('image_path', ''))

# 讀取prompt模板
with open("Generate_Description.md", "r", encoding='utf-8') as f:
    prompt_template = f.read()


def process_attraction_images(attraction_name, attraction_description):
    """處理單個景點的所有圖片"""
    attraction_folder = os.path.join(google_search_base_path, attraction_name)

    if not os.path.exists(attraction_folder):
        print(f"警告：找不到景點資料夾 {attraction_folder}")
        return

    # 獲取所有jpg圖片
    image_files = glob.glob(os.path.join(attraction_folder, "*.jpg"))

    # 為了測試，每個景點最多只處理前2張圖片
    image_files = image_files[:2]

    print(f"處理景點：{attraction_name}，共 {len(image_files)} 張圖片")

    for image_path in image_files:
        # 檢查是否已經處理過
        if image_path in processed_images:
            print(f"跳過已處理的圖片：{os.path.basename(image_path)}")
            continue

        try:
            # 準備prompt
            prompt = prompt_template.replace(
                "<|attraction_name|>", attraction_name)
            prompt = prompt.replace(
                "<|attraction_description|>", attraction_description)

            # 呼叫Gemini API
            print(f"處理圖片：{os.path.basename(image_path)}")

            # 上傳圖片
            image_file = genai.upload_file(image_path, mime_type='image/jpeg')

            model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
            response = model.generate_content([image_file, prompt])

            # 準備結果記錄
            result_record = {
                "attraction_name": attraction_name,
                "attraction_description": attraction_description,
                "image_path": image_path,
                "image_filename": os.path.basename(image_path),
                "reasoning": str(response.text)
            }

            # 寫入JSONL檔案
            with open(output_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(result_record, ensure_ascii=False) + '\n')

            # 更新已處理集合
            processed_images.add(image_path)

            print(f"完成處理：{os.path.basename(image_path)}")

        except Exception as e:
            print(f"處理圖片 {os.path.basename(image_path)} 時發生錯誤：{str(e)}")
            continue


# 主要處理流程
print("開始批量處理景點圖片...")
print(f"共有 {len(attractions_df)} 個景點需要處理")

# 為了測試，只處理前3個景點
test_df = attractions_df.head(3)
print(f"測試模式：只處理前 {len(test_df)} 個景點")

for index, row in enumerate(test_df.itertuples(), 1):
    attraction_name = row.資料名稱
    attraction_description = row.文字描述

    print(f"\n處理進度：{index}/{len(test_df)}")
    process_attraction_images(attraction_name, attraction_description)

print(f"\n所有處理完成！結果已儲存到：{output_path}")
