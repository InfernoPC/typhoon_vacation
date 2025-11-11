#!/usr/bin/env python3
"""
測試通知功能的腳本
用於測試 Power Automate 通知是否正常運作
"""

import json
import os
import sys
import requests


def create_test_adaptive_card() -> dict:
    """建立測試用的 Adaptive Card"""
    return {
        "message": {
            "type": "AdaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "🧪 測試通知",
                    "wrap": True,
                    "size": "Large",
                    "weight": "Bolder",
                    "color": "Good"
                },
                {
                    "type": "TextBlock",
                    "text": "這是一則測試通知，用於驗證 Power Automate 整合是否正常運作。",
                    "wrap": True,
                    "spacing": "Small"
                },
                {
                    "type": "Container",
                    "spacing": "Medium",
                    "separator": True,
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "**臺北市**",
                            "wrap": True,
                            "weight": "Bolder",
                            "size": "Medium"
                        },
                        {
                            "type": "FactSet",
                            "facts": [
                                {
                                    "title": "變更前：",
                                    "value": "正常上班、正常上課。"
                                },
                                {
                                    "title": "變更後：",
                                    "value": "士林區永福里、新安里、陽明里、公館里、菁山里、平等里、溪山里、翠山里:今天停止上班、停止上課。 北投區湖田里、湖山里、大屯里、泉源里:今天停止上班、停止上課。"
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "TextBlock",
                    "text": "📍 這是測試通知，並非實際颱風假異動",
                    "wrap": True,
                    "spacing": "Medium",
                    "isSubtle": True,
                    "size": "Small",
                    "color": "Attention"
                }
            ],
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4"
        }
    }


def send_test_notification(endpoint_url: str) -> bool:
    """發送測試通知"""
    if not endpoint_url:
        print("錯誤: 未提供 Power Automate endpoint URL")
        print("\n使用方式:")
        print("  python test_notification.py <POWER_AUTOMATE_ENDPOINT>")
        print("\n或設定環境變數:")
        print("  export POWER_AUTOMATE_ENDPOINT='your-endpoint-url'")
        print("  python test_notification.py")
        return False
    
    card_data = create_test_adaptive_card()
    
    print("=" * 60)
    print("發送測試通知...")
    print("=" * 60)
    print(f"Endpoint: {endpoint_url[:50]}...")
    print("\n通知內容預覽:")
    print(json.dumps(card_data, ensure_ascii=False, indent=2))
    print("\n" + "=" * 60)
    
    try:
        response = requests.post(
            endpoint_url,
            json=card_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"HTTP 狀態碼: {response.status_code}")
        
        if response.status_code in (200, 202):
            print("✅ 測試通知發送成功！")
            print("\n請檢查你的 Microsoft Teams 頻道是否收到通知。")
            return True
        else:
            print(f"❌ 測試通知發送失敗")
            print(f"回應內容: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 發送通知時逾時（超過 30 秒）")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 發送通知時發生錯誤: {e}")
        return False


def main():
    """主程式"""
    # 從命令列參數或環境變數取得 endpoint
    if len(sys.argv) > 1:
        endpoint_url = sys.argv[1]
    else:
        endpoint_url = os.environ.get('POWER_AUTOMATE_ENDPOINT', '')
    
    if not endpoint_url:
        print("錯誤: 未提供 Power Automate endpoint URL")
        print("\n使用方式:")
        print("  python test_notification.py <POWER_AUTOMATE_ENDPOINT>")
        print("\n或設定環境變數:")
        print("  export POWER_AUTOMATE_ENDPOINT='your-endpoint-url'")
        print("  python test_notification.py")
        return 1
    
    success = send_test_notification(endpoint_url)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
