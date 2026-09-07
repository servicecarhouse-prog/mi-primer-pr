"""Market data helpers backed by Binance's public REST API.

Only public (unauthenticated) endpoints are used here — no API key,
secret, or account access is required or accepted. This module can
fetch historical candles for backtesting and the latest price for the
paper-trading loop.
"""
from __future__ import annotations

import requests

BASE_URL = "https://api.binance.com"


def get_klines(symbol: str, interval: str = "1h", limit: int = 500) -> list[dict]:
    """Fetch historical candlesticks (klines) for a symbol.

    Returns a list of dicts with open_time, open, high, low, close, volume,
    ordered oldest to newest.
    """
    resp = requests.get(
        f"{BASE_URL}/api/v3/klines",
        params={"symbol": symbol, "interval": interval, "limit": limit},
        timeout=10,
    )
    resp.raise_for_status()
    raw = resp.json()
    return [
        {
            "open_time": row[0],
            "open": float(row[1]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4]),
            "volume": float(row[5]),
        }
        for row in raw
    ]


def get_last_price(symbol: str) -> float:
    """Fetch the current market price for a symbol."""
    resp = requests.get(
        f"{BASE_URL}/api/v3/ticker/price",
        params={"symbol": symbol},
        timeout=10,
    )
    resp.raise_for_status()
    return float(resp.json()["price"])
