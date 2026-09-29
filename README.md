# grok-bot

本倉庫包含可在瀏覽器開啟的互動網頁（HTML）。

## 網頁一覽

| 網頁 | 檔案 | 說明 |
|------|------|------|
| 氣壓原理互動模型 | [`air-pressure-drink-box.html`](./air-pressure-drink-box.html) | 香港小五常識：飲品盒為何會凹陷（p5.js） |
| 風的形成（海風原理） | [`sea-breeze-wind.html`](./sea-breeze-wind.html) | 日間海風成因：Canvas 對流動畫＋課本填空小遊戲 |
| 五位數密碼鎖 | [`index.html`](./index.html) | 解密挑戰小遊戲 |

---

## 用 GitHub Pages 公開網頁（給 Google Sites 嵌入）

Google Sites **不能直接執行** 含 JavaScript 的 HTML，請先用 GitHub Pages 公開，再嵌入網址。

### 一、第一次啟用 Pages（只需做一次）

1. 把本 PR **合併進 `main`**（或確保 `main` 已有 `air-pressure-drink-box.html` 與 `.github/workflows/deploy-github-pages.yml`）。
2. 打開倉庫：**Settings → Pages**。
3. **Build and deployment → Source** 選 **GitHub Actions**（不要選 “Deploy from a branch”）。
4. 到 **Actions** 分頁，確認工作流程 **Deploy GitHub Pages** 已成功（綠勾）。  
   - 若沒有自動跑，可點該 workflow → **Run workflow**（選 `main`）手動執行。

### 二、公開網址（合併並部署成功後）

氣壓模型：

```text
https://howardyu1995.github.io/grok-bot/air-pressure-drink-box.html
```

風的形成（海風原理）：

```text
https://howardyu1995.github.io/grok-bot/sea-breeze-wind.html
```

倉庫首頁（密碼鎖遊戲）：

```text
https://howardyu1995.github.io/grok-bot/
```

請先用瀏覽器打開確認可以操作，再去 Google Sites 嵌入。

### 三、放到 Google Sites

1. 編輯 Google Sites → 右側 **插入 → 嵌入**。
2. 選 **網址**，貼上氣壓模型網址（上一節）。
3. 嵌入框建議調大：寬度拉滿、高度約 **900～1100 px**（讓按鈕與滑桿都看得到）。
4. **發布**網站。

#### 進階：用 iframe 程式碼嵌入（可選）

若「嵌入 → 嵌入程式碼」可用，可貼：

```html
<iframe
  src="https://howardyu1995.github.io/grok-bot/air-pressure-drink-box.html"
  style="width:100%;height:1000px;border:0;"
  loading="lazy"
  allowfullscreen
  title="氣壓原理互動模型">
</iframe>
```

海風原理頁亦可同樣嵌入：

```html
<iframe
  src="https://howardyu1995.github.io/grok-bot/sea-breeze-wind.html"
  style="width:100%;height:1100px;border:0;"
  loading="lazy"
  allowfullscreen
  title="風的形成｜海風原理互動教學">
</iframe>
```

### 四、課堂注意

- 學校網路需能連到 `*.github.io` 與 `cdn.jsdelivr.net`（載入 p5.js）。
- 若校網擋 CDN，需改為下載 `p5.min.js` 到同資料夾並改成本地路徑後再部署。

---

## 本機預覽

```bash
# 在倉庫根目錄
python3 -m http.server 8765
# 瀏覽器開啟 http://127.0.0.1:8765/air-pressure-drink-box.html
# 或 http://127.0.0.1:8765/sea-breeze-wind.html
```
