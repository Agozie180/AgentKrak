from __future__ import annotations

import importlib.metadata
import os
from pathlib import Path
import shutil
import sys
import time
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from .config import (
    DEFAULT_INITIAL_CAPITAL,
    DEFAULT_INTERVAL,
    DEFAULT_PAIRS,
    DEFAULT_POLL_SECONDS,
    SIGNALS_LOG,
    TRADES_LOG,
)
from .fetcher import KrakenCLIError, _kraken_command, get_ohlcv, get_order_book, get_ticker, stream_prices
from .indicators import add_indicators
from .logger import log_signal
from .paper_trader import PaperTrader, read_trade_summary, safe_handle_trade
from .reporter import build_dashboard, live_dashboard, print_dashboard
from .signals import generate_signal


console = Console()


def parse_pairs(value: str) -> list[str]:
    return [pair.strip() for pair in value.split(",") if pair.strip()]


def health_check() -> None:
    try:
        get_ticker("BTC/USD")
    except KrakenCLIError as exc:
        raise click.ClickException(
            "Kraken CLI health check failed.\n"
            f"{exc}\n\n"
            "Install Kraken CLI, then retry:\n"
            "curl --proto '=https' --tlsv1.2 -LsSf "
            "https://github.com/krakenfx/kraken-cli/releases/latest/download/"
            "kraken-cli-installer.sh | sh\n\n"
            "On Windows, Kraken currently recommends WSL. If the binary is installed in a "
            "custom location, set KRAKEN_COMMAND to that executable path."
        ) from exc


def analyze_pair(pair: str, interval: str) -> tuple[dict[str, Any], dict[str, Any]]:
    ticker = get_ticker(pair)
    order_book = get_order_book(pair)
    candles = add_indicators(get_ohlcv(pair, interval))
    signal = generate_signal(pair, candles, ticker, order_book)
    log_signal(signal)
    price_row = {
        "pair": pair,
        **ticker,
        "spread_pct": order_book["spread_pct"],
    }
    return price_row, signal


@click.group()
def cli() -> None:
    """AgentKrak autonomous market signal agent."""


@cli.command()
@click.option("--pairs", default=",".join(DEFAULT_PAIRS), show_default=True)
@click.option("--interval", default=DEFAULT_INTERVAL, show_default=True)
@click.option("--capital", default=DEFAULT_INITIAL_CAPITAL, show_default=True, type=float)
@click.option("--poll", default=DEFAULT_POLL_SECONDS, show_default=True, type=int)
@click.option("--cycles", default=0, hidden=True, type=int)
def run(pairs: str, interval: str, capital: float, poll: int, cycles: int) -> None:
    """Start fetch -> analyze -> signal -> paper trade -> dashboard loop."""
    health_check()
    pair_list = parse_pairs(pairs)
    trader = PaperTrader(capital=capital)
    latest_prices: list[dict[str, Any]] = []
    latest_signals: list[dict[str, Any]] = []
    errors: list[str] = []
    completed_cycles = 0

    with live_dashboard() as live:
        while True:
            cycle_prices = []
            for pair in pair_list:
                try:
                    price_row, signal = analyze_pair(pair, interval)
                    cycle_prices.append(price_row)
                    latest_signals.append(signal)
                    trade_result = safe_handle_trade(trader, signal)
                    if trade_result and trade_result.get("error"):
                        errors.append(str(trade_result["error"]))
                except Exception as exc:
                    errors.append(f"{pair}: {exc}")
            if cycle_prices:
                latest_prices = cycle_prices
            live.update(
                build_dashboard(latest_prices, latest_signals, trader.summary(), errors),
                refresh=True,
            )
            completed_cycles += 1
            if cycles and completed_cycles >= cycles:
                break
            time.sleep(poll)


@cli.command()
@click.option("--pairs", default=",".join(DEFAULT_PAIRS), show_default=True)
@click.option("--interval", default=DEFAULT_INTERVAL, show_default=True)
def signals(pairs: str, interval: str) -> None:
    """Fetch, compute, print current signals, then exit."""
    health_check()
    price_rows = []
    signal_rows = []
    errors = []
    for pair in parse_pairs(pairs):
        try:
            price_row, signal = analyze_pair(pair, interval)
            price_rows.append(price_row)
            signal_rows.append(signal)
        except Exception as exc:
            errors.append(f"{pair}: {exc}")
    print_dashboard(console, price_rows, signal_rows, read_trade_summary(), errors)


@cli.command()
@click.option("--pairs", default=",".join(DEFAULT_PAIRS), show_default=True)
@click.option("--duration", default=60, show_default=True, type=int)
def stream(pairs: str, duration: int) -> None:
    """Stream live price ticks from Kraken WebSocket ticker."""
    health_check()
    for tick in stream_prices(parse_pairs(pairs), duration):
        console.print_json(data=tick)


@cli.command()
def report() -> None:
    """Print trade log summary and exit."""
    print_dashboard(console, [], [], read_trade_summary(), [])


@cli.command()
def doctor() -> None:
    """Check local readiness for the AgentKrak demo."""
    table = Table(title="AgentKrak Doctor", expand=True)
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail")

    command = _kraken_command()
    executable = command[0] if command else "kraken"
    resolved = shutil.which(executable)
    table.add_row(
        "Python",
        "OK",
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    )
    table.add_row(
        "Kraken command",
        "OK" if resolved else "MISSING",
        " ".join(command) if command else "kraken",
        style=None if resolved else "red",
    )
    if os.environ.get("KRAKEN_COMMAND"):
        table.add_row("KRAKEN_COMMAND", "SET", os.environ["KRAKEN_COMMAND"])

    for package in ["pandas", "rich", "click"]:
        table.add_row("Dependency", "OK", f"{package} {version_of(package)}")
    table.add_row("Dependency", "OPTIONAL", f"pandas-ta {version_of('pandas-ta')}")

    try:
        ticker = get_ticker("BTC/USD")
        table.add_row("Live Kraken ticker", "OK", f"BTC/USD ${ticker['price']:,.2f}", style="green")
    except KrakenCLIError as exc:
        table.add_row("Live Kraken ticker", "FAILED", str(exc), style="red")

    for log_path in [SIGNALS_LOG, TRADES_LOG]:
        parent = Path(log_path).resolve().parent
        table.add_row(
            log_path,
            "OK" if os.access(parent, os.W_OK) else "FAILED",
            f"Directory: {parent}",
            style=None if os.access(parent, os.W_OK) else "red",
        )

    console.print(table)


def version_of(package: str) -> str:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return "not installed"


if __name__ == "__main__":
    cli()
