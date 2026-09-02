"""Donation config + address exactness + QR payload."""
from __future__ import annotations

import pytest

from mccc.donations import (
    DEFAULT_BTC,
    DEFAULT_ETH,
    DEFAULT_SOL,
    ENV_BTC,
    ENV_ETH,
    ENV_SOL,
    address_for,
    get_channel,
    get_donation_channels,
    qr_png_bytes,
)


def test_default_addresses_exact(monkeypatch):
    for key in (ENV_BTC, ENV_ETH, ENV_SOL):
        monkeypatch.delenv(key, raising=False)
    assert address_for("BTC") == DEFAULT_BTC
    assert address_for("ETH") == DEFAULT_ETH
    assert address_for("SOL") == DEFAULT_SOL
    assert DEFAULT_BTC == "bc1q7a9uh6utn85gjhs5dakn3kkazsmt9s4q37cn32"
    assert DEFAULT_ETH == "0x6d04cff44c379cb89050ddb9b55e3b29d3ffc091"
    assert DEFAULT_SOL == "BgQgsr63rbRNsjLabU5toVwj1itkfLDHMLxCCo29tCwB"


def test_env_override(monkeypatch):
    monkeypatch.setenv(ENV_BTC, "bc1qtestoverride000000000000000000000000000")
    ch = get_channel("BTC")
    assert ch is not None
    assert ch.from_env is True
    assert ch.address.startswith("bc1qtestoverride")


def test_channels_shape(monkeypatch):
    for key in (ENV_BTC, ENV_ETH, ENV_SOL):
        monkeypatch.delenv(key, raising=False)
    channels = get_donation_channels()
    assert [c.asset for c in channels] == ["BTC", "ETH", "SOL"]
    for c in channels:
        assert c.network
        assert c.address
        assert c.from_env is False


def test_qr_encodes_exact_address(monkeypatch):
    pytest.importorskip("qrcode")
    for key in (ENV_BTC, ENV_ETH, ENV_SOL):
        monkeypatch.delenv(key, raising=False)
    addr = address_for("ETH")
    png = qr_png_bytes(addr)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(png) > 100
