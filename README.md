# TW-Dataset Generator

## 簡介

TW-Dataset Generator 是一個自動化工具，用於生成台灣旅遊景點的數據集。該工具可以自動下載景點資訊的JSON檔案，並從Google Maps收集每個景點的圖片，建立完整的台灣旅遊景點圖像資料集。

這個專案的主要功能包括：
- 從台灣觀光多媒體開放資料平台獲取景點資訊
- 下載並整理景點JSON數據
- 使用Google Maps API獲取每個景點的照片
- 將照片以結構化的方式儲存

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

## 系統需求

- Python 3.6+
- Google Maps API金鑰

## 安裝套件

本專案需要安裝以下Python套件：

```bash
pip install requests python-dotenv googlemaps pandas tqdm
```

## 獲取Google Maps API金鑰

若要使用景點圖片下載功能，您需要先獲取Google Maps API金鑰：

1. 前往[Google Cloud Console](https://console.cloud.google.com/)
2. 登入您的Google帳戶並創建一個新專案
3. 在左側選單中選擇「API和服務」>「程式庫」
4. 搜尋並啟用以下API：
   - Places API
   - Maps JavaScript API
5. 在「API和服務」>「憑證」頁面中創建API金鑰
6. 將API金鑰複製到專案的`.env`檔案中

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
