#!/usr/bin/env python3
"""
發送颱風假異動通知到 Microsoft Power Automate
當臺北市或新北市的颱風假狀態有變更時，發送 Adaptive Card 通知
"""

import json
import os
import sys
import requests
from typing import Dict, Optional


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


def create_adaptive_card(changes: Dict[str, tuple[str, str]]) -> Dict:
    """
    建立 Adaptive Card 訊息
    changes: {縣市名: (變更前狀態, 變更後狀態)}
    """
    body = [
        {
            "type": "TextBlock",
            "text": "🌀 颱風假異動通知",
            "wrap": True,
            "size": "Large",
            "weight": "Bolder",
            "color": "Attention"
        },
        {
            "type": "TextBlock",
            "text": "以下縣市的颱風假狀態已更新：",
            "wrap": True,
            "spacing": "Small"
        }
    ]
    
    # 為每個有變更的縣市加入資訊
    for county, (before_status, after_status) in changes.items():
        body.extend([
            {
                "type": "Container",
                "spacing": "Medium",
                "separator": True,
                "items": [
                    {
                        "type": "TextBlock",
                        "text": f"**{county}**",
                        "wrap": True,
                        "weight": "Bolder",
                        "size": "Medium"
                    },
                    {
                        "type": "FactSet",
                        "facts": [
                            {
                                "title": "變更前：",
                                "value": before_status
                            },
                            {
                                "title": "變更後：",
                                "value": after_status
                            }
                        ]
                    }
                ]
            }
        ])
    
    # 加入底部資訊和連結
    body.extend([
        {
            "type": "TextBlock",
            "text": "📍 資料來源：行政院人事行政總處",
            "wrap": True,
            "spacing": "Medium",
            "isSubtle": True,
            "size": "Small"
        },
        {
            "type": "ActionSet",
            "spacing": "Small",
            "actions": [
                {
                    "type": "Action.OpenUrl",
                    "title": "📦 GitHub Repo",
                    "url": "https://github.com/InfernoPC/typhoon_vacation"
                },
                {
                    "type": "Action.OpenUrl",
                    "title": "⚡ Power Automate Flow",
                    "url": "https://make.powerautomate.com/environments/ce11858d-af1c-e80a-9766-7541e365ec90/flows/c0119267-9a89-46a5-b285-8c9d6e5f1211/details"
                }
            ]
        }
    ])
    
    return {
        "message": {
            "type": "AdaptiveCard",
            "body": body,
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4"
        }
    }


def send_notification(endpoint_url: str, changes: Dict[str, tuple[str, str]]) -> bool:
    """
    發送通知到 Power Automate
    返回: 是否成功發送
    """
    if not endpoint_url:
        print("錯誤: 未提供 Power Automate endpoint URL")
        return False
    
    if not changes:
        print("資訊: 沒有需要通知的變更")
        return True
    
    card_data = create_adaptive_card(changes)
    
    try:
        print(f"發送通知到 Power Automate...")
        print(f"變更的縣市: {', '.join(changes.keys())}")
        
        response = requests.post(
            endpoint_url,
            json=card_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200 or response.status_code == 202:
            print("✅ 通知發送成功")
            return True
        else:
            print(f"❌ 通知發送失敗: HTTP {response.status_code}")
            print(f"回應內容: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 發送通知時逾時")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 發送通知時發生錯誤: {e}")
        return False


def main():
    """主程式"""
    # 從環境變數取得 Power Automate endpoint
    endpoint_url = os.environ.get('POWER_AUTOMATE_ENDPOINT', '')
    
    if not endpoint_url:
        print("警告: 未設定 POWER_AUTOMATE_ENDPOINT 環境變數")
        print("請在 GitHub Action 中設定此環境變數")
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
    if endpoint_url:
        success = send_notification(endpoint_url, changes)
        return 0 if success else 1
    else:
        print("\n預覽通知內容:")
        card_data = create_adaptive_card(changes)
        print(json.dumps(card_data, ensure_ascii=False, indent=2))
        return 0


if __name__ == '__main__':
    sys.exit(main())
