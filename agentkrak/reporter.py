from __future__ import annotations

import sys
from typing import Any

from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


UNICODE_BANNER = "⚡ AgentKrak v1.0 | Kraken CLI Trading Agent"
ASCII_BANNER = "AgentKrak v1.0 | Kraken CLI Trading Agent"


def signal_style(signal: str) -> str:
    return {"BUY": "green", "SELL": "red", "HOLD": "yellow"}.get(signal, "white")


def build_dashboard(
    prices: list[dict[str, Any]],
    signals: list[dict[str, Any]],
    trade_summary: dict[str, Any],
    errors: list[str] | None = None,
) -> Group:
    return Group(
        Panel(Text(_banner(), style="bold cyan"), border_style="cyan"),
        _price_table(prices),
        _signals_table(signals),
        _conditions_panel(signals),
        _trades_table(trade_summary),
        _errors_panel(errors or []),
        Panel("Powered by Kraken CLI | Press Ctrl+C to stop", border_style="blue"),
    )


def live_dashboard(refresh_per_second: float = 4) -> Live:
    return Live(auto_refresh=False, refresh_per_second=refresh_per_second, screen=True)


def print_dashboard(console, prices, signals, trade_summary, errors=None) -> None:
    console.print(build_dashboard(prices, signals, trade_summary, errors))


def _banner() -> str:
    encoding = (getattr(sys.stdout, "encoding", None) or "").lower()
    return UNICODE_BANNER if "utf" in encoding else ASCII_BANNER


def _price_table(prices: list[dict[str, Any]]) -> Table:
    table = Table(title="Live Prices", expand=True)
    table.add_column("Pair")
    table.add_column("Price", justify="right")
    table.add_column("24h Change", justify="right")
    table.add_column("Volume", justify="right")
    table.add_column("Spread", justify="right")
    for row in prices:
        table.add_row(
            str(row.get("pair", "")),
            f"{float(row.get('price', 0)):,.2f}",
            f"{float(row.get('change_24h', 0)):.2f}%",
            f"{float(row.get('volume', 0)):,.4f}",
            f"{float(row.get('spread_pct', 0)):.3f}%",
        )
    return table


def _signals_table(signals: list[dict[str, Any]]) -> Table:
    table = Table(title="Latest Signals", expand=True, show_lines=False)
    table.add_column("Time", no_wrap=True, width=5)
    table.add_column("Pair", no_wrap=True, width=7)
    table.add_column("Signal", no_wrap=True, width=9)
    table.add_column("RSI", justify="right", no_wrap=True, width=5)
    table.add_column("Conf", justify="right", no_wrap=True, width=5)
    table.add_column("SL", justify="right", no_wrap=True, width=9)
    table.add_column("TP", justify="right", no_wrap=True, width=9)
    table.add_column("R:R", justify="right", no_wrap=True, width=4)
    for signal in signals[-10:]:
        style = signal_style(str(signal.get("signal", "")))
        signal_label = _signal_label(signal)
        table.add_row(
            _time_only(signal.get("timestamp")),
            str(signal.get("pair", "")),
            signal_label,
            f"{float(signal.get('rsi', 0)):.2f}",
            f"{int(signal.get('confidence', 0))}%",
            _price_or_dash(signal.get("stop_loss")),
            _price_or_dash(signal.get("take_profit")),
            _ratio_or_dash(signal.get("risk_reward")),
            style=style,
        )
    return table


def _conditions_panel(signals: list[dict[str, Any]]) -> Panel:
    if not signals:
        return Panel("No signal diagnostics yet", title="Signal Diagnostics", border_style="cyan")
    lines = []
    for signal in signals[-5:]:
        pair = str(signal.get("pair", ""))
        confidence = int(signal.get("confidence", 0))
        threshold = int(signal.get("min_confidence", 0))
        status = "TRADE" if signal.get("tradable") else "WATCH"
        codes = _condition_codes(signal.get("conditions_met", []))
        lines.append(f"{pair}: {status} | conf {confidence}% / min {threshold}% | {codes}")
    return Panel("\n".join(lines), title="Signal Diagnostics", border_style="cyan")


def _signal_label(signal: dict[str, Any]) -> str:
    current = str(signal.get("signal", ""))
    raw = str(signal.get("raw_signal", current))
    tradable = bool(signal.get("tradable", current in {"BUY", "SELL"}))
    if raw in {"BUY", "SELL"} and current == "HOLD" and not tradable:
        return f"HOLD/{raw}"
    return current


def _price_or_dash(value: Any) -> str:
    if value in (None, ""):
        return "-"
    return f"{float(value):,.2f}"


def _ratio_or_dash(value: Any) -> str:
    if value in (None, ""):
        return "-"
    return f"{float(value):.2f}"


def _time_only(value: Any) -> str:
    text = str(value or "")
    if "T" in text:
        return text.split("T", 1)[1][:5]
    return text[:5]


def _condition_codes(conditions: Any) -> str:
    codes = []
    for condition in conditions or []:
        text = str(condition)
        lowered = text.lower()
        if "filtered" in lowered:
            codes.append("FILTER")
        elif "rsi" in lowered:
            codes.append("RSI")
        elif "ema" in lowered:
            codes.append("EMA")
        elif "macd" in lowered:
            codes.append("MACD")
        elif "bollinger" in lowered:
            codes.append("BB")
        elif "spread" in lowered:
            codes.append("SPREAD")
        else:
            codes.append(text[:10])
    return ", ".join(codes) if codes else "-"


def _trades_table(summary: dict[str, Any]) -> Table:
    table = Table(title="Paper Trading Summary", expand=True)
    table.add_column("Total Trades", justify="right")
    table.add_column("Wins", justify="right")
    table.add_column("Losses", justify="right")
    table.add_column("Win Rate", justify="right")
    table.add_column("Total PnL", justify="right")
    table.add_row(
        str(summary.get("total_trades", 0)),
        str(summary.get("wins", 0)),
        str(summary.get("losses", 0)),
        f"{float(summary.get('win_rate', 0)):.2f}%",
        f"${float(summary.get('total_pnl', 0)):,.2f}",
    )
    return table


def _errors_panel(errors: list[str]) -> Panel:
    text = "\n".join(errors[-5:]) if errors else "No errors"
    return Panel(text, title="Status", border_style="red" if errors else "green")
