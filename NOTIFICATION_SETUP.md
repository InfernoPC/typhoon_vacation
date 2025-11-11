# 通知功能設定指南

本指南說明如何設定 Power Automate 通知功能，當臺北市或新北市的颱風假狀態有變更時，自動發送通知到 Microsoft Teams。

## 📋 功能說明

- **監控縣市**: 臺北市、新北市
- **觸發條件**: 當這兩個縣市的颱風假狀態有變更時
- **通知內容**: 
  - 變更的縣市名稱
  - 變更前的狀態
  - 變更後的狀態
  - 資料來源資訊
- **智慧過濾**: 只有狀態真的改變時才發送通知，避免重複通知

## 🔧 設定步驟

### 步驟 1: 建立 Power Automate Flow

1. 前往 [Power Automate](https://make.powerautomate.com/)
2. 建立新的 Flow
3. 選擇觸發器：**When a HTTP request is received**
4. 在觸發器中，會自動產生一個 HTTP POST URL（endpoint）
5. 加入動作：**Post adaptive card in a chat or channel**
6. 設定要發送的 Teams 頻道或聊天室
7. 在 Adaptive Card 欄位中，使用動態內容：`triggerBody()?['message']`
8. 儲存 Flow 並複製 HTTP POST URL

### 步驟 2: 在 GitHub 設定 Secret

1. 前往你的 GitHub 倉庫
2. 點擊 **Settings** > **Secrets and variables** > **Actions**
3. 點擊 **New repository secret**
4. 填寫：
   - **Name**: `POWER_AUTOMATE_ENDPOINT`
   - **Secret**: 貼上步驟 1 複製的 HTTP POST URL
5. 點擊 **Add secret**

### 步驟 3: 測試通知功能

在本地測試（不實際發送）：

```bash
# 顯示預覽內容，不實際發送
python send_notification.py
```

在本地測試（實際發送）：

```bash
# 使用測試腳本發送測試通知
python test_notification.py <你的-POWER_AUTOMATE_ENDPOINT>

# 或設定環境變數
export POWER_AUTOMATE_ENDPOINT="你的-POWER_AUTOMATE_ENDPOINT"
python test_notification.py
```

### 步驟 4: 驗證自動化運作

1. 等待下一次 GitHub Actions 自動執行（每小時整點）
2. 或手動觸發 workflow：
   - 前往 GitHub 倉庫的 **Actions** 標籤
   - 選擇 **Scrape Typhoon Vacation Data**
   - 點擊 **Run workflow**
3. 查看執行記錄，確認 "Send notification to Power Automate" 步驟是否執行
4. 檢查 Teams 頻道是否收到通知

## 📝 通知卡片格式範例

當臺北市有變更時，Teams 會收到類似以下的 Adaptive Card：

```
🌀 颱風假異動通知

以下縣市的颱風假狀態已更新：

─────────────────────────
**臺北市**

變更前：  正常上班、正常上課。
變更後：  士林區永福里、新安里、陽明里、公館里、菁山里、
         平等里、溪山里、翠山里:今天停止上班、停止上課。 
         北投區湖田里、湖山里、大屯里、泉源里:今天停止上班、
         停止上課。

📍 資料來源：行政院人事行政總處
```

## 🔍 檢查執行狀態

### 在 GitHub Actions 中檢查

1. 前往 **Actions** 標籤
2. 點擊最近的 workflow 執行
3. 查看 "Send notification to Power Automate" 步驟
4. 如果看到 "✅ 通知發送成功"，表示通知已成功發送

### 查看執行條件

通知只會在以下情況執行：
- `output/臺北市.json` 或 `output/新北市.json` 有變更
- **且** 狀態內容確實不同（不是只有時間戳記變更）

## 🐛 疑難排解

### 問題：沒有收到通知

檢查清單：
- [ ] 確認 GitHub Secret `POWER_AUTOMATE_ENDPOINT` 已正確設定
- [ ] 確認 Power Automate Flow 處於「已開啟」狀態
- [ ] 檢查 GitHub Actions 執行記錄中是否有錯誤訊息
- [ ] 確認臺北市或新北市的狀態確實有變更（不是只有時間戳記）
- [ ] 檢查 Power Automate Flow 的執行歷史

### 問題：通知內容不正確

1. 檢查 `send_notification.py` 中的 `create_adaptive_card()` 函數
2. 使用 `test_notification.py` 發送測試通知來驗證格式
3. 確認 Power Automate 中的 Adaptive Card 設定正確

### 問題：收到重複通知

- 檢查程式碼是否正確比對變更前後的狀態
- 確認 git diff 邏輯運作正常
- 檢查是否有多個 workflow 同時執行

## 📚 相關檔案

- `send_notification.py`: 主要通知程式
- `test_notification.py`: 測試通知功能
- `.github/workflows/scrape_typhoon_vacation.yml`: GitHub Actions 工作流程
- `README.md`: 專案說明文件

## 🔗 參考資源

- [Power Automate 文件](https://docs.microsoft.com/power-automate/)
- [Adaptive Cards 設計工具](https://adaptivecards.io/designer/)
- [GitHub Actions 文件](https://docs.github.com/actions)
- [行政院人事行政總處](https://www.dgpa.gov.tw/typh/daily/nds.html)

## 💡 提示

- 建議先使用 `test_notification.py` 測試通知是否正常運作
- 可以修改 `send_notification.py` 中的 Adaptive Card 格式來客製化通知樣式
- 如果要監控其他縣市，修改 `send_notification.py` 中的 `counties_to_check` 列表
- Power Automate endpoint URL 應該保密，不要提交到版本控制中
