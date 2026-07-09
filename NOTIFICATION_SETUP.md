# 通知功能設定指南

本指南說明如何設定 Telegram 通知功能，當臺北市或新北市的颱風假狀態有變更時，透過 Telegram Bot 自動發送通知。

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

### 步驟 1: 建立 Telegram Bot 並取得 Chat ID

1. 在 Telegram 中搜尋 [@BotFather](https://t.me/BotFather)
2. 傳送 `/newbot`，依指示設定 Bot 名稱與 username
3. BotFather 會回覆一組 **Bot Token**（格式類似 `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`），請妥善保存
4. 取得 **Chat ID**：
   - 通知到個人：先傳一則訊息給你的 Bot，再開啟
     `https://api.telegram.org/bot<你的-BOT-TOKEN>/getUpdates`，從回應中的 `chat.id` 取得
   - 通知到群組：將 Bot 加入群組並在群組中傳一則訊息，再用同樣方式從 `getUpdates` 取得（群組的 Chat ID 為負數）

### 步驟 2: 在 GitHub 設定 Secrets

1. 前往你的 GitHub 倉庫
2. 點擊 **Settings** > **Secrets and variables** > **Actions**
3. 點擊 **New repository secret**，新增以下兩個 Secret：
   - **Name**: `TELEGRAM_BOT_TOKEN`，**Secret**: 步驟 1 取得的 Bot Token
   - **Name**: `TELEGRAM_CHAT_ID`，**Secret**: 步驟 1 取得的 Chat ID

### 步驟 3: 測試通知功能

在本地測試（不實際發送）：

```bash
# 顯示預覽內容，不實際發送
python send_notification.py
```

在本地測試（實際發送）：

```bash
# 使用測試腳本發送測試通知
python test_notification.py <你的-BOT-TOKEN> <你的-CHAT-ID>

# 或設定環境變數
export TELEGRAM_BOT_TOKEN="你的-BOT-TOKEN"
export TELEGRAM_CHAT_ID="你的-CHAT-ID"
python test_notification.py
```

### 步驟 4: 驗證自動化運作

1. 等待下一次 GitHub Actions 自動執行（每小時整點）
2. 或手動觸發 workflow：
   - 前往 GitHub 倉庫的 **Actions** 標籤
   - 選擇 **Scrape Typhoon Vacation Data**
   - 點擊 **Run workflow**
3. 查看執行記錄，確認 "Send notification to Telegram" 步驟是否執行
4. 檢查 Telegram 是否收到通知

## 📝 通知訊息格式範例

當臺北市有變更時，Telegram 會收到類似以下的訊息：

```
🌀 颱風假異動通知

以下縣市的颱風假狀態已更新：

臺北市
變更前：正常上班、正常上課。
變更後：士林區永福里、新安里、陽明里、公館里、菁山里、
       平等里、溪山里、翠山里:今天停止上班、停止上課。
       北投區湖田里、湖山里、大屯里、泉源里:今天停止上班、
       停止上課。

📍 資料來源：行政院人事行政總處
```

訊息下方附有「📦 GitHub Repo」按鈕，可直接開啟本專案頁面。

## 🔍 檢查執行狀態

### 在 GitHub Actions 中檢查

1. 前往 **Actions** 標籤
2. 點擊最近的 workflow 執行
3. 查看 "Send notification to Telegram" 步驟
4. 如果看到 "✅ 通知發送成功"，表示通知已成功發送

### 查看執行條件

通知只會在以下情況執行：
- `output/臺北市.json` 或 `output/新北市.json` 有變更
- **且** 狀態內容確實不同（不是只有時間戳記變更）

## 🐛 疑難排解

### 問題：沒有收到通知

檢查清單：
- [ ] 確認 GitHub Secrets `TELEGRAM_BOT_TOKEN` 和 `TELEGRAM_CHAT_ID` 已正確設定
- [ ] 確認 Chat ID 正確（群組 ID 為負數；群組升級為 supergroup 後 ID 會改變）
- [ ] 若通知到群組，確認 Bot 仍在群組中且未被封鎖
- [ ] 檢查 GitHub Actions 執行記錄中是否有錯誤訊息
- [ ] 確認臺北市或新北市的狀態確實有變更（不是只有時間戳記）

### 問題：通知內容不正確

1. 檢查 `send_notification.py` 中的 `create_telegram_message()` 函數
2. 使用 `test_notification.py` 發送測試通知來驗證格式

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

- [Telegram Bot API 文件](https://core.telegram.org/bots/api)
- [BotFather](https://t.me/BotFather)
- [GitHub Actions 文件](https://docs.github.com/actions)
- [行政院人事行政總處](https://www.dgpa.gov.tw/typh/daily/nds.html)

## 💡 提示

- 建議先使用 `test_notification.py` 測試通知是否正常運作
- 可以修改 `send_notification.py` 中的 `create_telegram_message()` 來客製化通知樣式
- 如果要監控其他縣市，修改 `send_notification.py` 中的 `counties_to_check` 列表
- Bot Token 應該保密，不要提交到版本控制中
