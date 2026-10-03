"""把分析結果渲染成繁中 Markdown 報告。"""

from __future__ import annotations

from datetime import datetime

from .analyzer import Analysis
from .tips import build_tips


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _num(value: float, digits: int = 2) -> str:
    return f"{value:,.{digits}f}"


def _broker_label(broker: str) -> str:
    return {
        "futu": "富途牛牛",
        "firstrade": "Firstrade",
        "unknown": "未知",
    }.get(broker, broker)


def render_markdown(analysis: Analysis, warnings: list[str] | None = None) -> str:
    m = analysis.metrics
    tips = build_tips(analysis)
    lines: list[str] = []
    lines.append(f"# 月結交易傾向報告（{analysis.month or '未指定月份'}）")
    lines.append("")
    lines.append(f"產生時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append("> 資料只在本機處理；本報告為行為與風控复盤，非投資建議。")
    lines.append("")

    if warnings:
        lines.append("## 解析提醒")
        lines.append("")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    lines.append("## 1. 本月概覽")
    lines.append("")
    lines.append("| 指標 | 數值 |")
    lines.append("| --- | --- |")
    lines.append(f"| 成交筆數 | {m['trade_count']}（買 {m['buy_count']} / 賣 {m['sell_count']}） |")
    lines.append(f"| 標的數 | {m['symbol_count']} |")
    lines.append(f"| 成交額（合計，原幣未換匯） | {_num(m['turnover'])} |")
    lines.append(f"| 費用合計 | {_num(m['total_fees'])}（佔成交額 {_pct(m['fee_drag'])}） |")
    lines.append(f"| 有交易日數 | {m['active_days']}（日均 {m['avg_trades_per_active_day']:.1f} 筆） |")
    lines.append(f"| 單日最多成交 | {m['max_trades_single_day']} 筆 |")
    if m["round_trips"]:
        payoff = (
            "∞"
            if m["payoff_ratio"] is None and m["avg_win"] > 0
            else (_num(m["payoff_ratio"]) if m["payoff_ratio"] is not None else "n/a")
        )
        lines.append(f"| 已實現回合 | {m['round_trips']} |")
        lines.append(f"| 已實現盈虧 | {_num(m['realized_pnl'])} |")
        lines.append(f"| 勝率 | {_pct(m['win_rate'])} |")
        lines.append(f"| 平均盈利 / 平均虧損 | {_num(m['avg_win'])} / {_num(m['avg_loss'])} |")
        lines.append(f"| 盈虧比 | {payoff} |")
        lines.append(f"| 平均持倉天數 | {m['avg_hold_days']:.1f} |")
        lines.append(f"| 日內短打佔比 | {_pct(m['day_trade_ratio'])} |")
        lines.append(f"| 最大標的成交額佔比 | {_pct(m['top_symbol_share'])} |")
    else:
        lines.append("| 已實現回合 | 0（可能仍有未平倉，或賣出落在其他月份） |")
    lines.append("")

    lines.append("## 2. 交易傾向")
    lines.append("")
    for tag in analysis.tendencies:
        lines.append(f"- {tag}")
    lines.append("")

    if analysis.broker_stats:
        lines.append("## 3. 券商拆分")
        lines.append("")
        lines.append("| 券商 | 筆數 | 標的 | 成交額 | 費用 | 已實現盈虧 |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
        for b in analysis.broker_stats:
            lines.append(
                f"| {_broker_label(b['broker'])} | {b['trades']} | {b['symbols']} | "
                f"{_num(b['turnover'])} | {_num(b['fees'])} | {_num(b['realized_pnl'])} |"
            )
        lines.append("")

    if analysis.symbol_stats:
        lines.append("## 4. 標的集中度（成交額 Top）")
        lines.append("")
        lines.append("| 標的 | 筆數 | 成交額佔比 | 已實現盈虧 | 回合數 |")
        lines.append("| --- | ---: | ---: | ---: | ---: |")
        for row in analysis.symbol_stats[:10]:
            lines.append(
                f"| {row['symbol']} | {row['trades']} | {_pct(row['share'])} | "
                f"{_num(row['realized_pnl'])} | {row['round_trips']} |"
            )
        lines.append("")

    if analysis.weekday_stats:
        lines.append("## 5. 星期分布")
        lines.append("")
        lines.append("| 星期 | 成交筆數 | 賣出回合盈虧 |")
        lines.append("| --- | ---: | ---: |")
        for row in analysis.weekday_stats:
            lines.append(
                f"| 週{row['weekday']} | {row['trades']} | {_num(row['realized_pnl'])} |"
            )
        lines.append("")

    if analysis.round_trips:
        best = [t for t in sorted(analysis.round_trips, key=lambda t: t.pnl, reverse=True) if t.pnl > 0][:5]
        worst = [t for t in sorted(analysis.round_trips, key=lambda t: t.pnl) if t.pnl < 0][:5]
        lines.append("## 6. 最佳／最差已實現回合")
        lines.append("")
        lines.append("### 最佳")
        lines.append("")
        if best:
            for t in best:
                lines.append(
                    f"- {t.symbol}（{_broker_label(t.broker)}）"
                    f" {t.buy_date}→{t.sell_date} 持倉 {t.hold_days} 日"
                    f"：{_num(t.pnl)} {t.currency}"
                )
        else:
            lines.append("- 本月沒有已實現盈利回合")
        lines.append("")
        lines.append("### 最差")
        lines.append("")
        if worst:
            for t in worst:
                lines.append(
                    f"- {t.symbol}（{_broker_label(t.broker)}）"
                    f" {t.buy_date}→{t.sell_date} 持倉 {t.hold_days} 日"
                    f"：{_num(t.pnl)} {t.currency}"
                )
        else:
            lines.append("- 本月沒有已實現虧損回合")
        lines.append("")

    lines.append("## 7. 如何優化交易策點")
    lines.append("")
    for i, tip in enumerate(tips, start=1):
        lines.append(f"### {i}. [{tip['priority']}] {tip['title']}")
        lines.append("")
        lines.append(tip["detail"])
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("下個月：把新的 CSV／XLSX 放進 `statements/`，再執行一次 `python3 analyze.py`。")
    lines.append("")
    return "\n".join(lines)
