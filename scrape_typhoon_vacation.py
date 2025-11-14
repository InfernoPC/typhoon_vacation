#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, Tuple, List

import requests
from bs4 import BeautifulSoup
import json


DGPA_URL = "https://www.dgpa.gov.tw/typh/daily/nds.html"
OUTPUT_DIR = Path("output")
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT_SEC = 20


def fetch_page(url: str) -> str:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        "Connection": "close",
    }
    resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SEC)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    return resp.text


def normalize_filename(name: str) -> str:
    # Windows 不允許 \ / : * ? " < > |，也避免首尾空白與控制字元
    name = name.strip()
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    # 避免隱藏檔和空檔名
    if not name or name in {".", ".."}:
        name = f"unknown_{int(time.time())}"
    return name


def extract_update_time(soup: BeautifulSoup) -> str:
    # 頁面有「更新時間：YYYY/MM/DD HH:MM:SS」樣式，容忍空白與中文冒號差異
    text = soup.get_text(" ", strip=True)
    m = re.search(r"(更新時間)\s*[:：]\s*([0-9]{4}/[0-9]{1,2}/[0-9]{1,2}\s+[0-9]{1,2}:[0-9]{2}:[0-9]{2})", text)
    if m:
        return m.group(2)
    return ""


def parse_county_rows(soup: BeautifulSoup) -> List[Tuple[str, str]]:
    """
    回傳 [(縣市名稱, 狀態字串), ...]
    嘗試尋找頁面中的資料表格，若結構異動則盡量容錯。
    新格式：第一欄為區域（可能跨列），第二欄為縣市，第三欄為狀態
    """
    results: List[Tuple[str, str]] = []

    # 嘗試找含有「停止上班」或「上班上課」的表格
    tables = soup.find_all("table")
    candidate_tables = []
    for tbl in tables:
        text_content = tbl.get_text(" ", strip=True)
        # 尋找包含縣市資料的表格
        if ("停止上班" in text_content or "上班上課" in text_content or "尚未宣布" in text_content):
            candidate_tables.append(tbl)

    target_table = candidate_tables[0] if candidate_tables else (tables[0] if tables else None)
    if not target_table:
        return results

    # 讀取資料列
    rows = target_table.find_all("tr")
    
    # 定義區域名稱，用於過濾
    regions = {"北部地區", "中部地區", "南部地區", "東部地區", "外島地區", "區域"}
    
    for tr in rows:
        cells = tr.find_all(["td", "th"])
        if len(cells) < 2:
            continue
        
        # 新格式：三欄（區域、縣市、狀態）或兩欄（縣市、狀態）
        if len(cells) >= 3:
            # 三欄格式：區域 | 縣市 | 狀態
            region = cells[0].get_text(" ", strip=True)
            county = cells[1].get_text(" ", strip=True)
            status = cells[2].get_text(" ", strip=True)
            
            # 略過標題列和區域名稱（不儲存區域資料）
            if county in ["縣市名稱", "縣市", ""] or "備註" in county:
                continue
            
            # 略過區域本身（不將區域當作縣市儲存）
            if county in regions:
                continue
            
            results.append((county, status))
            
        elif len(cells) == 2:
            # 兩欄格式：縣市 | 狀態
            county = cells[0].get_text(" ", strip=True)
            status = cells[1].get_text(" ", strip=True)
            
            # 略過標題列、空白和區域名稱
            if not county or county in ["縣市名稱", "縣市", "區域"] or "備註" in county:
                continue
            
            # 略過區域本身
            if county in regions:
                continue
            
            results.append((county, status))

    return results


def get_existing_counties() -> Dict[str, str]:
    """
    讀取 output 目錄中現有的縣市 JSON 檔案，回傳 {縣市名稱: 檔案路徑} 的字典。
    跳過 execution_log.json。
    """
    existing = {}
    if not OUTPUT_DIR.exists():
        return existing
    
    for json_file in OUTPUT_DIR.glob("*.json"):
        if json_file.name == "execution_log.json":
            continue
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "county" in data:
                    county_name = data["county"]
                    existing[county_name] = str(json_file)
        except (json.JSONDecodeError, IOError, KeyError):
            # 如果檔案格式有問題，跳過
            continue
    return existing


def write_outputs(update_time: str, county_status: List[Tuple[str, str]]) -> None:
    """
    寫入縣市資料。如果某個縣市原本有資料但現在沒有了，將其 status 設為空字串並保留檔案。
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 取得現有的縣市檔案
    existing_counties = get_existing_counties()
    
    # 建立新資料的縣市集合
    new_county_set = {county for county, _ in county_status}
    
    # 寫入新抓取的縣市資料
    for county, status in county_status:
        filename = normalize_filename(county) + ".json"
        out_path = OUTPUT_DIR / filename
        payload = {
            "source": DGPA_URL,
            "county": county,
            "status": status,
        }
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")
    
    # 對於舊檔案中存在但新資料中不存在的縣市，清空 status 但保留檔案
    for county_name in existing_counties.keys():
        if county_name not in new_county_set:
            filename = normalize_filename(county_name) + ".json"
            out_path = OUTPUT_DIR / filename
            payload = {
                "source": DGPA_URL,
                "county": county_name,
                "status": "",
            }
            with open(out_path, "w", encoding="utf-8", newline="\n") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
                f.write("\n")


def write_execution_log(update_time: str, county_status: List[Tuple[str, str]]) -> None:
    """
    將更新時間寫到統一的執行紀錄檔，不放在各縣市檔案中。
    可透過環境變數 SKIP_EXECUTION_LOG 來跳過產生 execution_log。
    """
    # 檢查是否要跳過 execution_log
    if os.environ.get("SKIP_EXECUTION_LOG", "").lower() in ("1", "true", "yes"):
        return
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    log_path = OUTPUT_DIR / "execution_log.json"
    payload = {
        "source": DGPA_URL,
        "county_count": len(county_status),
        "local_generation_time": time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    if update_time:
        payload["update_time"] = update_time
    with open(log_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main() -> int:
    try:
        html = fetch_page(DGPA_URL)
    except Exception as e:
        print(f"[ERROR] 下載失敗: {e}", file=sys.stderr)
        return 1

    soup = BeautifulSoup(html, "lxml")
    update_time = extract_update_time(soup)
    county_status = parse_county_rows(soup)

    if not county_status:
        print("[WARN] 未解析到任何縣市資料，請檢查頁面結構是否變動。", file=sys.stderr)

    try:
        write_outputs(update_time, county_status)
        write_execution_log(update_time, county_status)
    except Exception as e:
        print(f"[ERROR] 寫入檔案失敗: {e}", file=sys.stderr)
        return 2

    print(f"完成，輸出檔案於: {OUTPUT_DIR.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
