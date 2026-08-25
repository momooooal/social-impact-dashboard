# 社群效益戰情室 Social Impact Dashboard

把 Facebook、Instagram、Threads 的後台效益集中成一個可部署到 GitHub Pages 的年度社群成果網站。

這不是只有「漂亮圖表」的 dashboard。它的核心目標是：**從現在開始累積歷史資料，讓明年爭取社群宣傳／委外／廣告／素材製作經費時，有完整的量化證據。**

## 已做好的功能

- Facebook / Instagram / Threads 多帳號彙整
- GitHub Actions 每日自動抓取 Meta API，不把 Access Token 放在前端
- `data/analytics.json` 持續累積歷史快照
- 觀看／曝光、互動、互動率、淨追蹤成長、內容產出 KPI
- 近 30 天／90 天／今年至今／年度／自訂日期
- 與「前一等長期間」自動比較
- 各平台效益占比與趨勢
- 每月成果表
- 高效貼文 Top 10 / 20 / 50
- 內容類型績效、發文時段熱區
- 年度 KPI 目標達成率
- 自動產生「經費成果報告摘要」文字
- 平台別年度效益證據表
- CSV、JSON 匯出與瀏覽器列印／另存 PDF
- API 警告與資料蒐集紀錄
- API 尚未完成前，可用 CSV 手動匯入當備援
- 手機／桌機 RWD

## 架構

```text
Meta API
   │
   │ Access Token 只存在 GitHub Secrets
   ▼
GitHub Actions（每日 01:20 台灣時間）
   │
   ├─ scripts/collect.py
   │    ├─ Facebook Page Insights
   │    ├─ Instagram Professional Account Insights
   │    └─ Threads Insights
   │
   ▼
data/analytics.json  ← 每天累積，不覆蓋掉以前歷史
   │
   ▼
GitHub Pages
   └─ index.html + assets/app.js + assets/style.css
```

## 5 分鐘先把示範網站架起來

1. 在 GitHub 建立一個 Repository。
2. 把本專案全部檔案上傳到 Repository 根目錄。
3. GitHub Repository → **Settings → Pages**。
4. Build and deployment 的 Source 選 **GitHub Actions**。
5. 到 Actions 執行 `Deploy dashboard to GitHub Pages`，或 push 一次 main。
6. GitHub Pages 網址就會顯示示範版 dashboard。

> 一開始 `data/analytics.json` 是示範資料。Meta Token 還沒設好也可以先確認網站長相。

## 接上真實帳號

請看 [`SETUP_GUIDE.md`](SETUP_GUIDE.md)。

最重要的是三件事：

1. 修改 `config/accounts.json`：填 Page / IG / Threads ID。
2. GitHub → Settings → Secrets and variables → Actions：新增 Access Token。
3. Actions 手動執行 `Collect social insights`。

成功後，`data/analytics.json` 會從示範資料改成真實資料；往後每天自動更新。

## 多帳號

`config/accounts.json` 可以同時放多個帳號，例如：

```json
{
  "key": "ig-campaign",
  "platform": "instagram",
  "id": "1784XXXXXXXXXXX",
  "label": "活動專用 IG",
  "token_env": "IG_TOKEN_2",
  "enabled": true
}
```

工作流程已預留：

- `FB_TOKEN_1` ～ `FB_TOKEN_5`
- `IG_TOKEN_1` ～ `IG_TOKEN_5`
- `THREADS_TOKEN_1` ～ `THREADS_TOKEN_5`

若超過 5 個，只要照相同方式在 `.github/workflows/collect-social.yml` 增加環境變數即可。

## 年度 KPI

`config/accounts.json`：

```json
"goals": {
  "views": 1800000,
  "interactions": 130000,
  "followers_growth": 4500,
  "posts": 300
}
```

這些數字會自動出現在「經費成果報告 → 年度 KPI 達成率」。

## API 還沒申請好？先用手動 CSV

提供兩個模板：

- `data/manual_daily_template.csv`
- `data/manual_posts_template.csv`

填完後執行：

```bash
python scripts/import_csv.py \
  --daily data/manual_daily_template.csv \
  --posts data/manual_posts_template.csv
```

它會合併進同一份 `data/analytics.json`，所以網站不用改。

## 安全性

### Token

Access Token **不要**寫進：

- `index.html`
- `assets/app.js`
- `config/accounts.json`
- `data/analytics.json`

只放 GitHub Actions Secrets。

### 報表資料本身

GitHub Pages 是靜態網站。若 Repository / Pages 對外公開，`data/analytics.json` 的數字也等同公開資料。

如果你的社群效益數據屬於內部機密，不要用「前端密碼」假裝保護 GitHub Pages；那不是真正的存取控制。請改用有登入權限的內部平台或受保護的主機。

## 指標解讀

不同平台對 views / reach / engagement 的官方定義不完全相同。因此網站採兩層資料：

- **平台原生資料**：保留 API 真正回傳的欄位。
- **跨平台標準化資料**：用 `views`、`interactions`、`followers` 等共同欄位做主管總覽。

正式成果文件建議同時放：

- 全平台合計量體
- Facebook / Instagram / Threads 個別明細
- 指標定義註記

不要把三個平台的 Reach 當成同一種「不重複總人數」相加後宣稱為唯一人數。

## 檔案結構

```text
.
├─ index.html                       # 網站畫面
├─ assets/
│  ├─ app.js                        # dashboard 計算、圖表、報告
│  └─ style.css                     # 視覺與 RWD
├─ config/
│  ├─ accounts.json                 # 真正使用的帳號設定
│  └─ accounts.example.json         # 範例
├─ data/
│  ├─ analytics.json                # 歷史資料倉庫／網站資料源
│  ├─ manual_daily_template.csv     # 手動匯入範例
│  └─ manual_posts_template.csv
├─ scripts/
│  ├─ collect.py                    # Meta API 自動蒐集
│  └─ import_csv.py                 # 手動 CSV 備援
├─ .github/workflows/
│  ├─ deploy-pages.yml              # GitHub Pages 部署
│  └─ collect-social.yml            # 每日抓資料＋部署
├─ requirements.txt
├─ SETUP_GUIDE.md
└─ README.md
```

## 目前 API 版本設定

- Facebook / Instagram：`v26.0`
- Threads：`v1.0`

版本集中在 `config/accounts.json`，未來 Meta 換版時不必大改網站。

## 重要限制

- Instagram Insights 僅適用 Professional Account（Business / Creator），不是一般個人帳號。
- 完整 Insights 需要帳號所有者／管理者授權；不能只靠公開帳號名稱讀到別人的後台數據。
- Meta 會持續調整／淘汰指標。`collect.py` 對多數指標採「失敗就記 warning、其餘繼續」策略。
- 部分帳號層級指標只有有限歷史保留期，因此**越早開始每日保存越好**。
- 貼文 Insights 多為「目前累積值」，網站將它歸因到貼文發布日做內容成效比較，不表示所有互動都發生在發布日當天。

