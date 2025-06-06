# TW-Dataset Generator

## 簡介

TW-Dataset Generator 是一個自動化工具，用於生成台灣旅遊景點的數據集。該工具可以自動下載景點資訊的JSON檔案，並從Google Maps和Google Search收集每個景點的圖片，建立完整的台灣旅遊景點圖像資料集。

這個專案的主要功能包括：
- 從台灣觀光多媒體開放資料平台獲取景點資訊
- 下載並整理景點JSON數據
- 使用Google Maps API獲取每個景點的照片
- 使用Google Custom Search API從Google搜尋獲取大量景點圖片
- 將照片以結構化的方式儲存
- 根據Google搜尋結果數量過濾出前1000名熱門景點（`google_search_count.py`）

## 安裝方法

```bash
conda create -n tw-dataset python==3.11.10
conda activate tw-dataset
pip install -r requirements.txt
```

## 使用方法

本專案的使用流程分為以下幾個步驟：

### 1. 下載景點資料

首先，從台灣觀光多媒體開放資料平台下載景點CSV檔案：
1. 前往[觀光遊憩主題 :: 觀光多媒體開放資料平台](https://media.taiwan.net.tw/zh-tw/portal/travel)
2. 下載「景點.csv」檔案並放置在專案根目錄

### 2. 下載景點JSON資料

使用`json_downloader.py`工具下載景點的詳細JSON資料：

```bash
python json_downloader.py
```

這個步驟會讀取「景點.csv」，並為每個景點下載對應的JSON檔案到`attractions`資料夾。

### 3. 下載景點圖片

#### 3.1 使用Google Maps下載圖片

使用`image_scraper.py`工具為每個景點下載Google Maps圖片：

1. 首先，確保您已經設定Google Maps API金鑰：
   - 在專案根目錄建立`.env`檔案
   - 在檔案中添加：`GOOGLE_API_KEY=您的Google_API金鑰`

2. 執行下載圖片程式：
   ```bash
   python image_scraper.py
   ```

3. 程式會處理`attractions`資料夾中的所有JSON檔案，從中提取景點名稱
4. 使用Google Maps Places API搜尋每個景點並下載最多10張照片
5. 照片會儲存在`./image_data/<景點名稱>/<景點名稱_編號>.jpg`格式的路徑中

#### 3.2 使用Google Search下載圖片（新功能）

針對前1000名熱門景點，使用Google Custom Search API獲取大量景點圖片：

1. 首先，設定Google Custom Search API：
   - 在專案根目錄的`.env`檔案中添加：
     ```
     GOOGLE_API_KEY=您的Google_API金鑰
     GOOGLE_SEARCH_ENGINE_ID=您的自訂搜尋引擎ID
     ```
   - 關於如何設定Google Custom Search Engine，請參考下方的「API金鑰設定」部分

2. 執行Google Search圖片下載：
   ```bash
   python google_search_image_scraper.py
   ```

3. 程式會：
   - 讀取`景點_F1000.csv`中的景點資料
   - 使用Google Custom Search API搜尋每個景點的圖片
   - 下載每個景點最多100張高品質圖片，自動轉換為JPG格式
   - 將圖片儲存到`Data_F1000/google_search_image_data/<景點名稱>/`資料夾
   - 搜尋限制：僅搜尋照片類型圖片且限制在台灣地區
   - 自動跳過已有足夠圖片的景點，避免重複下載

#### 3.3 圖片格式統一轉換

將所有下載的圖片統一轉換為JPG格式：

```bash
python convert_images_to_jpg.py
```

此工具會：
- 自動掃描`Data_F1000/google_search_image_data/`目錄中的所有圖片
- 將PNG、WEBP、JPEG等格式轉換為高品質JPG格式
- 保持原有的檔名結構和編號
- 自動處理透明背景圖片（轉換為白色背景）
- 轉換完成後刪除原始檔案，節省儲存空間

### 4. 過濾景點（依Google搜尋結果數量前1000名）

本專案提供腳本可根據Google搜尋結果數量，過濾出前1000名熱門景點：

1. 準備好「景點.csv」檔案，放在專案根目錄。
2. 執行以下指令：
   ```bash
   python google_search_count.py
   ```
3. 程式會直接讀取 `景點.csv`，查詢每個景點的 Google 搜尋結果數量，並將搜尋結果數量最多的前1000個景點寫入 `景點_F1000.csv`。
4. 輸出檔案格式：
   - `景點_F1000.csv`，欄位為「景點名稱,搜尋結果數量」

> 程式會自動以多組 User-Agent 進行爬蟲，降低被 Google 反爬蟲偵測的機率。

### 依賴與驅動

- 若要使用 Selenium，請安裝 [ChromeDriver](https://sites.google.com/chromium.org/driver/) 並確保其與本機 Chrome 瀏覽器版本相符，且已加入 PATH。
- requirements.txt 已新增 selenium 套件。

## 系統需求

- Python 3.6+
- Google Maps API金鑰（僅Google Maps圖片下載功能需要）
- Flickr API憑證（僅Flickr圖片下載功能需要）
- Google Custom Search API憑證（僅Google Search圖片下載功能需要）

## 安裝套件

本專案需要安裝以下Python套件：

```bash
pip install -r requirements.txt
```

## API金鑰設定

### Google Maps API金鑰

若要使用Google Maps圖片下載功能，您需要先獲取Google Maps API金鑰：

1. 前往[Google Cloud Console](https://console.cloud.google.com/)
2. 登入您的Google帳戶並創建一個新專案
3. 在左側選單中選擇「API和服務」>「程式庫」
4. 搜尋並啟用以下API：
   - Places API
   - Maps JavaScript API
5. 在「API和服務」>「憑證」頁面中創建API金鑰
6. 將API金鑰複製到專案的`.env`檔案中

### Google Custom Search API設定

若要使用Google Search圖片下載功能：

1. **啟用API**：
   - 前往[Google Cloud Console](https://console.cloud.google.com/)
   - 在「API和服務」>「程式庫」中搜尋並啟用「Custom Search API」

2. **創建自訂搜尋引擎**：
   - 前往[Google Custom Search Engine](https://cse.google.com/cse/)
   - 點選「新增」創建新的搜尋引擎
   - 在「要搜尋的網站」中輸入 `*`（搜尋整個網路）
   - 建立後，在控制台中點選您的搜尋引擎
   - 在「設定」>「基本」中，啟用「圖片搜尋」
   - 記下「搜尋引擎ID」

3. **設定環境變數**：
   ```
   GOOGLE_API_KEY=您的Google_API金鑰
   GOOGLE_SEARCH_ENGINE_ID=您的自訂搜尋引擎ID
   ```


## 注意事項

- 程式會將所有活動記錄到命令行和相應的日誌檔案中
- 如果程式遇到錯誤，請查看日誌檔案了解詳情
- Google APIs有使用限制和計費標準，請確保您了解這些限制以避免產生意外費用
- Google Custom Search API每日有免費額度限制，超過後會產生費用
- 請遵守各API服務的使用條款和速率限制

## 授權條款

本專案使用的資料來源為[觀光多媒體開放資料—Open Multimedia Data in Tourism](https://media.taiwan.net.tw/zh-tw/portal)，受台灣政府開放資料授權條款約束。

使用Google Maps API時，請遵守[Google Maps Platform條款](https://cloud.google.com/maps-platform/terms/)。

### 5. 生成景點圖片推理描述（新功能）

針對已下載的景點圖片，使用Google Gemini AI生成詳細的推理描述：

1. **設定Gemini API**：
   - 在專案根目錄的`.env`檔案中添加：
     ```
     GEMINI_API_KEY=您的Gemini_API金鑰
     GEMINI_API_KEY_2=您的第二個Gemini_API金鑰（可選，用於提高處理速度和避免速率限制）
     ```
   - 如果只有一個API key，程式會自動使用單key模式
   - 建議設定兩個API key以提高處理效能和避免HTTP 429錯誤

2. **準備推理模板**：
   - 確保`reasoning/Generate_Description.md`檔案存在且包含適當的prompt模板

3. **執行推理生成**：
   ```bash
   cd reasoning
   python attraction_generation.py
   ```

4. **程式功能與多執行緒處理**：
   - **高效能並行處理**：使用10個線程同時處理圖片，大幅提升處理速度
   - **智能API key輪換**：自動在多個API key之間輪換，避免單一key的速率限制
   - **線程安全機制**：確保多線程環境下的文件寫入和狀態管理安全
   - 讀取`景點_F1000.csv`中的景點資料（名稱和描述）
   - 處理`Data_F1000/google_search_image_data/`目錄中的圖片
   - 為每張圖片生成包含以下內容的JSON格式推理：
     - 詳細的圖片描述分析
     - 多個關於圖片內容的問答
     - 圖片與景點資訊的符合度評估
   - **重複檢測與續傳**：自動跳過已處理的圖片，支援中斷後繼續處理
   - **即時進度顯示**：使用進度條顯示處理狀態和剩餘時間
   - 將結果以JSONL格式儲存到`Data_F1000/result.jsonl`

5. **效能提升**：
   - **10倍速度提升**：相比單線程處理，多線程版本可提升約10倍處理速度
   - **錯誤恢復機制**：遇到HTTP 429或quota錯誤時自動延遲重試
   - **記憶體優化**：採用任務池模式，避免大量圖片同時載入記憶體

6. **輸出格式**：
   每行包含一個JSON物件，包含以下欄位：
   - `attraction_name`: 景點名稱
   - `attraction_description`: 景點描述
   - `image_path`: 圖片路徑
   - `image_filename`: 圖片檔名
   - `reasoning`: Gemini AI生成的詳細推理內容

> **注意**：
> - Gemini API有使用限制和計費標準，建議先小批量測試
> - 目前程式設定為測試模式，僅處理前200個景點
> - 多執行緒處理會增加API使用量，請注意quota限制
> - 建議使用兩個不同的API key以獲得最佳性能

## JSON格式

程式預期的JSON檔案結構如下：

```json
{
  "AttractionID": "...",
  "AttractionName": "景點名稱",
  ...
}
```

其中`AttractionName`欄位是必需的。

# Taiwan Tourist Attractions Google Search Count

本工具會讀取台灣景點的 CSV 檔案，對每個景點進行 Google 搜尋，取得搜尋結果數量，並篩選出搜尋數量最多的前 1000 筆。

## 主要功能
- 讀取景點資料（CSV）
- 以爬蟲方式查詢 Google 搜尋結果數量（不再使用 Google API，並加強反爬蟲機制：隨機延遲、多 User-Agent、偵測驗證碼自動重試等）
- 支援自動儲存進度
- 篩選搜尋數量最多的前 1000 筆

## 安裝需求
- Python 3.7+
- pandas
- requests
- beautifulsoup4
- tqdm
- python-dotenv

安裝套件：

```bash
pip install -r requirements.txt
```

## 使用說明
1. 準備好景點資料檔案 `景點.csv`，放在專案目錄下。
2. 執行主程式：

```bash
python google_search_count.py
```

3. 結果會輸出到 `景點_F1000.csv`。

## 注意事項
- 本程式改為直接爬取 Google 搜尋頁面，**不再需要 Google API Key**。
- 每次請求會自動隨機切換多個 User-Agent，並隨機延遲，遇到 Google 驗證碼或 429/503 等錯誤會自動重試，以降低被 Google 反爬蟲偵測的機率。
- Google 可能會因為頻繁請求而出現驗證碼或封鎖，請斟酌使用。
- 若遇到搜尋失敗，會自動重試，並將失敗的搜尋數量設為 0。

## 參數設定
可在 `google_search_count.py` 內調整：
- `INPUT_FILE`：輸入檔名
- `OUTPUT_FILE`：輸出檔名
- `REQUEST_DELAY`：每次請求間隔秒數
- `BATCH_SIZE`：每 N 筆自動儲存進度
