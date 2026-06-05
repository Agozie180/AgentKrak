from __future__ import annotations

import pandas as pd


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of OHLCV data with the competition indicators attached."""
    data = df.copy()
    close = data["close"].astype(float)

    data["rsi_14"] = rsi(close, 14)
    data["ema_9"] = ema(close, 9)
    data["ema_21"] = ema(close, 21)

    macd_line, signal_line, histogram = macd(close)
    data["macd"] = macd_line
    data["macd_signal"] = signal_line
    data["macd_histogram"] = histogram

    mid = close.rolling(window=20, min_periods=20).mean()
    std = close.rolling(window=20, min_periods=20).std()
    data["bb_middle"] = mid
    data["bb_upper"] = mid + (2 * std)
    data["bb_lower"] = mid - (2 * std)
    return data


def ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def rsi(series: pd.Series, length: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    result = 100 - (100 / (1 + rs))
    return result.fillna(50)


def macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    macd_line = ema(series, fast) - ema(series, slow)
    signal_line = ema(macd_line, signal)
    return macd_line, signal_line, macd_line - signal_line
