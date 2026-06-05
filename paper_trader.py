from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import RISK_PER_TRADE, TRADES_LOG
from .fetcher import KrakenCLIError, _spot_pair, run_kraken


TRADE_FIELDS = ["timestamp", "pair", "action", "amount", "price", "pnl", "total_pnl", "win_rate"]


@dataclass
class PaperTrader:
    capital: float = 1000.0
    log_path: str = TRADES_LOG
    positions: dict[str, dict[str, float]] = field(default_factory=dict)
    total_pnl: float = 0.0
    wins: int = 0
    losses: int = 0
    total_trades: int = 0

    def handle_signal(self, signal: dict[str, Any]) -> dict[str, Any] | None:
        action = signal["signal"]
        if action not in {"BUY", "SELL"}:
            return None
        if action == "BUY":
            return self.buy(signal)
        return self.sell(signal)

    def buy(self, signal: dict[str, Any]) -> dict[str, Any]:
        pair = signal["pair"]
        price = float(signal["current_price"])
        notional = self.capital * RISK_PER_TRADE
        amount = round(notional / price, 8) if price else 0.0
        self._run_paper_order("buy", pair, amount)
        self.positions[pair] = {"entry_price": price, "amount": amount}
        self.total_trades += 1
        trade = self._trade_row(signal, "BUY", amount, price, 0.0)
        self._log_trade(trade)
        return trade

    def sell(self, signal: dict[str, Any]) -> dict[str, Any]:
        pair = signal["pair"]
        price = float(signal["current_price"])
        position = self.positions.get(pair)
        if position:
            amount = position["amount"]
            pnl = (price - position["entry_price"]) * amount
        else:
            amount = round((self.capital * RISK_PER_TRADE) / price, 8) if price else 0.0
            pnl = 0.0
        self._run_paper_order("sell", pair, amount)
        self.positions.pop(pair, None)
        self.total_trades += 1
        self.total_pnl += pnl
        self.capital += pnl
        if pnl >= 0:
            self.wins += 1
        else:
            self.losses += 1
        trade = self._trade_row(signal, "SELL", amount, price, pnl)
        self._log_trade(trade)
        return trade

    def summary(self) -> dict[str, Any]:
        closed_trades = self.wins + self.losses
        win_rate = (self.wins / closed_trades * 100) if closed_trades else 0.0
        return {
            "total_trades": self.total_trades,
            "wins": self.wins,
            "losses": self.losses,
            "win_rate": round(win_rate, 2),
            "total_pnl": round(self.total_pnl, 2),
        }

    def _trade_row(
        self,
        signal: dict[str, Any],
        action: str,
        amount: float,
        price: float,
        pnl: float,
    ) -> dict[str, Any]:
        summary = self.summary()
        return {
            "timestamp": signal["timestamp"],
            "pair": signal["pair"],
            "action": action,
            "amount": amount,
            "price": price,
            "pnl": round(pnl, 2),
            "total_pnl": summary["total_pnl"],
            "win_rate": summary["win_rate"],
        }

    def _log_trade(self, trade: dict[str, Any]) -> None:
        path = Path(self.log_path)
        write_header = not path.exists()
        with path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=TRADE_FIELDS)
            if write_header:
                writer.writeheader()
            writer.writerow({field: trade.get(field, "") for field in TRADE_FIELDS})

    def _run_paper_order(self, side: str, pair: str, amount: float) -> None:
        args = ["paper", side, _spot_pair(pair), str(amount)]
        try:
            run_kraken(args)
        except KrakenCLIError as exc:
            if "not initialized" not in str(exc).lower():
                raise
            run_kraken(["paper", "init"])
            run_kraken(args)


def read_trade_summary(path: str = TRADES_LOG) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        return {"total_trades": 0, "wins": 0, "losses": 0, "win_rate": 0.0, "total_pnl": 0.0}
    rows = list(csv.DictReader(file_path.open(encoding="utf-8")))
    sells = [row for row in rows if row.get("action") == "SELL"]
    wins = sum(1 for row in sells if float(row.get("pnl") or 0) >= 0)
    losses = len(sells) - wins
    total_pnl = float(rows[-1].get("total_pnl") or 0) if rows else 0.0
    win_rate = (wins / len(sells) * 100) if sells else 0.0
    return {
        "total_trades": len(rows),
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 2),
        "total_pnl": round(total_pnl, 2),
    }


def safe_handle_trade(trader: PaperTrader, signal: dict[str, Any]) -> dict[str, Any] | None:
    try:
        return trader.handle_signal(signal)
    except KrakenCLIError as exc:
        return {"error": str(exc), "pair": signal.get("pair"), "action": signal.get("signal")}
