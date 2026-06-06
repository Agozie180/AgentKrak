from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .config import SIGNALS_LOG


SIGNAL_FIELDS = [
    "timestamp",
    "pair",
    "current_price",
    "rsi",
    "signal",
    "raw_signal",
    "confidence",
    "min_confidence",
    "tradable",
    "risk_status",
    "stop_loss",
    "take_profit",
    "risk_reward",
    "conditions_met",
]


def log_signal(signal: dict[str, Any], path: str = SIGNALS_LOG) -> None:
    file_path = Path(path)
    write_header = not file_path.exists()
    row = signal.copy()
    row["conditions_met"] = "; ".join(row.get("conditions_met", []))
    with file_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SIGNAL_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in SIGNAL_FIELDS})
