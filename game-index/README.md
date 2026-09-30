# 教學遊戲目錄

給老師和學生用平板打開的目錄頁。頁面只放遊戲連結，不收集資料，也不用 localStorage。

## 檔案位置

- 目錄頁：[`game-index/index.html`](./index.html)
- CSS 和 JavaScript 都寫在這個檔案裡面，不用外網 CDN、外部字體或圖片。

本機預覽（在倉庫根目錄執行）：

```bash
python3 -m http.server 8765
```

然後打開 `http://127.0.0.1:8765/game-index/`。

## 怎樣加遊戲

打開 `index.html`，改 `<script>` 最上面的 `GAMES` 陣列，加一項即可。不用改其他程式。

```javascript
{
  title: "遊戲名稱",
  grade: 5,
  lessonNo: 3,
  lessonTitle: "空氣的特性",
  intro: "一句簡介。",
  url: "https://example.github.io/your-game/",
  icon: "🌬️"
}
```

- `grade` 用數字，頁面會顯示成「五年級」。
- `lessonNo` 用數字。1–20 會顯示成「第一課」至「第二十課」。
- 頁面先按年級、再按課次由小到大排列。
- 同一課有多個遊戲時，次序跟陣列由上至下。
- `url` 請用 `http` 或 `https`。

## 放到 Google Sites

合併到 `main` 後，`.github/workflows/deploy-github-pages.yml` 會把 `game-index/index.html` 複製到 GitHub Pages。

公開網址：

```text
https://howardyu1995.github.io/grok-bot/game-index/
```

若 Actions 顯示 Pages 未啟用，請有倉庫管理權限的人做一次：**Settings → Pages → Build and deployment → Source** 選 **GitHub Actions**，再到 **Actions** 重新跑 **Deploy GitHub Pages**。

嵌入步驟：

1. 先用瀏覽器打開上面的網址，確認目錄和「開始玩」都正常。
2. 編輯 Google Sites → 右側 **插入 → 嵌入**。
3. 選 **網址**，貼上目錄網址。
4. 嵌入框拉闊，高度建議約 **900–1400 px**，讓卡片同「開始玩」掣都睇到。
5. **發布**網站。學生撳卡片會在新分頁打開遊戲。

若要用嵌入程式碼：

```html
<iframe
  src="https://howardyu1995.github.io/grok-bot/game-index/"
  style="width:100%;height:1200px;border:0;"
  title="教學遊戲目錄">
</iframe>
```
