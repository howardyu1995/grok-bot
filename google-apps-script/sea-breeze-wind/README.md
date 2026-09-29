# 風的形成｜用 Google Apps Script 發佈到 Google Sites

Google 協作平台（Sites）**不能直接貼上含 JavaScript 的 HTML**（腳本會被清掉）。  
正確做法：先用 **Google Apps Script** 發成網頁應用程式，再把網址嵌進 Sites。

本資料夾已準備好兩個檔案（**完全自含，無外部 CDN**）：

| 檔案 | 用途 |
|------|------|
| `Code.gs` | Apps Script 入口（允許 iframe 嵌入） |
| `Index.html` | 完整互動頁面 |

---

## 一、在 Apps Script 建立專案（約 3 分鐘）

1. 用 Google 帳號開啟 [script.google.com](https://script.google.com/)
2. 點 **新增專案**
3. 專案名稱可改成：`風的形成-海風原理`
4. 左側已有 `程式碼.gs`（或 `Code.gs`）：
   - **全選刪除**預設內容
   - 貼上本資料夾 [`Code.gs`](./Code.gs) 的全部內容
5. 左側 **＋** → **HTML** → 檔名輸入：`Index`（不要加 `.html`）
6. 貼上本資料夾 [`Index.html`](./Index.html) 的全部內容
7. **Ctrl／⌘ + S** 儲存

---

## 二、部署成網頁應用程式

1. 上方 **部署** → **新增部署作業**
2. 左側齒輪 → 類型選 **網頁應用程式**
3. 設定建議：
   - **說明**：海風原理互動教學（可填）
   - **執行身分**：我
   - **具有存取權的使用者**：**任何人**（學生才能開）
4. 點 **部署**
5. 第一次會要求授權 → **允許**
6. 複製 **網頁應用程式網址**（形如 `https://script.google.com/macros/s/……/exec`）

之後若改過程式：再按 **部署 → 管理部署作業 → 編輯（筆）→ 版本選「新版本」→ 部署**。

---

## 三、嵌進 Google Sites 發佈

1. 編輯你的 Google 協作平台頁面
2. **插入 → 嵌入 → 網址**
3. 貼上上一步的 `/exec` 網址
4. 嵌入框拉大：寬度盡量滿版、高度約 **1100 px**
5. **發布**網站

### 或用「嵌入程式碼」

```html
<iframe
  src="這裡貼上你的 /exec 網址"
  style="width:100%;height:1100px;border:0;"
  loading="lazy"
  allowfullscreen
  title="風的形成｜海風原理互動教學">
</iframe>
```

---

## 課堂注意

- 學生需能連到 `script.google.com`（多數 Google Workspace 校園帳號可）。
- 本頁**不依賴** Tailwind／外部字型 CDN，校網較不易被擋。
- 若 iframe 空白：確認 `Code.gs` 有 `XFrameOptionsMode.ALLOWALL`，且部署權限為「任何人」。
