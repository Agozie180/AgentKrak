import pandas as pd

from agentkrak.signals import generate_signal


def frame(**overrides):
    data = {
        "close": [100, 99, 98],
        "rsi_14": [46, 40, 42],
        "ema_9": [99, 98, 101],
        "ema_21": [100, 99, 100],
        "macd": [-1, -0.5, 0.5],
        "macd_signal": [0, -0.25, 0],
        "bb_lower": [95, 96, 99],
        "bb_upper": [110, 109, 108],
    }
    data.update(overrides)
    return pd.DataFrame(data)


def test_buy_signal_fires_when_three_or_more_conditions_are_met():
    signal = generate_signal("BTC/USD", frame(), {"price": 98}, {"spread_pct": 0.1})

    assert signal["signal"] == "BUY"
    assert len(signal["conditions_met"]) >= 3


def test_sell_signal_fires_when_three_or_more_conditions_are_met():
    data = frame(
        close=[100, 101, 110],
        rsi_14=[58, 70, 65],
        ema_9=[101, 102, 99],
        ema_21=[100, 101, 100],
        macd=[1, 0.5, -0.5],
        macd_signal=[0, 0.25, 0],
        bb_upper=[108, 109, 110],
        bb_lower=[90, 91, 92],
    )
    signal = generate_signal("ETH/USD", data, {"price": 110}, {"spread_pct": 0.1})

    assert signal["signal"] == "SELL"
    assert len(signal["conditions_met"]) >= 3


def test_hold_signal_fires_when_fewer_than_three_conditions_are_met():
    data = frame(
        close=[100, 100, 100],
        rsi_14=[50, 50, 50],
        ema_9=[100, 100, 100],
        ema_21=[100, 100, 100],
        macd=[0, 0, 0],
        macd_signal=[0, 0, 0],
        bb_lower=[90, 90, 90],
        bb_upper=[110, 110, 110],
    )
    signal = generate_signal("SOL/USD", data, {"price": 100}, {"spread_pct": 0.1})

    assert signal["signal"] == "HOLD"
    assert signal["confidence"] == 20


def test_confidence_score_math_is_conditions_times_twenty():
    signal = generate_signal("BTC/USD", frame(), {"price": 98}, {"spread_pct": 0.1})

    assert signal["confidence"] == len(signal["conditions_met"]) * 20


def test_all_five_conditions_met_gives_100_confidence():
    signal = generate_signal("BTC/USD", frame(), {"price": 98}, {"spread_pct": 0.1})

    assert signal["confidence"] == 100
    assert len(signal["conditions_met"]) == 5


def test_threshold_filters_low_confidence_trade_to_hold():
    data = frame(close=[100, 101, 102], bb_lower=[90, 90, 90])
    signal = generate_signal(
        "BTC/USD",
        data,
        {"price": 102},
        {"spread_pct": 0.2},
        min_confidence=80,
    )

    assert signal["raw_signal"] == "BUY"
    assert signal["signal"] == "HOLD"
    assert signal["confidence"] == 60
    assert signal["tradable"] is False
    assert signal["risk_status"] == "candidate"
    assert signal["stop_loss"] is not None
    assert signal["take_profit"] is not None
    assert "Filtered below 80% confidence threshold" in signal["conditions_met"]


def test_buy_signal_includes_stop_loss_take_profit_and_risk_reward():
    signal = generate_signal(
        "BTC/USD",
        frame(),
        {"price": 100},
        {"spread_pct": 0.1},
        stop_loss_pct=0.02,
        take_profit_pct=0.04,
    )

    assert signal["tradable"] is True
    assert signal["risk_status"] == "active"
    assert signal["stop_loss"] == 98.0
    assert signal["take_profit"] == 104.0
    assert signal["risk_reward"] == 2.0


def test_sell_signal_risk_levels_are_inverted():
    data = frame(
        close=[100, 101, 110],
        rsi_14=[58, 70, 65],
        ema_9=[101, 102, 99],
        ema_21=[100, 101, 100],
        macd=[1, 0.5, -0.5],
        macd_signal=[0, 0.25, 0],
        bb_upper=[108, 109, 110],
        bb_lower=[90, 91, 92],
    )
    signal = generate_signal(
        "ETH/USD",
        data,
        {"price": 100},
        {"spread_pct": 0.1},
        stop_loss_pct=0.02,
        take_profit_pct=0.04,
    )

    assert signal["stop_loss"] == 102.0
    assert signal["take_profit"] == 96.0
