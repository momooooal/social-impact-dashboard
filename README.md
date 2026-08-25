# 社群效益戰情室 v2｜免 API 版

這是一個可部署在 GitHub Pages 的 Facebook／Instagram／Threads 社群效益整理網站。此版本**不使用 Meta API、不需要 Access Token、不會自動登入社群帳號**；改採每月人工輸入＋CSV匯入，網站在瀏覽器中自動完成彙整、活動分類、民眾詢問分析與年度成果摘要。

## 這版解決什麼

- 「＋新增本月社群數據」：一次填 FB／IG／Threads 當月後台數字。
- 互動不只貼文：可記錄限時動態互動、連結點擊、私訊諮詢對話、訊息則數。
- 單一活動宣傳分析：建立活動名稱、宣傳期間與關鍵字，系統自動判斷哪些貼文／限動／Threads／詢問屬於該活動。
- 人工校正優先：每筆資料都可改活動、勾選納入／排除；系統不會把猜測當成不可修改的真相。
- 民眾詢問分析：自動分為報名、名額候補、資格、時間、地點交通、費用、流程規則、裝備、天候、獎項等，並產生改善提示。
- 年度成果：彙整社群量體、內容互動、私訊諮詢、追蹤成長、活動效益與民眾詢問熱點。
- 完全靜態：只需要 GitHub Pages，沒有伺服器費用。

## 重要：資料存在哪裡？

GitHub Pages 是靜態網站，瀏覽器不能直接把表單資料寫回 GitHub Repository。

因此本版採兩層保存：

1. **平常輸入：瀏覽器 localStorage 自動保存。** 在同一個 GitHub Pages 網址、同一瀏覽器開啟時，資料會留著。
2. **正式備份：資料管理 →「下載網站資料檔」**，會下載 `manual-data.json`。把它覆蓋 Repository 的 `data/manual-data.json` 後，資料就會成為 GitHub 上的正式版本，也能換電腦使用。

建議每次完成月報或大量匯入後就備份一次。

## 建議每月流程

1. 到 Meta Business Suite／Instagram／Threads 後台整理當月數字。
2. 網站按「＋新增本月社群數據」，填三平台資料。
3. 有需要做活動分析時，先建立活動，再匯入／新增宣傳內容。
4. 將後台私訊或留言**去除姓名、電話、Email 等個資後**貼到「民眾詢問分析」。
5. 檢查系統活動判定，將誤判內容改掛活動或取消「納入」。
6. 到「資料管理」下載 `manual-data.json`，更新到 GitHub。

## 互動的計算方式

### 內容互動

`讚／反應 + 留言／回覆 + 分享／轉發 + 收藏 + 限動互動 + 連結點擊 + 其他內容互動`

### 服務互動

以「私訊／諮詢**對話數**」作為服務互動，不直接拿訊息總則數灌高互動。例如同一位民眾連續傳 10 則訊息，仍可記為 1 組諮詢對話、10 則訊息。

### 訊息則數

另外保存，用來呈現客服／資訊回應量能，不與諮詢人次混為一談。

## CSV

網站內可直接下載兩種範本：

- 宣傳內容 CSV
- 民眾詢問 CSV

若 Meta 匯出的是 Excel，可先在 Excel 另存為 UTF-8 CSV 再匯入。

## 檔案結構

```text
.
├─ index.html
├─ assets/
│  ├─ app.js
│  └─ style.css
├─ data/
│  └─ manual-data.json
├─ templates/
│  ├─ content-template.csv
│  └─ inquiry-template.csv
└─ .github/workflows/
   └─ deploy-pages.yml
```

本版已不需要 `collect.py`、Meta Token、`accounts.json` 或每日 API workflow。
