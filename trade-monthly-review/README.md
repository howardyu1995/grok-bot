# 月結交易傾向分析（Cursor CLI）

在 Cursor 裡直接跑，不上傳網站。支援：

- **富途牛牛／moomoo**：月結 PDF、成交／交易流水 CSV／XLSX
- **Firstrade**：月結 PDF、Tax Center／帳戶匯出 CSV

**固定規則：每次分析必須合併目前已提供的全部月結與匯出檔，不得只看最新一份。**

資料只在本機解析，不會送到外部服務。

## 每月怎麼用

1. 把新的月結 PDF／CSV 上傳到對話，或放到 [`statements/`](./statements/)（PDF 可放 `statements/raw/`）。
2. 在 Cursor 終端執行**全量合併**分析：

```bash
cd trade-monthly-review
pip3 install -r requirements.txt   # 首次需要（PDF/XLSX）
python3 analyze_all.py
```

3. 報告寫入 `reports/combined_all.md` 與 `reports/combined_all.json`。

單檔／示範資料仍可用：

```bash
python3 analyze.py
```

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
