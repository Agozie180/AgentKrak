from agentkrak.fetcher import KrakenCLIError
from agentkrak.paper_trader import PaperTrader


def test_paper_order_initializes_account_and_retries(monkeypatch, tmp_path):
    calls = []

    def fake_run_kraken(args):
        calls.append(args)
        if args[:2] == ["paper", "buy"] and ["paper", "init"] not in calls:
            raise KrakenCLIError("Paper account not initialized")
        return {"ok": True}

    monkeypatch.setattr("agentkrak.paper_trader.run_kraken", fake_run_kraken)
    trader = PaperTrader(log_path=str(tmp_path / "trades.log"))

    trade = trader.buy({
        "timestamp": "2026-06-05T00:00:00+00:00",
        "pair": "SOL/USD",
        "current_price": 100.0,
        "signal": "BUY",
    })

    assert calls == [
        ["paper", "buy", "SOLUSD", "0.5"],
        ["paper", "init"],
        ["paper", "buy", "SOLUSD", "0.5"],
    ]
    assert trade["action"] == "BUY"


def test_paper_trader_ignores_non_tradable_filtered_signal(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr("agentkrak.paper_trader.run_kraken", lambda args: calls.append(args))
    trader = PaperTrader(log_path=str(tmp_path / "trades.log"))

    trade = trader.handle_signal({
        "timestamp": "2026-06-05T00:00:00+00:00",
        "pair": "BTC/USD",
        "current_price": 100.0,
        "signal": "NO TRADE",
        "raw_signal": "BUY",
        "confidence": 40,
        "tradable": False,
    })

    assert trade is None
    assert calls == []
