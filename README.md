# 社群效益戰情室 v3 + Windows 社群資料小助手

這套專案用於彙整 Facebook、Instagram、Threads 社群成效，並將平台成果、單一活動宣傳效益與民眾詢問熱點整理成年度成果證據。

## v3 的核心架構

- **GitHub Pages Dashboard**：公開呈現匿名、彙整後的社群成果。
- **Windows 本機小助手**：用你本人已登入的專用瀏覽器工作階段擷取 Insights，不把 FB／IG／Threads 帳密寫進程式或 GitHub。
- **每日彙總快照**：追蹤者、觀看／瀏覽、觸及、內容互動、造訪、訊息彙總等能辨識到的卡片數字。
- **每月官方匯出檔**：CSV／XLSX 自動整理貼文、Reels、限動、Threads 內容成效。
- **活動自動判別＋人工校正**：依活動名稱、關鍵字、日期判斷內容歸屬，低信心資料可在 Dashboard 取消納入或改掛活動。
- **私訊匿名分析**：官方 ZIP／JSON 只在本機讀取；GitHub 只保存「月份 × 平台 × 活動 × 問題分類 × 件數」。
- **GitHub 自動同步（選用）**：搭配 GitHub Desktop 的既有登入狀態，自動 commit / push `data/collector-data.json`。

## 資料檔

- `data/manual-data.json`：活動設定、人工輸入與人工校正資料。
- `data/collector-data.json`：Windows 小助手產生的匿名自動資料。
- Dashboard 開啟時會合併兩份資料。

## 最短使用方式

1. 把本專案內容更新到 GitHub Repository。
2. Windows 電腦進 `helper`，雙擊 `install.bat`。
3. 雙擊 `開啟小助手.bat`。
4. 在「首次設定」分別開 Facebook、Instagram、Threads 專用瀏覽器並正常登入。
5. 每個平台切到要蒐集的 Insights 頁，按「記住目前網址」。
6. 用「以可見瀏覽器測試」確認能抓到資料。
7. 設定每日時間 → 「安裝每日排程」。
8. 若要網站自動更新：用 GitHub Desktop Clone Repository，讓小助手選該本機資料夾並開啟自動 Git 同步。
9. 每月底再把 Meta 官方 CSV／XLSX、訊息 ZIP／JSON 匯入一次，作為完整正式月資料。

完整步驟請看 `SETUP_GUIDE.md` 與 `helper/README_HELPER.md`。

## 安全與隱私

- 不要求把社群帳號密碼提供給程式作者或寫入 GitHub。
- 瀏覽器登入工作階段保存在 `%LOCALAPPDATA%\SocialImpactCollector\browser-profile`，請勿上傳或分享。
- 私訊原文與姓名只保存在 `%LOCALAPPDATA%\SocialImpactCollector\private`。
- 公開 GitHub 僅保存匿名彙總統計。

## 重要限制

這不是 Meta 官方 API。它以你本人有權限看到的後台頁面做本機自動化，因此 Meta 改版、登入驗證、2FA、Session 過期、電腦關機／睡眠等都可能造成某次自動擷取失敗。程式會留下本機文字快照與截圖供排錯，並在 Dashboard 顯示最後一次蒐集狀態。

正式年度成果仍建議以「每月官方匯出檔」校正；每日擷取主要用於避免歷史趨勢斷掉與減少人工工作。
