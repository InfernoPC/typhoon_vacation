# 使用說明

本專案會抓取 `行政院人事行政總處 天然災害停止上班及上課情形`（見來源連結），解析各縣市之「放假/不放假」資訊，並將每個縣市輸出為各別 JSON 檔至 `output/` 目錄。執行記錄可透過 GitHub Actions 執行記錄查詢。

- 來源：`https://www.dgpa.gov.tw/typh/daily/nds.html`

## 免責聲明

本專案僅供學習與研究用途，所提供之資料僅供參考，請勿作為正式公告或決策依據。資料來源及解析方式可能因網站變動而有所誤差，作者不對資料之正確性、即時性或完整性負任何責任。如需正式資訊，請以政府單位公告為準。

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
- 統一執行紀錄：本專案不產生 `execution_log.json`
  - 執行記錄可透過 [GitHub Actions 執行記錄](https://github.com/InfernoPC/typhoon_vacation/actions) 查詢
  - 或使用 GitHub API 程式化查詢最近一次執行狀態

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

### 查詢最近一次執行記錄

本專案不產生 `execution_log.json`，但仍可透過以下方式查詢最近一次執行記錄：

#### 1. 透過 GitHub Actions 網頁介面（推薦）

- **直接連結**：前往倉庫的 [Actions 標籤](https://github.com/InfernoPC/typhoon_vacation/actions)
- 查看 "Scrape Typhoon Vacation Data" workflow 的執行歷史
- 綠色勾號 ✅ 表示執行成功，紅色叉號 ❌ 表示執行失敗
- 點擊執行記錄可查看：
  - 執行時間
  - 執行狀態（有變更/無變更）
  - 詳細日誌
  - Workflow Run ID

#### 2. 使用 GitHub API 查詢（程式化查詢）

**查詢最近的執行記錄：**

```bash
curl -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/InfernoPC/typhoon_vacation/actions/runs?per_page=1
```

**查詢特定 workflow 的執行記錄：**

```bash
# 取得 workflow ID（需要先查詢一次）
WORKFLOW_ID=$(curl -s -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/InfernoPC/typhoon_vacation/actions/workflows | \
  jq -r '.workflows[] | select(.name=="Scrape Typhoon Vacation Data") | .id')

# 查詢該 workflow 的執行記錄
curl -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/InfernoPC/typhoon_vacation/actions/workflows/${WORKFLOW_ID}/runs?per_page=1"
```

**查詢最近一次執行的詳細資訊：**

```bash
# 取得最近一次執行的 run_id
RUN_ID=$(curl -s -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/InfernoPC/typhoon_vacation/actions/runs?per_page=1 | \
  jq -r '.workflow_runs[0].id')

# 查詢執行詳情
curl -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/InfernoPC/typhoon_vacation/actions/runs/${RUN_ID}"
```

**Python 範例：**

```python
import requests

# 查詢最近一次執行
url = "https://api.github.com/repos/InfernoPC/typhoon_vacation/actions/runs?per_page=1"
response = requests.get(url, headers={"Accept": "application/vnd.github.v3+json"})
data = response.json()

if data['workflow_runs']:
    run = data['workflow_runs'][0]
    print(f"執行時間: {run['created_at']}")
    print(f"狀態: {run['status']} - {run['conclusion']}")
    print(f"執行 ID: {run['id']}")
    print(f"執行 URL: {run['html_url']}")
```

#### 3. 查看 Commit 歷史

- 在倉庫主頁面查看 commit 歷史
- 若有自動提交，會看到 commit 訊息：`chore: 更新颱風放假資料 [時間]`
- 作者會顯示為 `github-actions[bot]`
- Commit 時間即為執行時間

#### 4. 查看 JSON 檔案的最後修改時間

- 在 GitHub 上查看 `output/` 目錄中的 JSON 檔案
- 點擊檔案後查看 "Last modified" 時間
- 若時間接近整點（UTC），表示剛執行過

#### 5. 直接連結到最近一次執行

您可以使用以下 URL 格式直接查看執行記錄：

```
https://github.com/InfernoPC/typhoon_vacation/actions/workflows/scrape_typhoon_vacation.yml
```

### 設定說明

1. 確保倉庫已啟用 GitHub Actions
2. 確保 `output/` 目錄已提交到 Git（不被 .gitignore 忽略）
3. Workflow 會自動使用 `GITHUB_TOKEN` 進行提交，無需額外設定

### 手動觸發

在 GitHub 倉庫頁面：

1. 進入 **Actions** 標籤
2. 選擇 **Scrape Typhoon Vacation Data** workflow
3. 點擊 **Run workflow** 按鈕

## API 端點

所有 JSON 檔案可透過 GitHub Raw 內容直接存取，無需 API 金鑰：

### 格式

```plain
https://raw.githubusercontent.com/InfernoPC/typhoon_vacation/main/output/{縣市名稱}.json
```

### 範例

- **澎湖縣**：

```plain
https://raw.githubusercontent.com/InfernoPC/typhoon_vacation/main/output/澎湖縣.json
```

- **花蓮縣**：

```plain
https://raw.githubusercontent.com/InfernoPC/typhoon_vacation/main/output/花蓮縣.json
```

### 使用方式

**JavaScript / Fetch API：**

```javascript
fetch('https://raw.githubusercontent.com/InfernoPC/typhoon_vacation/main/output/澎湖縣.json')
  .then(response => response.json())
  .then(data => console.log(data));
```

**Python：**

```python
import requests
import json

url = 'https://raw.githubusercontent.com/InfernoPC/typhoon_vacation/main/output/澎湖縣.json'
response = requests.get(url)
data = response.json()
print(data)
```

**curl：**

```bash
curl https://raw.githubusercontent.com/InfernoPC/typhoon_vacation/main/output/澎湖縣.json
```

### 注意事項

- 檔案會每小時自動更新（UTC 時間整點）
- 若縣市目前無資料，`status` 欄位為空字串 `""`
- 所有 URL 中的中文字元會自動進行 URL 編碼
