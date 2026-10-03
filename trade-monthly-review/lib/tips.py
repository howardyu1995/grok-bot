"""依分析指標產生可執行的策略優化建議。"""

from __future__ import annotations

from .analyzer import Analysis


def build_tips(analysis: Analysis) -> list[dict[str, str]]:
    m = analysis.metrics
    tips: list[dict[str, str]] = []

    def add(priority: str, title: str, detail: str) -> None:
        tips.append({"priority": priority, "title": title, "detail": detail})

    if m["trade_count"] == 0:
        add("高", "本月沒有可分析成交", "請確認匯出區間是否正確，或檔案是否放在 statements/ 內。")
        return tips

    if m["trade_count"] >= 40 or m["avg_trades_per_active_day"] >= 4:
        add(
            "高",
            "降低交易頻率，先設「每日上限」",
            f"本月 {m['trade_count']} 筆、活躍日均 {m['avg_trades_per_active_day']:.1f} 筆。"
            "建議下一交易月先訂：每天最多 2～3 筆計畫內交易；盤中衝動單隔日再評估。",
        )

    if m["day_trade_ratio"] >= 0.45:
        add(
            "高",
            "日內短打比例偏高：改用「進場前計畫」",
            f"已實現回合中約 {m['day_trade_ratio']:.0%} 為 0～1 日持倉。"
            "每筆進場前寫下：觸發條件、停損、目標、最大持倉時間；逾時未達標就減倉而非加倉。",
        )
    elif m["avg_hold_days"] >= 10:
        add(
            "中",
            "波段持有為主：強化再評估節奏",
            f"平均持倉約 {m['avg_hold_days']:.1f} 日。建議每週固定檢視一次：邏輯是否仍成立、"
            "是否因消息面漂移而變成「捨不得賣」。",
        )

    if m["top_symbol_share"] >= 0.45 and analysis.symbol_stats:
        top = analysis.symbol_stats[0]
        add(
            "高",
            f"資金過度集中在 {top['symbol']}",
            f"該標的佔成交額約 {top['share']:.0%}。建議單一標的週轉額不超過當月的 30%，"
            "或把加倉拆成 2～3 次，避免單點情緒放大。",
        )

    if m["round_trips"]:
        if m["win_rate"] >= 0.55 and (m["payoff_ratio"] is not None and m["payoff_ratio"] < 0.9):
            add(
                "高",
                "勝率不差但盈虧比偏弱：先修出場",
                f"勝率 {m['win_rate']:.0%}，平均盈利 {m['avg_win']:.2f}、平均虧損 {m['avg_loss']:.2f}。"
                "重點不是多找進場，而是：讓盈利單有空間、虧損單更快截斷（例如風險報酬至少 1:1.5）。",
            )
        if m["win_rate"] < 0.4:
            add(
                "高",
                "勝率偏低：縮小標的宇宙",
                f"已實現勝率 {m['win_rate']:.0%}。下一月只保留你最熟的 3～5 檔，"
                "其餘觀望；並回顧虧損單是否多來自追高或無計畫反手。",
            )
        if m["payoff_ratio"] is not None and m["payoff_ratio"] >= 1.5 and m["win_rate"] >= 0.4:
            add(
                "低",
                "盈虧結構尚可：維持並記錄可複製條件",
                "把盈利回合的進場觸發、持倉時間、出場原因記成檢查表，下月只做符合表單的交易。",
            )

    if m["fee_drag"] >= 0.002:
        add(
            "中",
            "費用拖累不可忽視",
            f"費用約佔成交額 {m['fee_drag']:.2%}（總費用 {m['total_fees']:.2f}）。"
            "合併碎單、減少無邊緣的來回，或評估是否有更合適的下單方式／市場時段。",
        )

    if "同一標的反覆進出且虧損（疑似追單／報復性交易）" in analysis.tendencies:
        add(
            "高",
            "禁止同標的當日反覆翻面",
            "對已虧損標的設「冷卻期」：當日停手，至少隔一個交易時段再評估；"
            "若要再進場，必須有新的獨立理由，而非想回本。",
        )

    if m["buy_count"] + m["sell_count"] > 0:
        buy_share = m["buy_count"] / (m["buy_count"] + m["sell_count"])
        if buy_share >= 0.65:
            add(
                "中",
                "本月偏多買入：檢查現金與風險預算",
                "確認加倉是否來自計畫內分批，而非行情上漲後 FOMO。"
                "為下一月預留固定現金比例，避免買滿後失去應變空間。",
            )
        elif buy_share <= 0.35:
            add(
                "中",
                "本月偏多賣出：區分「計畫了結」與「情緒砍倉」",
                "回顧賣出是否觸發預設目標／停損。若多為盤中害怕而砍，下一月改用預掛條件單減少臨場決策。",
            )

    # broker-specific
    for b in analysis.broker_stats:
        if b["broker"] == "futu" and b["fees"] > 0 and b["turnover"] and b["fees"] / b["turnover"] > 0.003:
            add(
                "中",
                "富途費用佔比偏高",
                "核對是否含港股印花稅／碎股／期權等較貴品種；若美股為主，可把高週轉策略集中到費用更可控的帳戶。",
            )
        if b["broker"] == "firstrade" and b["trades"] >= 15 and b["realized_pnl"] < 0:
            add(
                "中",
                "Firstrade 帳戶本月已實現為負",
                "美股帳戶適合用「觀察清單 + 限價」降低追價；避免開盤後 15 分鐘內無計畫市價單。",
            )

    # always give one process tip
    add(
        "低",
        "固定每月复盤節奏",
        "每月結單出來後重跑本工具：對照成交筆數、勝率、盈虧比、集中度四項是否改善。"
        "只追蹤 1～2 個改進點，比同時改很多習慣更有效。",
    )

    # sort by priority
    order = {"高": 0, "中": 1, "低": 2}
    tips.sort(key=lambda t: order.get(t["priority"], 9))
    return tips
