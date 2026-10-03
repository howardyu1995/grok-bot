#!/usr/bin/env python3
"""合併全部月結（富途 PDF + Firstrade PDF + CSV）後產出覆盤指標。"""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UPLOADS = Path("/home/ubuntu/.cursor/projects/workspace/uploads")
EXTRACT = Path("/tmp/statements_extract")
OUT = ROOT / "reports"
USD_HKD = 7.84


@dataclass
class Trade:
    broker: str
    date: str
    side: str
    symbol: str
    qty: float
    price: float
    amount: float
    fees: float = 0.0
    currency: str = "USD"
    source: str = ""
    is_option: bool = False
    is_warrant: bool = False
    dedupe_key: str = ""


@dataclass
class NavPoint:
    broker: str
    month: str
    open_native: float
    close_native: float
    currency: str
    net_external_native: float = 0.0


def parse_num(value) -> float:
    if value is None or value == "":
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    raw = str(value).strip().replace(",", "").replace("$", "")
    neg = raw.startswith("(") and raw.endswith(")")
    raw = raw.strip("()")
    try:
        n = float(raw)
    except ValueError:
        return 0.0
    return -abs(n) if neg else n


def to_hkd(amount: float, currency: str) -> float:
    c = (currency or "HKD").upper()
    if c == "USD":
        return amount * USD_HKD
    return amount


def ensure_extracts() -> None:
    EXTRACT.mkdir(parents=True, exist_ok=True)
    try:
        import pdfplumber
    except ImportError:
        return
    pdfs = list(UPLOADS.glob("*.pdf")) + list((ROOT / "statements" / "raw").glob("*.pdf"))
    for pdf in pdfs:
        out = EXTRACT / f"{pdf.stem}.txt"
        if out.exists() and out.stat().st_mtime >= pdf.stat().st_mtime:
            continue
        parts = []
        with pdfplumber.open(pdf) as doc:
            for i, page in enumerate(doc.pages, 1):
                parts.append(f"\n===== PAGE {i}/{len(doc.pages)} =====\n{page.extract_text() or ''}")
        out.write_text("\n".join(parts), encoding="utf-8")


# ----- Futu PDF text -----
SIDE_MAP = {
    "買入開倉": "buy",
    "買入平倉": "buy",
    "賣出開倉": "sell",
    "賣出平倉": "sell",
}


def parse_futu_text(path: Path) -> tuple[list[Trade], list[NavPoint], list[dict]]:
    text = path.read_text(encoding="utf-8")
    m = re.search(r"證券月結單\n(20\d{2}/\d{2})", text)
    month = m.group(1).replace("/", "-") if m else "unknown"
    nav_m = re.search(r"資產淨值\s+([\d,\.]+)\s+([\d,\.]+)\s+([+\-]?[\d,\.]+)", text)
    open_nav = parse_num(nav_m.group(1)) if nav_m else 0.0
    close_nav = parse_num(nav_m.group(2)) if nav_m else 0.0
    externals = []
    for fm in re.finditer(
        r"(20\d{2}/\d{2}/\d{2})\s+(增加|減少)\s+(出入金|資金調撥)\s+(HKD|USD)\s+([+\-]?[\d,\.]+)",
        text,
    ):
        externals.append(
            {
                "date": fm.group(1).replace("/", "-"),
                "kind": fm.group(3),
                "currency": fm.group(4),
                "amount": parse_num(fm.group(5)),
            }
        )
    net_ext = sum(e["amount"] for e in externals if e["currency"] == "HKD")
    net_ext += sum(to_hkd(e["amount"], "USD") for e in externals if e["currency"] == "USD")

    trades: list[Trade] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        side_key = next((k for k in SIDE_MAP if line.startswith(k)), None)
        if not side_key:
            i += 1
            continue
        side = SIDE_MAP[side_key]
        header = line
        block = [header]
        j = i + 1
        fees = 0.0
        symbol = ""
        date = ""
        qty = 0.0
        price = 0.0
        amount = 0.0
        currency = "HKD"
        while j < len(lines) and j <= i + 8:
            nxt = lines[j].strip()
            if any(nxt.startswith(k) for k in SIDE_MAP) and j > i + 1:
                break
            block.append(nxt)
            fee_m = re.search(r"小計:\s*([\d,\.]+)", nxt)
            if fee_m:
                fees = parse_num(fee_m.group(1))
            hm = re.match(
                rf"{side_key}\s+(HKD|USD|CNH|CNY)\s+([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)\s+([+\-]?[\d,\.]+)",
                header,
            )
            if hm:
                currency = hm.group(1)
                qty = abs(parse_num(hm.group(2)))
                price = abs(parse_num(hm.group(3)))
                amount = abs(parse_num(hm.group(4)))
            nm = re.search(
                r"(20\d{2}/\d{2}/\d{2})\s+(20\d{2}/\d{2}/\d{2})\s+([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)\s+([+\-]?[\d,\.]+)",
                nxt,
            )
            if nm:
                if not date:
                    date = nm.group(1).replace("/", "-")
                qty = abs(parse_num(nm.group(3)))
                price = abs(parse_num(nm.group(4)))
                amount = abs(parse_num(nm.group(5)))
            sm = re.search(r"([A-Z0-9\.\-]{2,30})\(", nxt)
            if sm and not symbol:
                symbol = sm.group(1)
            cm = re.search(r"\s(HKD|USD)\s+(20\d{2}/\d{2}/\d{2})", nxt)
            if cm:
                currency = cm.group(1)
                if not date:
                    date = cm.group(2).replace("/", "-")
            j += 1
            if fee_m:
                break
        if not symbol:
            for b in block[1:4]:
                sm = re.search(r"([A-Z0-9\.\-]{2,30})\(", b)
                if sm:
                    symbol = sm.group(1)
                    break
        if not date:
            for b in block:
                dm = re.search(r"(20\d{2}/\d{2}/\d{2})", b)
                if dm:
                    date = dm.group(1).replace("/", "-")
                    break
        if symbol and date and qty > 0:
            is_opt = bool(re.search(r"\d{6}[CP]\d", symbol))
            is_warr = bool(re.match(r"^[5-6]\d{4}$", symbol))
            key = f"futu|{date}|{side}|{symbol}|{qty:.6f}|{price:.6f}|{amount:.2f}"
            trades.append(
                Trade(
                    broker="futu",
                    date=date,
                    side=side,
                    symbol=symbol,
                    qty=qty,
                    price=price,
                    amount=amount,
                    fees=fees,
                    currency=currency,
                    source=path.name,
                    is_option=is_opt,
                    is_warrant=is_warr,
                    dedupe_key=key,
                )
            )
        i = j if j > i else i + 1

    nav = NavPoint("futu", month, open_nav, close_nav, "HKD", net_ext)
    return trades, [nav], externals


# ----- Firstrade PDF text -----
SYM_MAP = [
    ("AEROVIRONMENT", "AVAV"),
    ("ROCKET LAB", "RKLB"),
    ("EA SER TR ALPHA ARCHITECT 1 3 MONTH", "BOXX"),
    ("EA SER TR", "BOXX"),
    ("AMAZON", "AMZN"),
    ("CROWDSTRIKE", "CRWD"),
    ("COINBASE", "COIN"),
    ("JOBY AVIATION", "JOBY"),
    ("VANGUARD S&P 500", "VOO"),
    ("MICROSOFT", "MSFT"),
    ("NVIDIA", "NVDA"),
    ("MP MATERIALS", "MP"),
    ("IONQ", "IONQ"),
    ("RIGETTI", "RGTI"),
    ("PALANTIR", "PLTR"),
    ("ALPHABET INC CLASS C", "GOOG"),
    ("ALPHABET", "GOOGL"),
    ("SHP ETF TR", "SHP"),
    ("BERKSHIRE HATHAWAY", "BRK.B"),
    ("INVESCO EXCHANGE TRADED FD TR", "QQQM"),
    ("TIDAL TR II", "YMAG"),
    ("MARVELL", "MRVL"),
    ("PALO ALTO", "PANW"),
    ("CREDO TECHNOLOGY", "CRDO"),
    ("OKLO INC", "OKLO"),
    ("ECHOSTAR", "SATS"),
    ("TAIWAN SEMICONDUCTOR", "TSM"),
    ("FUTU HOLDINGS", "FUTU"),
    ("INTEL CORP", "INTC"),
    ("INTERNATIONAL BUSINESS", "IBM"),
    ("AMERICAN CENTURY", "AVUV"),
    ("ISHARES TR ISHARES MSCI USA MOMENTUM", "MTUM"),
    ("ISHARES TR", "IWM"),
    ("BLOOM ENERGY", "BE"),
    ("TEMA ETF", "TEMA"),
    ("SPACE EXPLORATION", "SPACEX"),
]


def norm_symbol(desc: str, fallback: str = "") -> str:
    if fallback and re.fullmatch(r"[A-Z][A-Z0-9\.\-]{0,9}", fallback.strip().upper()):
        return fallback.strip().upper()
    u = desc.upper()
    for key, sym in SYM_MAP:
        if key in u:
            return sym
    words = re.findall(r"[A-Za-z\.]+", desc)
    return " ".join(words[:3]).upper() if words else (fallback or "UNKNOWN")


def parse_firstrade_text(path: Path) -> tuple[list[Trade], list[NavPoint]]:
    text = path.read_text(encoding="utf-8")
    if "Total Equity Holdings" not in text and "BUY / SELL" not in text and "BOUGHT " not in text:
        return [], []
    m = re.search(
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+1,\s+(20\d{2})\s+-\s+\1\s+\d{1,2},\s+\2",
        text,
    )
    mmap = {
        n: f"{i:02d}"
        for i, n in enumerate(
            [
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            ],
            1,
        )
    }
    month = f"{m.group(2)}-{mmap[m.group(1)]}" if m else "unknown"
    eq = re.search(r"Total Equity Holdings\s+\$?([\d,\.]+)\s+\$?([\d,\.]+)", text)
    open_usd = parse_num(eq.group(1)) if eq else 0.0
    close_usd = parse_num(eq.group(2)) if eq else 0.0
    trades: list[Trade] = []
    for m2 in re.finditer(
        r"(BOUGHT|SOLD)\s+(\d{2}/\d{2}/\d{2})(?:\s+\d{2}/\d{2}/\d{2})?\s+[CM]\s+(.+?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+\$?([\d,]+\.\d{2})",
        text,
    ):
        side = "buy" if m2.group(1) == "BOUGHT" else "sell"
        md, dd, yy = m2.group(2).split("/")
        date = f"20{yy}-{md}-{dd}"
        desc = m2.group(3).strip()
        is_opt = desc.upper().startswith("CALL ") or desc.upper().startswith("PUT ")
        qty = abs(parse_num(m2.group(4)))
        price = abs(parse_num(m2.group(5)))
        amount = abs(parse_num(m2.group(6)))
        symbol = norm_symbol(desc)
        if is_opt:
            om = re.search(
                r"(CALL|PUT)\s+([A-Z]+)\s+(\d{2}/\d{2}/\d{2})\s+(\d+(?:\.\d+)?)\s+(\d+)\s+(\d+(?:\.\d+)?)\s+\$?([\d,]+\.\d{2})",
                m2.group(0),
            )
            if om:
                symbol = f"{om.group(1)}_{om.group(2)}_{om.group(3)}_{om.group(4)}"
                qty = abs(parse_num(om.group(5)))
                price = abs(parse_num(om.group(6)))
                amount = abs(parse_num(om.group(7)))
        key = f"ft|{date}|{side}|{symbol}|{qty:.6f}|{price:.6f}|{amount:.2f}"
        trades.append(
            Trade(
                broker="firstrade",
                date=date,
                side=side,
                symbol=symbol,
                qty=qty,
                price=price,
                amount=amount,
                currency="USD",
                source=path.name,
                is_option=is_opt,
                dedupe_key=key,
            )
        )
    nav = NavPoint("firstrade", month, open_usd, close_usd, "USD", 0.0)
    return trades, [nav]


# ----- Firstrade CSV export -----
def parse_firstrade_csv(path: Path) -> list[Trade]:
    text = path.read_text(encoding="utf-8-sig")
    rows = list(csv.DictReader(text.splitlines()))
    trades: list[Trade] = []
    for row in rows:
        kind = (row.get("交易類別") or "").strip()
        if kind not in {"買進", "賣出"}:
            continue
        date = (row.get("日期") or "").replace("/", "-")
        # normalize 2026-9-1 -> 2026-09-01
        parts = date.split("-")
        if len(parts) == 3:
            date = f"{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}"
        side = "buy" if kind == "買進" else "sell"
        symbol = (row.get("代號") or "").strip().upper() or norm_symbol(row.get("說明") or "")
        qty = abs(parse_num(row.get("數量")))
        price = abs(parse_num(row.get("價格")))
        amount = abs(parse_num(row.get("金額")))
        if qty <= 0 and amount > 0 and price > 0:
            qty = amount / price
        if qty <= 0:
            continue
        key = f"ft|{date}|{side}|{symbol}|{qty:.6f}|{price:.6f}|{amount:.2f}"
        trades.append(
            Trade(
                broker="firstrade",
                date=date,
                side=side,
                symbol=symbol,
                qty=qty,
                price=price,
                amount=amount,
                currency="USD",
                source=path.name,
                dedupe_key=key,
            )
        )
    return trades


def dedupe_trades(trades: list[Trade]) -> list[Trade]:
    """CSV 優先於 PDF（代號較準）；其餘依 dedupe_key。"""
    by_key: dict[str, Trade] = {}
    for t in trades:
        prev = by_key.get(t.dedupe_key)
        if prev is None:
            by_key[t.dedupe_key] = t
            continue
        # prefer csv source
        if "export" in t.source or t.source.endswith(".csv"):
            by_key[t.dedupe_key] = t
    # near-duplicate: same date/side/symbol/qty within 1% price
    items = list(by_key.values())
    items.sort(key=lambda x: (x.date, x.broker, x.symbol, x.side, x.qty, "csv" not in x.source))
    kept: list[Trade] = []
    for t in items:
        dup = False
        for k in kept:
            if (
                k.broker == t.broker
                and k.date == t.date
                and k.side == t.side
                and k.symbol == t.symbol
                and abs(k.qty - t.qty) < 1e-6
                and k.price > 0
                and abs(k.price - t.price) / k.price < 0.01
            ):
                # keep csv if either is csv
                if ("export" in t.source or t.source.endswith(".csv")) and not (
                    "export" in k.source or k.source.endswith(".csv")
                ):
                    kept.remove(k)
                    kept.append(t)
                dup = True
                break
        if not dup:
            kept.append(t)
    return kept


def fifo_trips(trades: list[Trade]) -> list[dict]:
    lots: dict[tuple, list] = defaultdict(list)
    trips = []
    for t in sorted(trades, key=lambda x: (x.date, x.side == "sell", x.source)):
        key = (t.broker, t.symbol, t.currency)
        if t.side == "buy":
            lots[key].append(
                {
                    "date": t.date,
                    "qty": t.qty,
                    "price": t.price,
                    "fees": t.fees,
                    "opt": t.is_option,
                    "warr": t.is_warrant,
                }
            )
            continue
        rem = t.qty
        sell_fee_u = t.fees / t.qty if t.qty else 0.0
        while rem > 1e-9 and lots[key]:
            lot = lots[key][0]
            mq = min(rem, lot["qty"])
            buy_fee = lot["fees"] * (mq / lot["qty"]) if lot["qty"] else 0.0
            sell_fee = sell_fee_u * mq
            mult = 100 if (t.is_option or lot["opt"]) else 1
            pnl_native = (t.price - lot["price"]) * mq * mult - buy_fee - sell_fee
            hold = (
                datetime.strptime(t.date, "%Y-%m-%d") - datetime.strptime(lot["date"], "%Y-%m-%d")
            ).days
            trips.append(
                {
                    "broker": t.broker,
                    "symbol": t.symbol,
                    "buy_date": lot["date"],
                    "sell_date": t.date,
                    "qty": mq,
                    "buy_price": lot["price"],
                    "sell_price": t.price,
                    "pnl_native": pnl_native,
                    "pnl_hkd": to_hkd(pnl_native, t.currency),
                    "fees": buy_fee + sell_fee,
                    "hold_days": max(hold, 0),
                    "currency": t.currency,
                    "is_option": t.is_option or lot["opt"],
                    "is_warrant": t.is_warrant or lot["warr"],
                    "month": t.date[:7],
                }
            )
            lot["qty"] -= mq
            lot["fees"] -= buy_fee
            rem -= mq
            if lot["qty"] <= 1e-9:
                lots[key].pop(0)
    return trips


def summarize(trades: list[Trade], trips: list[dict], label: str) -> dict:
    buys = [t for t in trades if t.side == "buy"]
    sells = [t for t in trades if t.side == "sell"]
    turnover = sum(to_hkd(t.amount, t.currency) for t in trades)
    fees = sum(to_hkd(t.fees, t.currency) for t in trades)
    wins = [t for t in trips if t["pnl_hkd"] > 0]
    losses = [t for t in trips if t["pnl_hkd"] < 0]
    realized = sum(t["pnl_hkd"] for t in trips)
    win_rate = len(wins) / len(trips) if trips else None
    avg_win = sum(t["pnl_hkd"] for t in wins) / len(wins) if wins else 0.0
    avg_loss = sum(t["pnl_hkd"] for t in losses) / len(losses) if losses else 0.0
    payoff = (avg_win / abs(avg_loss)) if avg_loss else None
    hold = [t["hold_days"] for t in trips]
    by_day = Counter(t.date for t in trades)
    symbols = Counter()
    for t in trades:
        symbols[t.symbol] += to_hkd(t.amount, t.currency)
    streak = cur = 0
    cur_amt = 0.0
    max_amt = 0.0
    for t in sorted(trips, key=lambda x: x["sell_date"]):
        if t["pnl_hkd"] < 0:
            cur += 1
            cur_amt += t["pnl_hkd"]
            streak = max(streak, cur)
            max_amt = min(max_amt, cur_amt)
        else:
            cur = 0
            cur_amt = 0.0
    by_sym = defaultdict(list)
    for t in trips:
        by_sym[t["symbol"]].append(t)
    revenge = {
        s: sum(x["pnl_hkd"] for x in v)
        for s, v in by_sym.items()
        if len(v) >= 3 and sum(x["pnl_hkd"] for x in v) < 0
    }
    return {
        "label": label,
        "trade_count": len(trades),
        "buy_count": len(buys),
        "sell_count": len(sells),
        "symbol_count": len({t.symbol for t in trades}),
        "date_start": min((t.date for t in trades), default=""),
        "date_end": max((t.date for t in trades), default=""),
        "turnover_hkd": turnover,
        "fees_hkd": fees,
        "fee_drag": fees / turnover if turnover else 0,
        "active_days": len(by_day),
        "avg_trades_per_day": len(trades) / len(by_day) if by_day else 0,
        "max_day_trades": max(by_day.values()) if by_day else 0,
        "round_trips": len(trips),
        "realized_pnl_hkd": realized,
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "payoff": payoff,
        "max_win": max((t["pnl_hkd"] for t in trips), default=0),
        "max_loss": min((t["pnl_hkd"] for t in trips), default=0),
        "day_trade_pct": sum(1 for d in hold if d <= 1) / len(trips) if trips else 0,
        "short_pct": sum(1 for d in hold if 1 < d <= 7) / len(trips) if trips else 0,
        "swing_pct": sum(1 for d in hold if d > 7) / len(trips) if trips else 0,
        "avg_hold": statistics.mean(hold) if hold else 0,
        "avg_hold_win": statistics.mean([t["hold_days"] for t in wins]) if wins else None,
        "avg_hold_loss": statistics.mean([t["hold_days"] for t in losses]) if losses else None,
        "top_symbol": symbols.most_common(10),
        "top_share": (symbols.most_common(1)[0][1] / turnover) if turnover and symbols else 0,
        "loss_streak_n": streak,
        "loss_streak_amt": max_amt,
        "revenge_symbols": revenge,
        "option_trades": sum(1 for t in trades if t.is_option),
        "warrant_trades": sum(1 for t in trades if t.is_warrant),
        "best_trips": sorted(trips, key=lambda x: -x["pnl_hkd"])[:8],
        "worst_trips": sorted(trips, key=lambda x: x["pnl_hkd"])[:8],
        "by_month_realized": dict(
            sorted(
                {
                    m: sum(t["pnl_hkd"] for t in trips if t["month"] == m)
                    for m in {t["month"] for t in trips}
                }.items()
            )
        ),
        "by_month_trades": dict(
            sorted(Counter(t.date[:7] for t in trades).items())
        ),
        "by_broker_realized": {
            b: sum(t["pnl_hkd"] for t in trips if t["broker"] == b)
            for b in sorted({t["broker"] for t in trips})
        },
    }


def load_all() -> tuple[list[Trade], list[NavPoint], dict]:
    ensure_extracts()
    trades: list[Trade] = []
    navs: list[NavPoint] = []
    meta = {"sources": []}

    for path in sorted(EXTRACT.glob("*.txt")):
        head = path.read_text(encoding="utf-8")[:2500]
        if "證券月結單" in head or "保證金綜合帳戶" in head:
            t, n, _ = parse_futu_text(path)
            trades.extend(t)
            navs.extend(n)
            meta["sources"].append({"file": path.name, "broker": "futu", "trades": len(t)})
        else:
            t, n = parse_firstrade_text(path)
            if t or n:
                trades.extend(t)
                navs.extend(n)
                meta["sources"].append({"file": path.name, "broker": "firstrade", "trades": len(t)})

    csv_paths = [
        ROOT / "statements" / "firstrade-export.csv",
        UPLOADS / "export_fb8c.csv",
        *sorted(UPLOADS.glob("export*.csv")),
        *sorted(UPLOADS.glob("*.csv")),
    ]
    seen_csv_hash: set[str] = set()
    for path in csv_paths:
        if not path.exists():
            continue
        digest = path.read_bytes()
        import hashlib

        h = hashlib.sha1(digest).hexdigest()
        if h in seen_csv_hash:
            continue
        seen_csv_hash.add(h)
        t = parse_firstrade_csv(path)
        trades.extend(t)
        meta["sources"].append({"file": path.name, "broker": "firstrade-csv", "trades": len(t)})

    before = len(trades)
    trades = dedupe_trades(trades)
    meta["raw_trades"] = before
    meta["deduped_trades"] = len(trades)
    return trades, navs, meta


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="合併全部月結分析")
    parser.add_argument("--stdout-json", action="store_true")
    args = parser.parse_args(argv)

    trades, navs, meta = load_all()
    trips = fifo_trips(trades)
    overall = summarize(trades, trips, "ALL")

    # monthly slices
    months = sorted({t.date[:7] for t in trades})
    monthly = {}
    for m in months:
        tr = [t for t in trades if t.date[:7] == m]
        tp = [t for t in trips if t["month"] == m]
        monthly[m] = summarize(tr, tp, m)

    # NAV adjusted
    nav_rows = []
    for n in sorted(navs, key=lambda x: (x.broker, x.month)):
        chg = n.close_native - n.open_native
        adj = chg - n.net_external_native
        nav_rows.append(
            {
                "broker": n.broker,
                "month": n.month,
                "open": n.open_native,
                "close": n.close_native,
                "currency": n.currency,
                "net_external": n.net_external_native,
                "adj_pnl": adj,
            }
        )

    payload = {
        "meta": meta,
        "overall": overall,
        "monthly": {k: {kk: vv for kk, vv in v.items() if kk not in ("best_trips", "worst_trips")} | {
            "best_trips": v["best_trips"][:3],
            "worst_trips": v["worst_trips"][:3],
        } for k, v in monthly.items()},
        "nav": nav_rows,
        "months_covered": months,
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "combined_all.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    (OUT / "combined_trades.json").write_text(
        json.dumps([asdict(t) for t in sorted(trades, key=lambda x: x.date)], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUT / "combined_trips.json").write_text(
        json.dumps(trips, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # human summary markdown
    o = overall
    lines = [
        f"# 合併全部月結覆盤（{o['date_start']} → {o['date_end']}）",
        "",
        f"- 來源數：{len(meta['sources'])}；原始成交 {meta['raw_trades']} → 去重後 {meta['deduped_trades']}",
        f"- 覆蓋月份：{', '.join(months)}",
        "",
        "## 總覽",
        "",
        f"- 成交筆數：{o['trade_count']}（買 {o['buy_count']} / 賣 {o['sell_count']}）",
        f"- 已實現盈虧（FIFO, HKD約當）：{o['realized_pnl_hkd']:.2f}",
        f"- 勝率：{(o['win_rate'] or 0)*100:.1f}%；盈虧比：{o['payoff']}",
        f"- 平均獲利/虧損：{o['avg_win']:.2f} / {o['avg_loss']:.2f}",
        f"- 最大連虧：{o['loss_streak_n']} 次 / {o['loss_streak_amt']:.2f} HKD",
        f"- 費用：{o['fees_hkd']:.2f}（佔成交額 {o['fee_drag']*100:.3f}%）",
        f"- 當沖/短線/波段：{o['day_trade_pct']*100:.1f}% / {o['short_pct']*100:.1f}% / {o['swing_pct']*100:.1f}%",
        "",
        "## 按月已實現",
        "",
    ]
    for m, v in o["by_month_realized"].items():
        lines.append(f"- {m}: {v:.2f} HKD（成交 {o['by_month_trades'].get(m,0)} 筆）")
    lines += ["", "## 券商已實現", ""]
    for b, v in o["by_broker_realized"].items():
        lines.append(f"- {b}: {v:.2f} HKD")
    lines += ["", "## 最差回合", ""]
    for t in o["worst_trips"][:8]:
        lines.append(
            f"- {t['sell_date']} {t['broker']} {t['symbol']} hold={t['hold_days']}d pnl={t['pnl_hkd']:.2f}"
        )
    lines += ["", "## 最佳回合", ""]
    for t in o["best_trips"][:8]:
        lines.append(
            f"- {t['sell_date']} {t['broker']} {t['symbol']} hold={t['hold_days']}d pnl={t['pnl_hkd']:.2f}"
        )
    md = "\n".join(lines) + "\n"
    (OUT / "combined_all.md").write_text(md, encoding="utf-8")

    print(md)
    if args.stdout_json:
        print(json.dumps({"meta": meta, "overall_core": {k: o[k] for k in o if k not in ("best_trips","worst_trips","revenge_symbols","top_symbol")}}, ensure_ascii=False, indent=2, default=str))
    print(f"\nJSON → {OUT / 'combined_all.json'}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
