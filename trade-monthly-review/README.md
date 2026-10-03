# 月結交易傾向分析（Cursor CLI）

在 Cursor 裡直接跑，不上傳網站。支援：

- **富途牛牛／moomoo**：成交／交易流水 CSV，或含「交易流水」工作表的 XLSX（含年度帳單）
- **Firstrade**：Tax Center → Download Account Information → Excel CSV

資料只在本機解析，不會送到外部服務。

## 每月怎麼用

1. 從兩家券商匯出該月成交（CSV／XLSX）。
2. 把檔案放到 [`statements/`](./statements/)（檔名建議含 `futu` 或 `firstrade` 方便辨識）。
3. 在 Cursor 終端執行：

```bash
cd trade-monthly-review
pip3 install -r requirements.txt   # 首次需要（讀 XLSX）
python3 analyze.py
```

4. 終端會印出完整報告，並寫入 `reports/YYYY-MM.md`。

### 常用參數

```bash
# 指定月份
python3 analyze.py --month 2026-01

# 指定檔案
python3 analyze.py statements/futu-2026-01.csv statements/firstrade-2026-01.csv

# 只看終端、不寫檔
python3 analyze.py --stdout-only
```

若 `statements/` 是空的，會自動改用 [`samples/`](./samples/) 示範資料，方便先試跑。

## 匯出路徑提示

### Firstrade

Accounts → Tax Center → Download Account Information → Excel CSV Files → 選帳戶與日期區間。

預期欄位包含：`Symbol, Quantity, Price, Action, TradeDate, Commission, Fee, RecordType` 等。

### 富途牛牛

- 桌面版／APP 匯出**歷史成交／交易流水** CSV；或
- 年度帳單 XLSX（內含「交易流水」表）後，用 `--month YYYY-MM` 只看單月。

常見欄位：成交時間、代碼名稱、方向、數量、價格、幣種、成交金額、總費用。

## 報告會看什麼

- 成交頻率、買／賣偏向、標的集中度
- FIFO 已實現回合：勝率、盈虧比、持倉天數、日內短打比例
- 費用拖累、星期分布、券商拆分
- 依數據產生的**策略優化建議**（頻率、出場、集中度、報復性交易等）

## 注意

- 多幣種成交額**不會自動換匯**，解讀時請分開看 USD／HKD。
- 跨月才賣出的部位，已實現盈虧可能落在賣出月份。
- 本工具是行為复盤，不是投資建議。
