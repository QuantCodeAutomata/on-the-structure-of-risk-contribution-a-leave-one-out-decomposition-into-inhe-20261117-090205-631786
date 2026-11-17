"""Shared pytest fixtures: market-data marker and a cached reduced data slice."""
from __future__ import annotations

import os

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "market_data: test needs a live QuantX Dataloader / Massive call"
    )


@pytest.fixture(scope="session")
def reduced_price_panel(request: pytest.FixtureRequest):
    """A few instruments, a short window, loaded once through data/data_loader.py."""
    if not os.environ.get("DATALOADER_API_KEY"):
        pytest.skip("DATALOADER_API_KEY not set")
    cache_dir = request.config.cache.mkdir("reduced_price_panel")
    cache_file = cache_dir / "panel.pkl"
    import pandas as pd

    if cache_file.exists():
        return pd.read_pickle(cache_file)

    from data.data_loader import load_price_panel

    tickers = {"CL1 Comdty": "USO", "ES1 Index": "SPY", "TY1 Comdty": "IEF"}
    prices, returns, meta = load_price_panel(tickers, "2022-01-01", "2023-12-31")
    result = (prices, returns, meta)
    pd.to_pickle(result, cache_file)
    return result
