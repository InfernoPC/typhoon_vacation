#!/usr/bin/env python3
"""
發送颱風假異動通知到 Telegram
當臺北市或新北市的颱風假狀態有變更時，透過 Telegram Bot 發送通知
"""

import html
import json
import os
import sys
import time
import requests
from typing import Dict, Optional

GITHUB_REPO_URL = "https://github.com/InfernoPC/typhoon_vacation"

# Windows 主控台預設編碼 (cp950) 無法輸出部分符號，統一改用 UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout.reconfigure(encoding='utf-8')


def load_json_file(filepath: str) -> Optional[Dict]:
    """載入 JSON 檔案"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"警告: 找不到檔案 {filepath}")
        return None
    except json.JSONDecodeError as e:
        print(f"錯誤: 無法解析 JSON 檔案 {filepath}: {e}")
        return None


def get_git_diff_status(county: str) -> tuple[Optional[str], Optional[str]]:
    """
    使用 git diff 取得某個縣市的變更前後狀態
    返回: (變更前的 status, 變更後的 status)
    """
    import subprocess

    filename = f"output/{county}.json"

    try:
        # 取得變更前的內容 (HEAD)
        result_before = subprocess.run(
            ['git', 'show', f'HEAD:{filename}'],
            capture_output=True,
            text=True,
            encoding='utf-8',  # 檔案內容為 UTF-8，避免 Windows 預設 cp950 解碼失敗
            check=False
        )

        before_data = None
        if result_before.returncode == 0:
            try:
                before_data = json.loads(result_before.stdout)
            except json.JSONDecodeError:
                print(f"警告: 無法解析 {county} 的歷史資料")

        # 取得變更後的內容 (當前檔案)
        after_data = load_json_file(filename)

        before_status = before_data.get('status', '正常上班、正常上課。') if before_data else '正常上班、正常上課。'
        after_status = after_data.get('status', '正常上班、正常上課。') if after_data else '正常上班、正常上課。'

        # 只有在狀態真的有變更時才返回
        if before_status != after_status:
            return before_status, after_status
        else:
            return None, None

    except Exception as e:
        print(f"錯誤: 取得 {county} 的 git diff 時發生錯誤: {e}")
        return None, None


def create_telegram_message(changes: Dict[str, tuple[str, str]]) -> str:
    """
    建立 Telegram 通知訊息 (HTML 格式)
    changes: {縣市名: (變更前狀態, 變更後狀態)}
    """
    lines = [
        "🌀 <b>颱風假異動通知</b>",
        "",
        "以下縣市的颱風假狀態已更新：",
    ]

    for county, (before_status, after_status) in changes.items():
        lines.extend([
            "",
            f"<b>{html.escape(county)}</b>",
            f"變更前：{html.escape(before_status)}",
            f"變更後：{html.escape(after_status)}",
        ])

    lines.extend([
        "",
        "📍 資料來源：行政院人事行政總處",
    ])

    return "\n".join(lines)


def send_notification(bot_token: str, chat_id: str, changes: Dict[str, tuple[str, str]]) -> bool:
    """
    發送通知到 Telegram
    返回: 是否成功發送
    """
    if not bot_token or not chat_id:
        print("錯誤: 未提供 Telegram Bot Token 或 Chat ID")
        return False

    if not changes:
        print("資訊: 沒有需要通知的變更")
        return True

    payload = {
        'chat_id': chat_id,
        'text': create_telegram_message(changes),
        'parse_mode': 'HTML',
        'disable_web_page_preview': True,
        'reply_markup': {
            'inline_keyboard': [[
                {'text': '📦 GitHub Repo', 'url': GITHUB_REPO_URL}
            ]]
        }
    }

    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    max_attempts = 3
    retry_delay = 5

    print("發送通知到 Telegram...")
    print(f"變更的縣市: {', '.join(changes.keys())}")

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.post(api_url, json=payload, timeout=30)

            if response.status_code == 200 and response.json().get('ok'):
                print("✅ 通知發送成功")
                return True

            # 注意: 錯誤訊息不可印出 API URL，避免洩漏 bot token
            try:
                description = response.json().get('description', '')
            except ValueError:
                description = ''
            print(f"❌ 通知發送失敗 (第 {attempt} 次): HTTP {response.status_code} {description}")

        except requests.exceptions.Timeout:
            print(f"❌ 發送通知時逾時 (第 {attempt} 次)")
        except requests.exceptions.RequestException as e:
            print(f"❌ 發送通知時發生錯誤 (第 {attempt} 次): {type(e).__name__}")

        if attempt < max_attempts:
            print(f"等待 {retry_delay} 秒後重試...")
            time.sleep(retry_delay)

    return False


def main():
    """主程式"""
    # 從環境變數取得 Telegram Bot 設定
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')

    if not bot_token or not chat_id:
        print("警告: 未設定 TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID 環境變數")
        print("請在 GitHub Action 中設定這些環境變數")
        # 在開發環境中可以選擇不中斷執行
        if os.environ.get('GITHUB_ACTIONS') == 'true':
            sys.exit(1)
        else:
            print("繼續執行（開發模式）...")

    # 檢查臺北市和新北市是否有變更
    counties_to_check = ['臺北市', '新北市']
    changes = {}

    for county in counties_to_check:
        print(f"檢查 {county} 的變更狀態...")
        before_status, after_status = get_git_diff_status(county)

        if before_status is not None and after_status is not None:
            print(f"✓ {county} 有變更")
            changes[county] = (before_status, after_status)
        else:
            print(f"  {county} 無變更或無法取得差異")

    if not changes:
        print("\n✓ 臺北市和新北市都沒有狀態變更")
        return 0

    print(f"\n發現 {len(changes)} 個縣市有變更")

    # 發送通知
    if bot_token and chat_id:
        success = send_notification(bot_token, chat_id, changes)
        return 0 if success else 1
    else:
        print("\n預覽通知內容:")
        print(create_telegram_message(changes))
        return 0


if __name__ == '__main__':
    sys.exit(main())
