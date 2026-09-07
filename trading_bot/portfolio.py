"""Virtual portfolio for paper trading — no real money or exchange account
is ever touched. It just keeps track of a simulated cash/asset balance so
the strategy's performance can be measured."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Trade:
    side: str  # "BUY" or "SELL"
    price: float
    quantity: float
    timestamp: str
    pnl_pct: float | None = None


@dataclass
class Portfolio:
    cash: float
    quantity: float = 0.0
    trades: list[Trade] = field(default_factory=list)

    def buy(self, price: float, timestamp: str) -> Trade:
        quantity = self.cash / price
        self.quantity = quantity
        self.cash = 0.0
        trade = Trade(side="BUY", price=price, quantity=quantity, timestamp=timestamp)
        self.trades.append(trade)
        return trade

    def sell(self, price: float, timestamp: str) -> Trade:
        entry_trade = next(t for t in reversed(self.trades) if t.side == "BUY")
        pnl_pct = (price - entry_trade.price) / entry_trade.price * 100
        self.cash = self.quantity * price
        quantity_sold = self.quantity
        self.quantity = 0.0
        trade = Trade(
            side="SELL",
            price=price,
            quantity=quantity_sold,
            timestamp=timestamp,
            pnl_pct=pnl_pct,
        )
        self.trades.append(trade)
        return trade

    def equity(self, last_price: float) -> float:
        return self.cash + self.quantity * last_price
