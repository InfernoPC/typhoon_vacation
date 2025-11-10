## 使用說明

本專案會抓取 `行政院人事行政總處 天然災害停止上班及上課情形`（見來源連結），解析各縣市之「放假/不放假」資訊，並將每個縣市輸出為各別 JSON 檔至 `output/` 目錄；頁面「更新時間」統一寫入 `output/execution_log.txt`。

- 來源：`https://www.dgpa.gov.tw/typh/daily/nds.html`

### 環境需求
- Python 3.9+（建議 3.10+）

### 安裝
```bash
python -m venv .venv
source .venv/Scripts/activate  # Windows Git Bash
# 或 PowerShell: .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```

### 執行
```bash
python scrape_typhoon_vacation.py
```

### 輸出
- 產出目錄：`output/`
- 檔名：`{縣市名稱}.json`
- JSON 欄位：
  - `source`: 來源連結
  - `county`: 縣市名稱
  - `status`: 狀態（停止上班上課或未停等），若某縣市原本有資料但重新抓取後沒有資料，則 `status` 為空字串但檔案保留
- 統一執行紀錄：`output/execution_log.json`
  - 包含 `source`、`county_count`、`local_generation_time`、`update_time`（如有）

若網站版面異動導致解析不到資料，腳本會印出警告訊息，請回報或調整解析邏輯。

## GitHub Actions 自動化

本專案包含 GitHub Actions workflow，會自動執行爬蟲並提交更新：

### 自動執行
- **排程**：每小時執行一次（UTC 時間整點）
- **觸發條件**：
  - 定時排程（cron）
  - 手動觸發（workflow_dispatch）
  - 當 main/master 分支有 push 時（但會忽略 output/ 目錄的變更，避免無限循環）

### 自動提交
- 當 `output/` 目錄有變更時，會自動提交並推送到倉庫
- Commit 訊息格式：`chore: 更新颱風放假資料 [YYYY-MM-DD HH:MM:SS UTC]`
- 若沒有變更，則跳過提交步驟

### 設定說明
1. 確保倉庫已啟用 GitHub Actions
2. 確保 `output/` 目錄已提交到 Git（不被 .gitignore 忽略）
3. Workflow 會自動使用 `GITHUB_TOKEN` 進行提交，無需額外設定

### 手動觸發
在 GitHub 倉庫頁面：
1. 進入 **Actions** 標籤
2. 選擇 **Scrape Typhoon Vacation Data** workflow
3. 點擊 **Run workflow** 按鈕


