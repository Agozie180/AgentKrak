from datetime import datetime, timezone

from agentkrak.sessions import current_session


def utc(hour: int) -> datetime:
    return datetime(2026, 6, 7, hour, 0, tzinfo=timezone.utc)


def test_asian_session_crosses_midnight():
    assert current_session(utc(23)).name == "Asian"
    assert current_session(utc(2)).name == "Asian"
    assert current_session(utc(5)).min_confidence == 65


def test_london_session_threshold():
    session = current_session(utc(7))

    assert session.name == "London"
    assert session.min_confidence == 72


def test_new_york_session_threshold():
    session = current_session(utc(13))

    assert session.name == "New York"
    assert session.min_confidence == 75


def test_off_session_covers_low_liquidity_and_transition_hours():
    assert current_session(utc(21)).name == "Off"
    assert current_session(utc(6)).name == "Off"
    assert current_session(utc(12)).min_confidence == 60
