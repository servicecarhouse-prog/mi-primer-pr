"""Paper-trading bot: SMA-crossover entries + trailing-stop/take-profit exits.

IMPORTANT: This bot only ever simulates trades against a virtual balance.
It is NOT connected to any broker, exchange account, or real money. It
reads public, unauthenticated market data from Binance to make its
decisions realistic, but nothing it does can place a real order.

Usage:
    python bot.py backtest --symbol BTCUSDT --interval 1h --limit 500
    python bot.py paper --symbol BTCUSDT --interval 1m --iterations 60 --sleep 5
"""
from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone

from data_feed import get_klines, get_last_price
from portfolio import Portfolio
from strategy import SmaTrailingStopStrategy, StrategyConfig


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_backtest(args: argparse.Namespace) -> None:
    klines = get_klines(args.symbol, interval=args.interval, limit=args.limit)
    closes = [k["close"] for k in klines]
    times = [
        datetime.fromtimestamp(k["open_time"] / 1000, tz=timezone.utc).isoformat(
            timespec="seconds"
        )
        for k in klines
    ]

    config = StrategyConfig(
        fast_window=args.fast_window,
        slow_window=args.slow_window,
        take_profit_pct=args.take_profit_pct,
        trailing_stop_pct=args.trailing_stop_pct,
    )
    strategy = SmaTrailingStopStrategy(config)
    portfolio = Portfolio(cash=args.initial_balance)

    warmup = args.slow_window
    for i in range(warmup, len(closes)):
        window = closes[: i + 1]
        strategy.closes = window[:-1]
        signal = strategy.on_price(closes[i])
        price, ts = closes[i], times[i]

        if signal == "BUY" and portfolio.quantity == 0:
            trade = portfolio.buy(price, ts)
            strategy.open_position(price, trade.quantity)
            print(f"[{ts}] BUY  @ {price:.2f}  qty={trade.quantity:.6f}")
        elif signal == "SELL" and portfolio.quantity > 0:
            trade = portfolio.sell(price, ts)
            strategy.close_position()
            print(f"[{ts}] SELL @ {price:.2f}  pnl={trade.pnl_pct:+.2f}%")

    final_price = closes[-1]
    equity = portfolio.equity(final_price)
    print_summary(args.initial_balance, equity, portfolio)


def run_paper(args: argparse.Namespace) -> None:
    seed_klines = get_klines(args.symbol, interval=args.interval, limit=args.slow_window + 5)
    seed_closes = [k["close"] for k in seed_klines]

    config = StrategyConfig(
        fast_window=args.fast_window,
        slow_window=args.slow_window,
        take_profit_pct=args.take_profit_pct,
        trailing_stop_pct=args.trailing_stop_pct,
    )
    strategy = SmaTrailingStopStrategy(config, history=seed_closes)
    portfolio = Portfolio(cash=args.initial_balance)

    print(
        f"Paper trading {args.symbol} | balance=${args.initial_balance:.2f} "
        f"| take_profit={args.take_profit_pct}% | trailing_stop={args.trailing_stop_pct}% "
        f"(SIMULATED — no real orders are placed)"
    )

    last_price = seed_closes[-1]
    for _ in range(args.iterations):
        price = get_last_price(args.symbol)
        ts = now_iso()
        signal = strategy.on_price(price)

        if signal == "BUY" and portfolio.quantity == 0:
            trade = portfolio.buy(price, ts)
            strategy.open_position(price, trade.quantity)
            print(f"[{ts}] BUY  @ {price:.2f}  qty={trade.quantity:.6f}")
        elif signal == "SELL" and portfolio.quantity > 0:
            trade = portfolio.sell(price, ts)
            strategy.close_position()
            print(f"[{ts}] SELL @ {price:.2f}  pnl={trade.pnl_pct:+.2f}%")
        else:
            print(f"[{ts}] price={price:.2f}  equity=${portfolio.equity(price):.2f}")

        last_price = price
        time.sleep(args.sleep)

    print_summary(args.initial_balance, portfolio.equity(last_price), portfolio)


def print_summary(initial_balance: float, final_equity: float, portfolio: Portfolio) -> None:
    pnl = final_equity - initial_balance
    pnl_pct = pnl / initial_balance * 100
    closed = [t for t in portfolio.trades if t.side == "SELL"]
    wins = [t for t in closed if t.pnl_pct and t.pnl_pct > 0]
    print("\n--- Resumen (SIMULADO) ---")
    print(f"Balance inicial: ${initial_balance:.2f}")
    print(f"Equity final:    ${final_equity:.2f}")
    print(f"P&L:             ${pnl:+.2f} ({pnl_pct:+.2f}%)")
    print(f"Operaciones cerradas: {len(closed)}  |  Ganadoras: {len(wins)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["backtest", "paper"])
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--limit", type=int, default=500, help="backtest: candles to fetch")
    parser.add_argument("--iterations", type=int, default=30, help="paper: loop iterations")
    parser.add_argument("--sleep", type=float, default=5.0, help="paper: seconds between checks")
    parser.add_argument("--initial-balance", type=float, default=1000.0, dest="initial_balance")
    parser.add_argument("--fast-window", type=int, default=10, dest="fast_window")
    parser.add_argument("--slow-window", type=int, default=30, dest="slow_window")
    parser.add_argument("--take-profit-pct", type=float, default=10.0, dest="take_profit_pct")
    parser.add_argument("--trailing-stop-pct", type=float, default=5.0, dest="trailing_stop_pct")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.mode == "backtest":
        run_backtest(args)
    else:
        run_paper(args)


if __name__ == "__main__":
    main()
