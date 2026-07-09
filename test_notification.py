#!/usr/bin/env python3
"""
測試通知功能的腳本
用於測試 Telegram 通知是否正常運作
"""

import os
import sys
import requests

GITHUB_REPO_URL = "https://github.com/InfernoPC/typhoon_vacation"

# Windows 主控台預設編碼 (cp950) 無法輸出部分符號，統一改用 UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout.reconfigure(encoding='utf-8')


def create_test_message() -> str:
    """建立測試用的 Telegram 訊息 (HTML 格式)"""
    return "\n".join([
        "🧪 <b>測試通知</b>",
        "",
        "這是一則測試通知，用於驗證 Telegram 整合是否正常運作。",
        "",
        "<b>臺北市</b>",
        "變更前：正常上班、正常上課。",
        "變更後：士林區永福里、新安里、陽明里、公館里、菁山里、平等里、溪山里、翠山里:今天停止上班、停止上課。 "
        "北投區湖田里、湖山里、大屯里、泉源里:今天停止上班、停止上課。",
        "",
        "📍 這是測試通知，並非實際颱風假異動",
    ])


def mask_token(token: str) -> str:
    """遮蔽 token，只顯示前 10 碼"""
    return f"{token[:10]}..." if len(token) > 10 else "***"


def send_test_notification(bot_token: str, chat_id: str) -> bool:
    """發送測試通知"""
    message = create_test_message()

    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True,
        'reply_markup': {
            'inline_keyboard': [[
                {'text': '📦 GitHub Repo', 'url': GITHUB_REPO_URL}
            ]]
        }
    }

    print("=" * 60)
    print("發送測試通知...")
    print("=" * 60)
    print(f"Bot Token: {mask_token(bot_token)}")
    print(f"Chat ID: {chat_id}")
    print("\n通知內容預覽:")
    print(message)
    print("\n" + "=" * 60)

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json=payload,
            timeout=30
        )

        print(f"HTTP 狀態碼: {response.status_code}")

        if response.status_code == 200 and response.json().get('ok'):
            print("✅ 測試通知發送成功！")
            print("\n請檢查你的 Telegram 是否收到通知。")
            return True
        else:
            # 注意: 不可印出 API URL，避免洩漏 bot token
            try:
                description = response.json().get('description', '')
            except ValueError:
                description = ''
            print("❌ 測試通知發送失敗")
            print(f"錯誤說明: {description}")
            return False

    except requests.exceptions.Timeout:
        print("❌ 發送通知時逾時（超過 30 秒）")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 發送通知時發生錯誤: {type(e).__name__}")
        return False


def print_usage():
    print("\n使用方式:")
    print("  python test_notification.py <TELEGRAM_BOT_TOKEN> <TELEGRAM_CHAT_ID>")
    print("\n或設定環境變數:")
    print("  export TELEGRAM_BOT_TOKEN='your-bot-token'")
    print("  export TELEGRAM_CHAT_ID='your-chat-id'")
    print("  python test_notification.py")


def main():
    """主程式"""
    # 從命令列參數或環境變數取得 bot token 和 chat id
    if len(sys.argv) > 2:
        bot_token = sys.argv[1]
        chat_id = sys.argv[2]
    else:
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')

    if not bot_token or not chat_id:
        print("錯誤: 未提供 Telegram Bot Token 或 Chat ID")
        print_usage()
        return 1

    success = send_test_notification(bot_token, chat_id)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
