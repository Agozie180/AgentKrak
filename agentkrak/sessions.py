from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class TradingSession:
    name: str
    min_confidence: int
    note: str


ASIAN_SESSION = TradingSession("Asian", 65, "trending moves, cleaner signals")
LONDON_SESSION = TradingSession("London", 72, "high volatility, false breaks possible")
NEW_YORK_SESSION = TradingSession("New York", 75, "highest volume, needs strong confirmation")
OFF_SESSION = TradingSession("Off", 60, "low liquidity, trade carefully")


def current_session(now: datetime | None = None) -> TradingSession:
    moment = now or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    utc_hour = moment.astimezone(timezone.utc).hour

    if utc_hour >= 23 or utc_hour < 6:
        return ASIAN_SESSION
    if 7 <= utc_hour < 12:
        return LONDON_SESSION
    if 13 <= utc_hour < 21:
        return NEW_YORK_SESSION
    return OFF_SESSION


def session_summary(session: TradingSession | None = None) -> str:
    active = session or current_session()
    return f"{active.name} session | min confidence {active.min_confidence}% | {active.note}"
