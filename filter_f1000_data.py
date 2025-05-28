#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
篩選景點_F1000.csv中的景點，並從attractions和image_data資料夾中提取對應資料
"""

import pandas as pd
import os
import shutil
import json
import glob
from pathlib import Path


def create_data_f1000_folder():
    """創建Data_F1000資料夾結構"""
    base_dir = Path("Data_F1000")
    attractions_dir = base_dir / "attractions"
    image_data_dir = base_dir / "image_data"

    # 創建資料夾
    attractions_dir.mkdir(parents=True, exist_ok=True)
    image_data_dir.mkdir(parents=True, exist_ok=True)

    return base_dir, attractions_dir, image_data_dir


def read_f1000_csv():
    """讀取景點_F1000.csv並提取唯一識別碼"""
    try:
        df = pd.read_csv("景點_F1000.csv")
        print(f"成功讀取景點_F1000.csv，共有 {len(df)} 筆資料")

        # 提取唯一識別碼
        attraction_ids = df['唯一識別碼'].tolist()
        print(f"提取出 {len(attraction_ids)} 個景點唯一識別碼")

        return attraction_ids, df
    except Exception as e:
        print(f"讀取CSV檔案時發生錯誤: {e}")
        return None, None


def get_attraction_name_from_json(json_path):
    """從JSON檔案中提取景點名稱"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('資料名稱', 'Unknown')
    except:
        return 'Unknown'


def copy_attractions_data(attraction_ids, attractions_dir):
    """複製attractions資料夾中對應的JSON檔案"""
    source_dir = Path("attractions")
    copied_count = 0

    print("\n開始複製attractions資料...")

    for attraction_id in attraction_ids:
        # 尋找對應的JSON檔案
        json_file = source_dir / f"{attraction_id}.json"

        if json_file.exists():
            # 複製檔案
            destination = attractions_dir / f"{attraction_id}.json"
            shutil.copy2(json_file, destination)

            # 獲取景點名稱用於顯示
            attraction_name = get_attraction_name_from_json(json_file)
            print(f"✓ 複製: {attraction_id} - {attraction_name}")
            copied_count += 1
        else:
            print(f"✗ 找不到檔案: {attraction_id}.json")

    print(f"\n共複製了 {copied_count} 個attractions檔案")
    return copied_count


def find_matching_image_folders(attraction_ids, df):
    """根據景點名稱尋找image_data中對應的資料夾"""
    image_source_dir = Path("image_data")
    attraction_names = df['資料名稱'].tolist()

    # 創建ID到名稱的映射
    id_to_name = dict(zip(attraction_ids, attraction_names))

    # 獲取image_data中所有資料夾名稱
    available_folders = [
        d.name for d in image_source_dir.iterdir() if d.is_dir()]

    matching_folders = []

    print("\n檢查image_data資料夾對應關係...")

    for attraction_id in attraction_ids:
        attraction_name = id_to_name.get(attraction_id, '')

        # 嘗試直接匹配名稱
        if attraction_name in available_folders:
            matching_folders.append(
                (attraction_id, attraction_name, attraction_name))
            print(f"✓ 找到匹配: {attraction_id} - {attraction_name}")
        else:
            # 嘗試部分匹配
            found = False
            for folder_name in available_folders:
                if attraction_name in folder_name or folder_name in attraction_name:
                    matching_folders.append(
                        (attraction_id, attraction_name, folder_name))
                    print(
                        f"✓ 部分匹配: {attraction_id} - {attraction_name} -> {folder_name}")
                    found = True
                    break

            if not found:
                print(f"✗ 找不到匹配: {attraction_id} - {attraction_name}")

    return matching_folders


def copy_image_data(matching_folders, image_data_dir):
    """複製對應的image_data資料夾"""
    source_dir = Path("image_data")
    copied_count = 0

    print("\n開始複製image_data資料...")

    for attraction_id, attraction_name, folder_name in matching_folders:
        source_folder = source_dir / folder_name
        destination_folder = image_data_dir / folder_name

        if source_folder.exists() and source_folder.is_dir():
            try:
                shutil.copytree(source_folder, destination_folder)
                print(f"✓ 複製資料夾: {folder_name}")
                copied_count += 1
            except Exception as e:
                print(f"✗ 複製失敗 {folder_name}: {e}")
        else:
            print(f"✗ 資料夾不存在: {folder_name}")

    print(f"\n共複製了 {copied_count} 個image_data資料夾")
    return copied_count


def create_summary_report(base_dir, attraction_ids, attractions_copied, images_copied, df):
    """創建處理摘要報告"""
    report_path = base_dir / "處理摘要.txt"

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("Data_F1000 資料處理摘要\n")
        f.write("=" * 50 + "\n\n")
        f.write(
            f"處理時間: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"景點_F1000.csv 總數: {len(attraction_ids)}\n")
        f.write(f"成功複製的 attractions 檔案: {attractions_copied}\n")
        f.write(f"成功複製的 image_data 資料夾: {images_copied}\n\n")

        f.write("詳細景點清單:\n")
        f.write("-" * 30 + "\n")
        for i, (_, row) in enumerate(df.iterrows(), 1):
            f.write(f"{i:3d}. {row['唯一識別碼']} - {row['資料名稱']}\n")

    print(f"\n摘要報告已保存至: {report_path}")


def main():
    """主函數"""
    print("開始處理景點_F1000資料...")

    # 讀取CSV檔案
    attraction_ids, df = read_f1000_csv()
    if attraction_ids is None:
        return

    # 創建目標資料夾
    base_dir, attractions_dir, image_data_dir = create_data_f1000_folder()
    print(f"已創建資料夾: {base_dir}")

    # 複製attractions資料
    attractions_copied = copy_attractions_data(attraction_ids, attractions_dir)

    # 尋找並複製image_data資料
    matching_folders = find_matching_image_folders(attraction_ids, df)
    images_copied = copy_image_data(matching_folders, image_data_dir)

    # 創建摘要報告
    create_summary_report(base_dir, attraction_ids,
                          attractions_copied, images_copied, df)

    print("\n" + "=" * 50)
    print("處理完成!")
    print(f"總景點數: {len(attraction_ids)}")
    print(f"成功複製 attractions 檔案: {attractions_copied}")
    print(f"成功複製 image_data 資料夾: {images_copied}")
    print(f"資料已保存至: {base_dir}")
    print("=" * 50)


if __name__ == "__main__":
    main()
