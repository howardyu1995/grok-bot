"""從正規化成交紀錄計算交易傾向指標。"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .parsers import Trade


@dataclass
class RoundTrip:
    symbol: str
    broker: str
    buy_date: str
    sell_date: str
    quantity: float
    buy_price: float
    sell_price: float
    pnl: float
    fees: float
    hold_days: int
    currency: str


@dataclass
class Analysis:
    month: str
    trades: list[Trade]
    round_trips: list[RoundTrip]
    metrics: dict[str, Any] = field(default_factory=dict)
    tendencies: list[str] = field(default_factory=list)
    symbol_stats: list[dict[str, Any]] = field(default_factory=list)
    broker_stats: list[dict[str, Any]] = field(default_factory=list)
    weekday_stats: list[dict[str, Any]] = field(default_factory=list)


def _parse_day(date_str: str) -> datetime:
    return datetime.strptime(date_str[:10], "%Y-%m-%d")


def filter_by_month(trades: list[Trade], month: str | None) -> tuple[list[Trade], str]:
    if not trades:
        return [], month or ""
    if month:
        filtered = [t for t in trades if t.trade_date.startswith(month)]
        return filtered, month
    # default: most common YYYY-MM
    months = Counter(t.trade_date[:7] for t in trades if t.trade_date)
    top = months.most_common(1)[0][0]
    return [t for t in trades if t.trade_date.startswith(top)], top


def build_round_trips(trades: list[Trade]) -> list[RoundTrip]:
    lots: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    trips: list[RoundTrip] = []
    ordered = sorted(trades, key=lambda t: (t.trade_date, t.trade_time or "", t.source_row))

    for trade in ordered:
        key = (trade.broker, trade.symbol)
        if trade.side == "buy":
            lots[key].append(
                {
                    "date": trade.trade_date,
                    "qty": trade.quantity,
                    "price": trade.price,
                    "fees": trade.fees,
                    "currency": trade.currency,
                }
            )
            continue

        remaining = trade.quantity
        sell_fees_unit = trade.fees / trade.quantity if trade.quantity else 0.0
        while remaining > 1e-9 and lots[key]:
            lot = lots[key][0]
            matched = min(remaining, lot["qty"])
            buy_fee_share = lot["fees"] * (matched / lot["qty"]) if lot["qty"] else 0.0
            sell_fee_share = sell_fees_unit * matched
            pnl = (trade.price - lot["price"]) * matched - buy_fee_share - sell_fee_share
            hold_days = (_parse_day(trade.trade_date) - _parse_day(lot["date"])).days
            trips.append(
                RoundTrip(
                    symbol=trade.symbol,
                    broker=trade.broker,
                    buy_date=lot["date"],
                    sell_date=trade.trade_date,
                    quantity=matched,
                    buy_price=lot["price"],
                    sell_price=trade.price,
                    pnl=pnl,
                    fees=buy_fee_share + sell_fee_share,
                    hold_days=max(hold_days, 0),
                    currency=trade.currency or lot["currency"],
                )
            )
            lot["qty"] -= matched
            lot["fees"] -= buy_fee_share
            remaining -= matched
            if lot["qty"] <= 1e-9:
                lots[key].pop(0)
    return trips


def analyze(trades: list[Trade], month: str | None = None) -> Analysis:
    month_trades, resolved_month = filter_by_month(trades, month)
    trips = build_round_trips(month_trades)

    buy_count = sum(1 for t in month_trades if t.side == "buy")
    sell_count = sum(1 for t in month_trades if t.side == "sell")
    total_fees = sum(t.fees for t in month_trades)
    turnover = sum(t.amount for t in month_trades)
    symbols = sorted({t.symbol for t in month_trades})

    realized = [t for t in trips]
    wins = [t for t in realized if t.pnl > 0]
    losses = [t for t in realized if t.pnl < 0]
    realized_pnl = sum(t.pnl for t in realized)
    win_rate = (len(wins) / len(realized)) if realized else 0.0
    avg_win = (sum(t.pnl for t in wins) / len(wins)) if wins else 0.0
    avg_loss = (sum(t.pnl for t in losses) / len(losses)) if losses else 0.0
    payoff = (avg_win / abs(avg_loss)) if avg_loss else (float("inf") if avg_win else 0.0)
    avg_hold = (sum(t.hold_days for t in realized) / len(realized)) if realized else 0.0
    day_trades = sum(1 for t in realized if t.hold_days <= 1)
    day_trade_ratio = (day_trades / len(realized)) if realized else 0.0

    # concentration by turnover
    by_symbol_turn = Counter()
    for t in month_trades:
        by_symbol_turn[t.symbol] += t.amount
    top_symbol_share = 0.0
    if turnover > 0 and by_symbol_turn:
        top_symbol_share = by_symbol_turn.most_common(1)[0][1] / turnover

    # trading days intensity
    by_day = Counter(t.trade_date for t in month_trades)
    active_days = len(by_day)
    max_day_trades = max(by_day.values()) if by_day else 0
    avg_per_active_day = (len(month_trades) / active_days) if active_days else 0.0

    weekday_names = ["一", "二", "三", "四", "五", "六", "日"]
    weekday_counter: Counter[int] = Counter()
    weekday_pnl: dict[int, float] = defaultdict(float)
    for t in month_trades:
        wd = _parse_day(t.trade_date).weekday()
        weekday_counter[wd] += 1
    for trip in realized:
        wd = _parse_day(trip.sell_date).weekday()
        weekday_pnl[wd] += trip.pnl

    symbol_stats = []
    trip_by_symbol: dict[str, list[RoundTrip]] = defaultdict(list)
    for trip in realized:
        trip_by_symbol[trip.symbol].append(trip)
    for symbol, turn in by_symbol_turn.most_common():
        sym_trips = trip_by_symbol.get(symbol, [])
        symbol_stats.append(
            {
                "symbol": symbol,
                "turnover": turn,
                "share": (turn / turnover) if turnover else 0.0,
                "trades": sum(1 for t in month_trades if t.symbol == symbol),
                "realized_pnl": sum(t.pnl for t in sym_trips),
                "round_trips": len(sym_trips),
            }
        )

    broker_stats = []
    brokers = sorted({t.broker for t in month_trades})
    for broker in brokers:
        b_trades = [t for t in month_trades if t.broker == broker]
        b_trips = [t for t in realized if t.broker == broker]
        b_turn = sum(t.amount for t in b_trades)
        broker_stats.append(
            {
                "broker": broker,
                "trades": len(b_trades),
                "turnover": b_turn,
                "fees": sum(t.fees for t in b_trades),
                "realized_pnl": sum(t.pnl for t in b_trips),
                "symbols": len({t.symbol for t in b_trades}),
            }
        )

    fee_drag = (total_fees / turnover) if turnover else 0.0
    metrics = {
        "trade_count": len(month_trades),
        "buy_count": buy_count,
        "sell_count": sell_count,
        "symbol_count": len(symbols),
        "turnover": turnover,
        "total_fees": total_fees,
        "fee_drag": fee_drag,
        "active_days": active_days,
        "avg_trades_per_active_day": avg_per_active_day,
        "max_trades_single_day": max_day_trades,
        "round_trips": len(realized),
        "win_rate": win_rate,
        "realized_pnl": realized_pnl,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "payoff_ratio": payoff if payoff != float("inf") else None,
        "avg_hold_days": avg_hold,
        "day_trade_ratio": day_trade_ratio,
        "top_symbol_share": top_symbol_share,
        "open_lots_estimate": max(0, buy_count - len(realized)),  # rough
    }

    tendencies = _infer_tendencies(metrics, month_trades, realized)

    weekday_stats = [
        {
            "weekday": weekday_names[i],
            "trades": weekday_counter.get(i, 0),
            "realized_pnl": weekday_pnl.get(i, 0.0),
        }
        for i in range(7)
        if weekday_counter.get(i, 0) or weekday_pnl.get(i, 0)
    ]

    return Analysis(
        month=resolved_month,
        trades=month_trades,
        round_trips=realized,
        metrics=metrics,
        tendencies=tendencies,
        symbol_stats=symbol_stats,
        broker_stats=broker_stats,
        weekday_stats=weekday_stats,
    )


def _infer_tendencies(
    metrics: dict[str, Any], trades: list[Trade], trips: list[RoundTrip]
) -> list[str]:
    tags: list[str] = []
    count = metrics["trade_count"]
    if count >= 40 or metrics["avg_trades_per_active_day"] >= 4:
        tags.append("高頻／過度交易傾向")
    elif count <= 8:
        tags.append("低頻、精選出手")

    if metrics["day_trade_ratio"] >= 0.45:
        tags.append("偏日內短打")
    elif metrics["avg_hold_days"] >= 10:
        tags.append("偏波段持有")
    elif trips:
        tags.append("短線波段混合")

    if metrics["top_symbol_share"] >= 0.45:
        tags.append("標的過度集中")
    elif metrics["symbol_count"] >= 12 and count:
        tags.append("標的分散偏廣")

    if metrics["round_trips"]:
        if metrics["win_rate"] >= 0.55 and (metrics["payoff_ratio"] or 0) < 0.9:
            tags.append("勝率尚可但盈虧比偏弱（小賺大虧風險）")
        if metrics["win_rate"] < 0.4:
            tags.append("勝率偏低")
        if (metrics["payoff_ratio"] or 0) >= 1.5 and metrics["win_rate"] >= 0.4:
            tags.append("盈虧結構相對健康")

    if metrics["fee_drag"] >= 0.002:
        tags.append("費用侵蝕明顯")

    buys = metrics["buy_count"]
    sells = metrics["sell_count"]
    if buys + sells > 0:
        if buys / (buys + sells) >= 0.65:
            tags.append("單月偏多買入／加倉")
        elif sells / (buys + sells) >= 0.65:
            tags.append("單月偏多了結／減倉")

    # chase pattern: many same-symbol round trips with short holds and net loss
    by_sym = defaultdict(list)
    for trip in trips:
        by_sym[trip.symbol].append(trip)
    revenge = 0
    for sym_trips in by_sym.values():
        if len(sym_trips) >= 3 and sum(t.pnl for t in sym_trips) < 0:
            revenge += 1
    if revenge:
        tags.append("同一標的反覆進出且虧損（疑似追單／報復性交易）")

    if not tags:
        tags.append("樣本尚不足以標定強烈傾向")
    return tags
