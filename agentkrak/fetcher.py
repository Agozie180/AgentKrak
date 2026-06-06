from __future__ import annotations

import json
import os
import shlex
from pathlib import Path
import subprocess
import time
from collections.abc import Generator, Iterable
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from .config import (
    DEFAULT_KRAKEN_COMMAND,
    KRAKEN_BACKOFF_SECONDS,
    KRAKEN_RETRIES,
    KRAKEN_TIMEOUT_SECONDS,
)


class KrakenCLIError(RuntimeError):
    pass


def run_kraken(
    args: list[str],
    retries: int = KRAKEN_RETRIES,
    timeout: int = KRAKEN_TIMEOUT_SECONDS,
) -> Any:
    command = [*_kraken_command(), *args, "-o", "json"]
    last_error = ""

    for attempt in range(retries + 1):
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                check=False,
                text=True,
                timeout=timeout,
            )
        except FileNotFoundError as exc:
            raise KrakenCLIError(
                "Kraken CLI was not found. Install it with the official installer, ensure "
                "`kraken` is on PATH, or set KRAKEN_COMMAND to the executable path."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            last_error = f"Kraken CLI timed out after {timeout}s: {' '.join(command)}"
            if attempt == retries:
                raise KrakenCLIError(last_error) from exc
            time.sleep(_retry_delay(attempt))
            continue

        if completed.returncode != 0:
            last_error = completed.stderr.strip() or completed.stdout.strip()
            if attempt == retries:
                raise KrakenCLIError(
                    f"Kraken CLI command failed ({completed.returncode}): {last_error}"
                )
            time.sleep(_retry_delay(attempt))
            continue

        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            last_error = completed.stdout.strip()[:500]
            if attempt == retries:
                raise KrakenCLIError(f"Kraken CLI returned malformed JSON: {last_error}") from exc
            time.sleep(_retry_delay(attempt))
            continue

        api_error = _api_error_message(payload)
        if api_error:
            last_error = f"Kraken API error: {api_error}"
            if attempt == retries:
                raise KrakenCLIError(last_error)
            time.sleep(_retry_delay(attempt))
            continue

        return payload

    raise KrakenCLIError(last_error or "Unknown Kraken CLI error")


def get_ohlcv(pair: str, interval: str) -> pd.DataFrame:
    payload = run_kraken(["ohlc", _spot_pair(pair), "--interval", _interval_minutes(interval)])
    rows = _extract_ohlc_rows(payload)
    frame = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    for column in ["open", "high", "low", "close", "volume"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="s", errors="coerce", utc=True)
    return frame.dropna().reset_index(drop=True)


def get_ticker(pair: str) -> dict[str, float]:
    payload = run_kraken(["ticker", _spot_pair(pair)])
    ticker = _first_market_payload(payload, pair)
    price = _first_number(ticker, ["price", "last", "c", "close"])
    high = _first_number(ticker, ["high", "h", "high_24h"])
    low = _first_number(ticker, ["low", "l", "low_24h"])
    volume = _first_number(ticker, ["volume", "v", "volume_24h"])
    open_price = _first_number(ticker, ["open", "o"], default=price)
    change_pct = ((price - open_price) / open_price * 100) if open_price else 0.0
    return {
        "price": price,
        "high_24h": high,
        "low_24h": low,
        "volume": volume,
        "change_24h": change_pct,
    }


def get_order_book(pair: str, depth: int = 10) -> dict[str, float]:
    payload = run_kraken(["orderbook", _spot_pair(pair), "--count", str(depth)])
    book = _first_market_payload(payload, pair)
    bids = book.get("bids") or book.get("bid") or []
    asks = book.get("asks") or book.get("ask") or []
    best_bid = _price_from_level(bids[0]) if bids else 0.0
    best_ask = _price_from_level(asks[0]) if asks else 0.0
    mid = (best_bid + best_ask) / 2 if best_bid and best_ask else 0.0
    spread_pct = ((best_ask - best_bid) / mid * 100) if mid else 0.0
    return {"best_bid": best_bid, "best_ask": best_ask, "spread_pct": spread_pct}


def stream_prices(pairs: Iterable[str], duration: int = 60) -> Generator[dict[str, Any], None, None]:
    command = [
        *_kraken_command(),
        "ws",
        "ticker",
        *[_display_pair(pair) for pair in pairs],
        "-o",
        "json",
    ]
    deadline = time.monotonic() + duration
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError as exc:
        raise KrakenCLIError(
            "Kraken CLI was not found. Install it before streaming or set KRAKEN_COMMAND."
        ) from exc

    try:
        while time.monotonic() < deadline:
            if process.stdout is None:
                break
            line = process.stdout.readline()
            if not line:
                if process.poll() is not None:
                    stderr = process.stderr.read() if process.stderr else ""
                    raise KrakenCLIError(f"Kraken watch exited early: {stderr.strip()}")
                time.sleep(0.1)
                continue
            try:
                tick = json.loads(line)
            except json.JSONDecodeError:
                yield {"timestamp": _now_iso(), "error": f"Malformed stream JSON: {line.strip()}"}
                continue
            if isinstance(tick, dict):
                tick.setdefault("timestamp", _now_iso())
                yield tick
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def _extract_ohlc_rows(payload: Any) -> list[list[Any]]:
    candidate = payload
    if isinstance(payload, dict):
        result = payload.get("result", payload)
        values = [value for key, value in result.items() if key.lower() != "last"]
        candidate = values[0] if values else result

    rows: list[list[Any]] = []
    for row in candidate if isinstance(candidate, list) else []:
        if isinstance(row, dict):
            rows.append([
                row.get("timestamp") or row.get("time"),
                row.get("open"),
                row.get("high"),
                row.get("low"),
                row.get("close"),
                row.get("volume") or row.get("vwap") or 0,
            ])
        elif isinstance(row, list) and len(row) >= 7:
            rows.append([row[0], row[1], row[2], row[3], row[4], row[6]])
    if not rows:
        raise KrakenCLIError("Kraken OHLC response did not contain candles.")
    return rows


def _first_market_payload(payload: Any, pair: str) -> dict[str, Any]:
    if isinstance(payload, dict) and "result" in payload:
        payload = payload["result"]
    if isinstance(payload, dict):
        if pair in payload and isinstance(payload[pair], dict):
            return payload[pair]
        for value in payload.values():
            if isinstance(value, dict):
                return value
        return payload
    raise KrakenCLIError("Kraken response did not contain market data.")


def _first_number(data: dict[str, Any], keys: list[str], default: float = 0.0) -> float:
    for key in keys:
        value = data.get(key)
        if isinstance(value, list) and value:
            value = value[0]
        if isinstance(value, dict):
            value = value.get("price") or value.get("value")
        try:
            if value is not None:
                return float(value)
        except (TypeError, ValueError):
            continue
    return default


def _price_from_level(level: Any) -> float:
    if isinstance(level, dict):
        return float(level.get("price") or level.get("p") or 0)
    if isinstance(level, list) and level:
        return float(level[0])
    return 0.0


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _api_error_message(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    error = payload.get("error")
    if isinstance(error, list) and error:
        return "; ".join(str(item) for item in error)
    if isinstance(error, str) and error:
        return error
    if payload.get("success") is False:
        return str(payload.get("message") or "Kraken CLI API request failed")
    return None


def _retry_delay(attempt: int) -> float:
    return KRAKEN_BACKOFF_SECONDS * (2**attempt)


def _kraken_command() -> list[str]:
    configured = os.environ.get("KRAKEN_COMMAND")
    if not configured and os.name == "nt" and Path("kraken.cmd").exists():
        configured = "kraken.cmd"
    configured = configured or DEFAULT_KRAKEN_COMMAND
    return shlex.split(configured, posix=os.name != "nt")


def _spot_pair(pair: str) -> str:
    return pair.replace("/", "").upper()


def _display_pair(pair: str) -> str:
    if "/" in pair:
        return pair.upper()
    pair = pair.upper()
    if pair.endswith("USD") and len(pair) > 3:
        return f"{pair[:-3]}/USD"
    return pair


def _interval_minutes(interval: str) -> str:
    normalized = str(interval).strip().lower()
    aliases = {
        "1m": "1",
        "5m": "5",
        "15m": "15",
        "30m": "30",
        "1h": "60",
        "4h": "240",
        "1d": "1440",
        "1w": "10080",
    }
    return aliases.get(normalized, normalized)
