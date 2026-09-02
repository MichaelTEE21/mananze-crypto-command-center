"""Market provider shape + DEMO labelling."""
from __future__ import annotations

from mccc.market_provider import CoinGeckoProvider, clear_market_cache


def test_price_map_shape():
    clear_market_cache()
    p = CoinGeckoProvider(ttl_seconds=60, timeout=3.0)
    mapping, source, is_live = p.price_map(ids="bitcoin,ethereum")
    assert isinstance(mapping, dict)
    assert isinstance(source, str)
    assert isinstance(is_live, bool)
    # At least one symbol when DEMO or live
    assert len(mapping) >= 1


def test_overview_flags():
    clear_market_cache()
    p = CoinGeckoProvider(ttl_seconds=60, timeout=3.0)
    overview, source, is_live = p.get_overview()
    assert "btc" in overview
    assert isinstance(is_live, bool)
    if not is_live:
        assert "DEMO" in source or "demo" in source.lower() or "unreachable" in source.lower()
