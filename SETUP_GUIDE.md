# v3 安裝與使用教學（Windows + GitHub Pages）

## 第一部分：更新你已建立的 GitHub 網站

把 `social-impact-suite-v3` ZIP 解壓縮後，將**裡面的內容**上傳到你原本的 Repository 根目錄。

Repository 首頁應直接看到：

- `index.html`
- `assets/`
- `data/`
- `helper/`
- `.github/`
- `README.md`
- `SETUP_GUIDE.md`

### 舊 API 檔案如果還存在，刪除

- `.github/workflows/collect-social.yml`
- `scripts/collect.py`
- `scripts/import_csv.py`
- `requirements.txt`（根目錄舊版）
- `config/accounts.json`
- `config/accounts.example.json`
- 舊的 `data/analytics.json`

保留 `.github/workflows/deploy-pages.yml`。

GitHub `Settings → Secrets and variables → Actions` 裡舊的 `FB_TOKEN_1`、`IG_TOKEN_1`、`THREADS_TOKEN_1` 都可以刪除。v3 不使用 Meta API Token。

---

# 第二部分：安裝 Windows 社群資料小助手

## 1. 準備 Python

電腦需要 Python 3.11 以上。若尚未安裝，從 Python 官方 Windows 安裝程式安裝，安裝時勾選：

`Add Python to PATH`

## 2. 執行安裝

打開專案的：

`helper\install.bat`

它會自動：

1. 建立獨立 Python 環境；
2. 安裝 Playwright 與 Excel 讀取套件；
3. 安裝小助手專用 Chromium。

完成後，之後只要雙擊：

`helper\開啟小助手.bat`

---

# 第三部分：第一次登入 FB／IG／Threads

小助手不要求你輸入帳密到設定檔。你會在專用瀏覽器中自己正常登入。

## Facebook

1. 小助手 → `① 首次設定`。
2. Facebook 那列按 `開啟設定瀏覽器`。
3. 在跳出的 Chromium 正常登入 Facebook。
4. 進 Meta Business Suite 的 Facebook Insights／洞察報告。
5. 日期篩選若有「本月」等相對期間，優先用相對期間。
6. 回小助手按 `記住目前網址`。

已預填高雄市政府運動發展局 Page ID `255034405020824` 的 Business Suite URL，但仍以你實際登入後的頁面為準。

## Instagram

1. Instagram 那列按 `開啟設定瀏覽器`。
2. 如果已經由 Meta Business Suite 登入，不一定需要重新登入。
3. 切換到 Instagram 帳號的 Insights。
4. 回小助手按 `記住目前網址`。

## Threads

1. Threads 那列按 `開啟設定瀏覽器`。
2. 正常登入 Threads。
3. 開啟 Threads Insights。
4. 回小助手按 `記住目前網址`。

> 三平台共用「小助手自己的瀏覽器資料夾」。Cookie／Local Storage 只留在 `%LOCALAPPDATA%\SocialImpactCollector\browser-profile`。不要把這個資料夾給別人。

---

# 第四部分：測試每天自動擷取

先把所有「設定瀏覽器」視窗關掉，再到：

`③ 執行與狀態 → 以可見瀏覽器測試`

每個平台應出現類似：

- Facebook：`擷取 4 個指標`
- Instagram：`擷取 5 個指標`
- Threads：`擷取 3 個指標`

小助手會在本機留下：

`%LOCALAPPDATA%\SocialImpactCollector\raw\YYYY-MM-DD\`

其中有平台文字快照、當時頁面 URL 與截圖。這些檔案**不會同步到 GitHub**。

如果顯示「登入狀態失效」，重新用 `開啟設定瀏覽器` 登入即可。

如果顯示「未辨識到指標」，通常代表記住的網址不是 Insights 主畫面，或 Meta 改版；重新定位後再測。

---

# 第五部分：安裝每天固定時間排程

小助手 → `① 首次設定`：

1. `每日執行時間` 填，例如 `18:00`。
2. 按 `儲存設定`。
3. 按 `安裝每日排程`。

另外，在「本單位私訊名稱」填入官方帳號在匯出訊息裡可能出現的名稱，用逗號分隔，例如：`高雄市政府運動發展局, kaohsiung_sports`。這是為了讓私訊分析排除小編自己的回覆。

Windows 工作排程器會建立：

`Social Impact Collector`

之後每天固定執行。

注意：電腦如果關機或睡眠，當次無法正常擷取；Session 過期或遇到 2FA 也會需要重新登入。

---

# 第六部分：讓 GitHub 網站也自動更新

最簡單的方法是使用 GitHub Desktop。

## 1. Clone Repository

GitHub Desktop 登入你的 GitHub 帳號後，把目前 Dashboard Repository Clone 到電腦，例如：

`C:\Users\你的帳號\Documents\GitHub\social-impact-dashboard`

## 2. 告訴小助手 Repository 在哪

小助手 → `① 首次設定`：

- `本機 Repository` → `選擇資料夾`
- 選剛剛 Clone 下來的資料夾
- 勾選 `每日擷取成功後自動 commit / push 到 GitHub`
- `儲存設定`

第一次可先到 `③ 執行與狀態 → 立即同步 GitHub` 測試。

小助手只會自動更新：

`data/collector-data.json`

GitHub Pages 的部署 workflow 會再自動更新網站。

---

# 第七部分：每月底匯入官方完整內容資料

每日擷取是「趨勢保險」。正式月成果建議每月底從 Meta 後台匯出一次 CSV／XLSX。

小助手 → `② 月度匯入／私訊`：

`內容成效 → 選擇 CSV / XLSX 並匯入`

平台可選 `auto`；檔名辨識不出來時手動指定 Facebook、Instagram 或 Threads。

小助手會自動比對常見中英文欄位：

- 發布日期／時間
- 文案／Caption
- URL／Permalink
- 內容類型
- Views
- Reach
- Likes / Reactions
- Comments / Replies
- Shares / Reposts
- Saves
- Clicks

匯入後，Dashboard 會依你建立的活動名稱、日期與關鍵字自動判斷活動；低信心資料仍可在網站手動改掛或排除。

---

# 第八部分：FB／IG／Threads 私訊分析

私訊**不要直接抓原文推到 GitHub**。

每月用 Meta 官方「匯出你的資訊／下載資料」取得 ZIP 或 JSON，再交給小助手：

`② 月度匯入／私訊 → 私訊／後台詢問 → 選擇官方 ZIP / JSON / 資料夾`

小助手會在你的電腦上：

1. 找出訊息；
2. 排除自己帳號的回覆；
3. 自動判斷是哪個活動；
4. 自動分類：報名、名額、資格、時間、交通、費用、規則、裝備、天候、獎項等；
5. 將原文保存在本機 private 資料夾；
6. GitHub 只保存匿名件數。

## 人工修正

匯入後，下方「私訊本機校正」會顯示本機明細。

選一筆後可以：

- 改活動；
- 改問題分類；
- 取消「納入統計」。

按：

`儲存校正並更新匿名統計`

才會重新產生 GitHub 使用的匿名統計。

---

# 你的正常工作流程最後會變成

### 每天

不用做事（電腦開著、登入狀態正常即可）。

Windows 小助手 → 擷取 → `collector-data.json` → GitHub push → Pages 更新。

### 每月底

1. FB／IG／Threads 後台正式資料下載一次；
2. 拖進小助手；
3. 私訊官方 ZIP／JSON 拖進小助手；
4. 看一下低信心活動歸屬與私訊分類；
5. 完成。

這樣年度報告會同時有：

- 平台每月趨勢；
- 貼文／Reels／限動／Threads 成效；
- 單一活動宣傳成果；
- 自動判別＋人工校正；
- 私訊量與客服量；
- 民眾最常詢問的問題；
- 可作為下一年度宣傳改善與經費爭取依據的年度摘要。
