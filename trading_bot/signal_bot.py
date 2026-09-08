"""Single-shot signal check, meant to be run on a schedule (e.g. by a CI
job that has real internet access, since this repo may also be used from
sandboxes that don't).

Each run:
  1. Loads the last simulated position (if any) from state.json.
  2. Fetches recent closes and asks the strategy for a signal.
  3. Appends a line to signals.log describing what happened.
  4. Saves the updated state back to state.json.

Nothing here places a real order anywhere — it only simulates a position
in state.json so the strategy's trailing-stop/take-profit logic has
something to track between runs.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from data_feed import get_klines
from strategy import Position, SmaTrailingStopStrategy, StrategyConfig

STATE_FILE = Path(__file__).parent / "state.json"
LOG_FILE = Path(__file__).parent / "signals.log"


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"in_position": False, "entry_price": None, "peak_price": None}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def log_line(line: str) -> None:
    with LOG_FILE.open("a") as f:
        f.write(line + "\n")
    print(line)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="15m")
    parser.add_argument("--fast-window", type=int, default=10, dest="fast_window")
    parser.add_argument("--slow-window", type=int, default=30, dest="slow_window")
    parser.add_argument("--take-profit-pct", type=float, default=10.0, dest="take_profit_pct")
    parser.add_argument("--trailing-stop-pct", type=float, default=5.0, dest="trailing_stop_pct")
    args = parser.parse_args()

    config = StrategyConfig(
        fast_window=args.fast_window,
        slow_window=args.slow_window,
        take_profit_pct=args.take_profit_pct,
        trailing_stop_pct=args.trailing_stop_pct,
    )

    klines = get_klines(args.symbol, interval=args.interval, limit=args.slow_window + 5)
    closes = [k["close"] for k in klines]

    state = load_state()
    strategy = SmaTrailingStopStrategy(config, history=closes[:-1])
    if state["in_position"]:
        strategy.position = Position(entry_price=state["entry_price"], quantity=1.0)
        strategy.position.peak_price = state["peak_price"]

    price = closes[-1]
    signal = strategy.on_price(price)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")

    if signal == "BUY":
        state = {"in_position": True, "entry_price": price, "peak_price": price}
        log_line(f"[{ts}] {args.symbol} price={price:.2f}  -> SEÑAL: COMPRA")
    elif signal == "SELL":
        entry = state["entry_price"]
        pnl_pct = (price - entry) / entry * 100
        state = {"in_position": False, "entry_price": None, "peak_price": None}
        log_line(f"[{ts}] {args.symbol} price={price:.2f}  -> SEÑAL: VENDE (pnl={pnl_pct:+.2f}%)")
    else:
        if state["in_position"]:
            state["peak_price"] = max(state["peak_price"], price)
            status = f"en posición desde {state['entry_price']:.2f}"
        else:
            status = "sin posición"
        log_line(f"[{ts}] {args.symbol} price={price:.2f}  -> sin señal ({status})")

    save_state(state)


if __name__ == "__main__":
    main()
