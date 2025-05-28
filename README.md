# TW-Dataset Generator

## 簡介

TW-Dataset Generator 是一個自動化工具，用於生成台灣旅遊景點的數據集。該工具可以自動下載景點資訊的JSON檔案，並從Google Maps和Flickr收集每個景點的圖片，建立完整的台灣旅遊景點圖像資料集。

這個專案的主要功能包括：
- 從台灣觀光多媒體開放資料平台獲取景點資訊
- 下載並整理景點JSON數據
- 使用Google Maps API獲取每個景點的照片
- 使用Flickr API獲取高品質景點圖片
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

#### 3.2 使用Flickr下載圖片（新功能）

針對前1000名熱門景點，使用Flickr API獲取高品質圖片：

1. 首先，申請Flickr API憑證：
   - 前往[Flickr API申請頁面](https://www.flickr.com/services/apps/create/apply)
   - 選擇 "Apply for a non-commercial key"
   - 獲取API Key和API Secret

2. 執行Flickr圖片下載：
   ```bash
   cd Data_F1000
   python flickr_image_scraper.py
   ```

3. 程式會：
   - 讀取`景點_F1000.csv`中的景點資料
   - 使用Flickr API搜尋相關圖片
   - 將圖片儲存到`Data_F1000/Flickr_image_data/`資料夾

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

### Flickr API憑證

若要使用Flickr圖片下載功能：

1. 前往[Flickr API申請頁面](https://www.flickr.com/services/apps/create/apply)
2. 選擇 "Apply for a non-commercial key"
3. 填寫應用程式資訊
4. 獲取API Key和API Secret
5. 在`.env`檔案中設定憑證

## 注意事項

- 程式會將所有活動記錄到命令行和名為`image_scraper.log`的檔案中
- 如果程式遇到錯誤，請查看日誌檔案了解詳情
- Google Maps API有使用限制和計費標準，請確保您了解這些限制以避免產生意外費用

## 授權條款

本專案使用的資料來源為[觀光多媒體開放資料—Open Multimedia Data in Tourism](https://media.taiwan.net.tw/zh-tw/portal)，受台灣政府開放資料授權條款約束。

使用Google Maps API時，請遵守[Google Maps Platform條款](https://cloud.google.com/maps-platform/terms/)。

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
