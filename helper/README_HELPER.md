# 社群資料小助手（Windows 本機版）

這個小助手是 Dashboard v3 的資料蒐集端。它**不保存 Facebook／Instagram／Threads 的帳號密碼**；第一次在小助手的專用 Chromium 登入後，登入 Cookie／Local Storage 只留在本機的：

`%LOCALAPPDATA%\SocialImpactCollector\browser-profile`

請把這個資料夾視為登入憑證，不要壓縮、上傳或分享。

## 第一次安裝

1. 先安裝 Python 3.11 以上（安裝時勾選 `Add Python to PATH`）。
2. 雙擊 `helper\install.bat`。
3. 安裝完成後雙擊 `helper\開啟小助手.bat`。
4. 在「首次設定」依序對 Facebook、Instagram、Threads 按「開啟設定瀏覽器」。
5. 在跳出的**專用瀏覽器**正常登入，進到該平台的 Insights 畫面；日期篩選建議用「本月」或其他會自動隨日期更新的相對期間。
6. 回到小助手按「記住目前網址」。三個平台各做一次。
7. 按「以可見瀏覽器測試」；確認三平台有抓到指標。
8. 設定每天執行時間，按「安裝每日排程」。

## GitHub 自動同步（建議）

最簡單的方法是安裝 GitHub Desktop，登入一次後 Clone 你的 Dashboard Repository。

小助手 → 首次設定 → 「本機 Repository」選擇 Clone 下來的那個資料夾 → 勾選「每日擷取成功後自動 commit / push」。

之後小助手只會更新：

`data/collector-data.json`

不會把瀏覽器登入資料、私訊原文推到 GitHub。

## 每日自動蒐集的資料

小助手會擷取你指定 Insights 頁面「目前可見」的彙總卡片，辨識常見中英文標籤，例如：追蹤者、瀏覽／觀看、觸及、互動、造訪、訊息對話等。原始文字快照與畫面截圖會留在：

`%LOCALAPPDATA%\SocialImpactCollector\raw\YYYY-MM-DD\`

這是為了 Meta 改版時能除錯；不會上傳 GitHub。

**注意：Meta Business Suite 的畫面與指標會改版，且日期篩選狀態會影響擷取值。每月官方 CSV／XLSX 匯出仍建議作為正式成果的權威資料來源。**

## 每月匯入貼文／Reels／限動資料

在小助手的「月度匯入／私訊」選擇 Meta Business Suite 匯出的 CSV 或 XLSX。程式會嘗試自動辨識常見中英文欄位：發布時間、文案、網址、觀看、觸及、讚、留言、分享、收藏、點擊等。

匯入後會依 Dashboard `data/manual-data.json` 中建立的活動名稱、日期與關鍵字自動判斷活動；低信心資料在網站中保留人工校正。

## 私訊／後台詢問

首次設定請在「本單位私訊名稱」填入官方帳號可能出現的名稱／帳號（可用逗號分隔），用來排除小編自己的回覆。


請使用 Meta 官方「匯出你的資訊／下載資料」取得 ZIP 或 JSON，再交給小助手本機分析。

小助手會：

- 嘗試找到 JSON 中的 messages；
- 排除 `config.json` 的 `own_sender_names`（自己的回覆）；
- 分成報名、名額、資格、時間、交通、費用、規則、裝備、天候、獎項等類別；
- 依活動名稱與關鍵字判斷活動；
- **只把「月份 × 平台 × 活動 × 問題類別 × 件數」寫入 Dashboard**。

私訊原文只保存於：

`%LOCALAPPDATA%\SocialImpactCollector\private\`

## 現實限制

這不是 Meta 官方 API，而是使用你本人已登入、有權限看到的後台頁面做本機自動化。因此：

- Meta 改版可能讓某些指標暫時辨識不到；
- 2FA、登入驗證、Session 過期時需要你重新登入；
- 電腦關機或睡眠時，Windows 排程無法正常擷取；
- 不建議用它自動讀取或上傳民眾私訊原文；私訊原文採官方匯出後本機分析。

Dashboard 的年度正式數字建議每月至少用一次官方匯出檔校正。
