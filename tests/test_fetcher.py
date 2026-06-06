import pandas as pd
import pytest

from agentkrak import fetcher


def test_get_ticker_parses_current_kraken_cli_shape(monkeypatch):
    monkeypatch.setattr(
        fetcher,
        "run_kraken",
        lambda args: {
            "BTCUSD": {
                "c": ["68000.0", "1.0"],
                "h": ["70000.0", "70000.0"],
                "l": ["65000.0", "65000.0"],
                "v": ["123.4", "123.4"],
                "o": "67000.0",
            }
        },
    )

    ticker = fetcher.get_ticker("BTC/USD")

    assert ticker["price"] == 68000.0
    assert ticker["high_24h"] == 70000.0
    assert ticker["low_24h"] == 65000.0
    assert ticker["volume"] == 123.4
    assert ticker["change_24h"] == pytest.approx(1.4925, rel=1e-3)


def test_get_order_book_returns_best_bid_ask_and_spread(monkeypatch):
    monkeypatch.setattr(
        fetcher,
        "run_kraken",
        lambda args: {
            "result": {
                "ETHUSD": {
                    "bids": [["3499.0", "2.0", "1"]],
                    "asks": [["3501.0", "2.0", "1"]],
                }
            }
        },
    )

    book = fetcher.get_order_book("ETH/USD")

    assert book["best_bid"] == 3499.0
    assert book["best_ask"] == 3501.0
    assert book["spread_pct"] == pytest.approx(0.05714, rel=1e-3)


def test_get_ohlcv_normalizes_kraken_rows(monkeypatch):
    monkeypatch.setattr(
        fetcher,
        "run_kraken",
        lambda args: {
            "result": {
                "SOLUSD": [
                    [1770000000, "170", "180", "165", "175", "174", "1000", 50],
                    [1770003600, "175", "181", "172", "179", "178", "1100", 60],
                ],
                "last": 1770003600,
            }
        },
    )

    frame = fetcher.get_ohlcv("SOL/USD", "1h")

    assert list(frame.columns) == ["timestamp", "open", "high", "low", "close", "volume"]
    assert isinstance(frame, pd.DataFrame)
    assert frame.iloc[-1]["close"] == 179.0
    assert frame.iloc[-1]["volume"] == 1100.0


def test_interval_and_pair_helpers_match_cli_expectations():
    assert fetcher._spot_pair("BTC/USD") == "BTCUSD"
    assert fetcher._display_pair("BTCUSD") == "BTC/USD"
    assert fetcher._interval_minutes("1h") == "60"
    assert fetcher._interval_minutes("15m") == "15"


def test_extract_ohlc_rows_rejects_empty_payload():
    with pytest.raises(fetcher.KrakenCLIError, match="did not contain candles"):
        fetcher._extract_ohlc_rows({"result": {"last": 1}})


def test_api_error_message_detects_kraken_error_payloads():
    assert fetcher._api_error_message({"error": ["EGeneral:Temporary lockout"]}) == (
        "EGeneral:Temporary lockout"
    )
    assert fetcher._api_error_message({"success": False, "message": "rate limited"}) == "rate limited"
    assert fetcher._api_error_message({"result": {"BTCUSD": {}}}) is None
