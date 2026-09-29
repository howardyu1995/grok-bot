# grok-bot

本倉庫包含可在瀏覽器開啟的互動網頁（HTML）。

## 網頁一覽

| 網頁 | 檔案 | 說明 |
|------|------|------|
| 氣壓原理互動模型 | [`air-pressure-drink-box.html`](./air-pressure-drink-box.html) | 香港小五常識：飲品盒為何會凹陷（p5.js） |
| 風的形成（海風原理） | [`sea-breeze-wind.html`](./sea-breeze-wind.html)／[`google-apps-script/sea-breeze-wind/`](./google-apps-script/sea-breeze-wind/) | 日間海風成因；**可用 Apps Script 直接嵌進 Google Sites** |
| 五位數密碼鎖 | [`index.html`](./index.html) | 解密挑戰小遊戲 |

---

## 風的形成：直接發佈到 Google Sites（建議）

Google Sites **不能直接貼 HTML＋JavaScript**（腳本會被清掉）。  
請用 **Google Apps Script** 發成網頁，再嵌入 Sites——全程在 Google 帳號內完成，不必開 GitHub Pages。

詳細步驟見：[`google-apps-script/sea-breeze-wind/README.md`](./google-apps-script/sea-breeze-wind/README.md)

### 摘要

1. 開啟 [script.google.com](https://script.google.com/) → **新增專案**
2. 貼上 [`Code.gs`](./google-apps-script/sea-breeze-wind/Code.gs)
3. 新增 HTML 檔（檔名 `Index`），貼上 [`Index.html`](./google-apps-script/sea-breeze-wind/Index.html)
4. **部署 → 網頁應用程式** → 存取權選 **任何人** → 複製 `/exec` 網址
5. Google Sites → **插入 → 嵌入 → 網址** → 貼上該網址（高度約 **1100px**）→ **發布**

本頁為**完全自含**（無 Tailwind／字型 CDN），校網較不易被擋。

---

## 其他頁：用 GitHub Pages 公開（給 Google Sites 嵌入）

適用氣壓模型、密碼鎖等靜態 HTML。

### 一、第一次啟用 Pages（只需做一次）

1. 確保 `main` 已有要公開的 HTML 與 [`.github/workflows/deploy-github-pages.yml`](./.github/workflows/deploy-github-pages.yml)。
2. 倉庫：**Settings → Pages** → **Source** 選 **GitHub Actions**。
3. **Actions** 確認 **Deploy GitHub Pages** 成功。

### 二、公開網址（部署成功後）

```text
https://howardyu1995.github.io/grok-bot/air-pressure-drink-box.html
https://howardyu1995.github.io/grok-bot/sea-breeze-wind.html
https://howardyu1995.github.io/grok-bot/
```

### 三、放到 Google Sites

1. **插入 → 嵌入 → 網址**，貼上上列網址之一。
2. 寬度拉滿、高度約 **900～1100 px**。
3. **發布**。

```html
<iframe
  src="https://howardyu1995.github.io/grok-bot/air-pressure-drink-box.html"
  style="width:100%;height:1000px;border:0;"
  loading="lazy"
  allowfullscreen
  title="氣壓原理互動模型">
</iframe>
```

### 四、課堂注意（GitHub Pages）

- 學校網路需能連到 `*.github.io`；氣壓模型另需 `cdn.jsdelivr.net`（p5.js）。

---

## 本機預覽

```bash
# 在倉庫根目錄
python3 -m http.server 8765
# 瀏覽器開啟 http://127.0.0.1:8765/sea-breeze-wind.html
# 或 http://127.0.0.1:8765/air-pressure-drink-box.html
```
