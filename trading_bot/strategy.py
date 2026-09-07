"""Trading strategy: SMA crossover entries, trailing-stop + take-profit exits.

Entry: buy when the fast SMA crosses above the slow SMA (a simple momentum
signal). Exit: whichever comes first —
  - Take-profit: price rises `take_profit_pct` above the entry price.
  - Trailing stop: price falls `trailing_stop_pct` below the highest price
    seen since entry (locks in gains as the price climbs, caps losses if it
    reverses immediately).
"""
from __future__ import annotations

from dataclasses import dataclass, field


def sma(values: list[float], window: int) -> list[float | None]:
    """Simple moving average; None where there isn't enough history yet."""
    out: list[float | None] = []
    total = 0.0
    for i, v in enumerate(values):
        total += v
        if i >= window:
            total -= values[i - window]
        out.append(total / window if i >= window - 1 else None)
    return out


@dataclass
class Position:
    entry_price: float
    quantity: float
    peak_price: float = field(init=False)

    def __post_init__(self) -> None:
        self.peak_price = self.entry_price


@dataclass
class StrategyConfig:
    fast_window: int = 10
    slow_window: int = 30
    take_profit_pct: float = 10.0
    trailing_stop_pct: float = 5.0


class SmaTrailingStopStrategy:
    """Stateful strategy: feed closes one at a time, get back a signal."""

    def __init__(self, config: StrategyConfig, history: list[float] | None = None):
        self.config = config
        self.closes: list[float] = list(history or [])
        self.position: Position | None = None

    def _current_smas(self) -> tuple[float | None, float | None]:
        fast = sma(self.closes, self.config.fast_window)
        slow = sma(self.closes, self.config.slow_window)
        return fast[-1], slow[-1]

    def _previous_smas(self) -> tuple[float | None, float | None]:
        if len(self.closes) < 2:
            return None, None
        fast = sma(self.closes[:-1], self.config.fast_window)
        slow = sma(self.closes[:-1], self.config.slow_window)
        return fast[-1], slow[-1]

    def on_price(self, price: float) -> str | None:
        """Feed the latest close. Returns 'BUY', 'SELL', or None."""
        self.closes.append(price)

        if self.position is not None:
            self.position.peak_price = max(self.position.peak_price, price)
            take_profit_price = self.position.entry_price * (
                1 + self.config.take_profit_pct / 100
            )
            stop_price = self.position.peak_price * (
                1 - self.config.trailing_stop_pct / 100
            )
            if price >= take_profit_price or price <= stop_price:
                return "SELL"
            return None

        fast_prev, slow_prev = self._previous_smas()
        fast_now, slow_now = self._current_smas()
        if None in (fast_prev, slow_prev, fast_now, slow_now):
            return None
        crossed_up = fast_prev <= slow_prev and fast_now > slow_now
        if crossed_up:
            return "BUY"
        return None

    def open_position(self, price: float, quantity: float) -> None:
        self.position = Position(entry_price=price, quantity=quantity)

    def close_position(self) -> Position:
        assert self.position is not None
        position = self.position
        self.position = None
        return position
