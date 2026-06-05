from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd


BUY = "BUY"
SELL = "SELL"
HOLD = "HOLD"


def generate_signal(
    pair: str,
    indicator_frame: pd.DataFrame,
    ticker: dict[str, Any],
    order_book: dict[str, Any],
) -> dict[str, Any]:
    if len(indicator_frame) < 2:
        raise ValueError("At least two candles are required to generate a signal.")

    current = indicator_frame.iloc[-1]
    previous = indicator_frame.iloc[-2]
    price = float(ticker.get("price") or current["close"])
    spread_pct = float(order_book.get("spread_pct", 999))

    buy_conditions = []
    if float(current["rsi_14"]) < 45 and float(current["rsi_14"]) > float(previous["rsi_14"]):
        buy_conditions.append("RSI < 45 and rising")
    if _crossed_above(indicator_frame["ema_9"], indicator_frame["ema_21"], 2):
        buy_conditions.append("EMA 9 crossed above EMA 21")
    if _crossed_above(indicator_frame["macd"], indicator_frame["macd_signal"], 2):
        buy_conditions.append("MACD crossed above signal")
    if float(current["close"]) <= float(current["bb_lower"]):
        buy_conditions.append("Close at or below lower Bollinger Band")
    if spread_pct < 0.15:
        buy_conditions.append("Bid/ask spread below 0.15%")

    sell_conditions = []
    if float(current["rsi_14"]) > 60 and float(current["rsi_14"]) < float(previous["rsi_14"]):
        sell_conditions.append("RSI > 60 and falling")
    if _crossed_below(indicator_frame["ema_9"], indicator_frame["ema_21"], 2):
        sell_conditions.append("EMA 9 crossed below EMA 21")
    if _crossed_below(indicator_frame["macd"], indicator_frame["macd_signal"], 2):
        sell_conditions.append("MACD crossed below signal")
    if float(current["close"]) >= float(current["bb_upper"]):
        sell_conditions.append("Close at or above upper Bollinger Band")
    if spread_pct < 0.15:
        sell_conditions.append("Bid/ask spread below 0.15%")

    if len(buy_conditions) >= 3 and len(buy_conditions) >= len(sell_conditions):
        signal = BUY
        conditions = buy_conditions
    elif len(sell_conditions) >= 3:
        signal = SELL
        conditions = sell_conditions
    else:
        signal = HOLD
        conditions = buy_conditions if len(buy_conditions) >= len(sell_conditions) else sell_conditions

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pair": pair,
        "current_price": round(price, 8),
        "rsi": round(float(current["rsi_14"]), 2),
        "signal": signal,
        "confidence": min(len(conditions) * 20, 100),
        "conditions_met": conditions,
    }


def _crossed_above(left: pd.Series, right: pd.Series, candles: int = 2) -> bool:
    for idx in range(1, candles + 1):
        if len(left) <= idx:
            continue
        was_below = float(left.iloc[-idx - 1]) <= float(right.iloc[-idx - 1])
        now_above = float(left.iloc[-idx]) > float(right.iloc[-idx])
        if was_below and now_above:
            return True
    return False


def _crossed_below(left: pd.Series, right: pd.Series, candles: int = 2) -> bool:
    for idx in range(1, candles + 1):
        if len(left) <= idx:
            continue
        was_above = float(left.iloc[-idx - 1]) >= float(right.iloc[-idx - 1])
        now_below = float(left.iloc[-idx]) < float(right.iloc[-idx])
        if was_above and now_below:
            return True
    return False
