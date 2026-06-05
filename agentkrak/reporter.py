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
    table = Table(title="Latest Signals", expand=True)
    table.add_column("Time")
    table.add_column("Pair")
    table.add_column("Signal")
    table.add_column("RSI", justify="right")
    table.add_column("Confidence", justify="right")
    table.add_column("Conditions")
    for signal in signals[-10:]:
        style = signal_style(str(signal.get("signal", "")))
        table.add_row(
            str(signal.get("timestamp", ""))[:19],
            str(signal.get("pair", "")),
            str(signal.get("signal", "")),
            f"{float(signal.get('rsi', 0)):.2f}",
            f"{int(signal.get('confidence', 0))}%",
            "; ".join(signal.get("conditions_met", [])),
            style=style,
        )
    return table


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
