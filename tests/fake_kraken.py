from __future__ import annotations

import json
import sys
import time


def main() -> int:
    args = [arg for arg in sys.argv[1:] if arg not in {"-o", "json"}]
    if not args:
        return error("missing command")

    command = args[0]
    if command == "ticker":
        pair = args[1] if len(args) > 1 else "BTCUSD"
        price = price_for(pair)
        return emit({
            pair: {
                "c": [str(price), "1.0"],
                "h": [str(price * 1.03), str(price * 1.03)],
                "l": [str(price * 0.97), str(price * 0.97)],
                "v": ["1234.5", "1234.5"],
                "o": str(price * 0.99),
            }
        })

    if command == "ohlc":
        pair = args[1] if len(args) > 1 else "BTCUSD"
        return emit({"result": {pair: ohlc_rows(price_for(pair)), "last": 1}})

    if command == "orderbook":
        pair = args[1] if len(args) > 1 else "BTCUSD"
        price = price_for(pair)
        half_spread = price * 0.0003
        return emit({
            "result": {
                pair: {
                    "bids": [[str(price - half_spread), "2.0", "1"]],
                    "asks": [[str(price + half_spread), "2.0", "1"]],
                }
            }
        })

    if command == "paper" and len(args) >= 4 and args[1] in {"buy", "sell"}:
        return emit({
            "mode": "paper",
            "status": "filled",
            "action": args[1],
            "pair": args[2],
            "volume": args[3],
        })

    if command == "ws" and len(args) >= 2 and args[1] == "ticker":
        pairs = args[2:] or ["BTC/USD"]
        deadline = time.monotonic() + 3
        tick = 0
        while time.monotonic() < deadline:
            for pair in pairs:
                print(json.dumps({
                    "channel": "ticker",
                    "data": [{"symbol": pair, "last": price_for(pair) + tick}],
                }), flush=True)
            tick += 1
            time.sleep(0.25)
        return 0

    return error(f"unsupported fake kraken command: {' '.join(args)}")


def price_for(pair: str) -> float:
    normalized = pair.replace("/", "").upper()
    if normalized.startswith("ETH"):
        return 3500.0
    if normalized.startswith("SOL"):
        return 175.0
    return 68000.0


def ohlc_rows(price: float) -> list[list[object]]:
    rows = []
    start = 1_770_000_000
    for idx in range(30):
        close = price
        if idx == 28:
            close = price * 0.90
        if idx == 29:
            close = price * 0.91
        rows.append([
            start + idx * 3600,
            str(close * 1.002),
            str(close * 1.01),
            str(close * 0.99),
            str(close),
            str(close),
            "100.0",
            10,
        ])
    return rows


def emit(payload: object) -> int:
    print(json.dumps(payload))
    return 0


def error(message: str) -> int:
    print(json.dumps({"error": "validation", "message": message}))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
