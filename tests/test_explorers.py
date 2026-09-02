"""Explorer registry + UNAVAILABLE honesty + security rejection."""
from __future__ import annotations

from mccc.explorers import (
    DATA_UNAVAILABLE,
    available_chains,
    get_provider,
    list_providers,
    lookup_address,
    lookup_tx,
)
from mccc.explorers.base import ExplorerStatus


def test_builtin_providers_registered():
    names = {p.chain for p in list_providers()}
    assert {"ethereum", "bitcoin", "solana"} <= names
    assert "ethereum" in available_chains()


def test_unknown_chain_unavailable():
    res = lookup_address("cosmos", "someaddr")
    assert res.status == ExplorerStatus.UNAVAILABLE
    assert res.label == "UNAVAILABLE"


def test_reject_seed_on_explorer():
    mnemonic = (
        "abandon abandon abandon abandon abandon abandon "
        "abandon abandon abandon abandon abandon about"
    )
    res = lookup_address("ethereum", mnemonic)
    assert res.status == ExplorerStatus.UNAVAILABLE
    low = res.summary.lower()
    assert ("seed" in low) or ("credential" in low) or ("sensitive" in low)


def test_eth_demo_address_labelled():
    res = lookup_address("ethereum", "0xDEMOdeadbeef")
    assert res.label in ("DEMO", "UNAVAILABLE", "VERIFIED")
    assert res.kind == "address"


def test_solana_tx_unavailable_honest():
    res = lookup_tx(
        "solana",
        "FakeSignature111111111111111111111111111111111111111111111111111",
    )
    assert res.status == ExplorerStatus.UNAVAILABLE
    assert res.label == "UNAVAILABLE"
    assert DATA_UNAVAILABLE.split()[0] in res.summary or "UNAVAILABLE" in res.summary


def test_get_provider():
    assert get_provider("ethereum") is not None
    assert get_provider("nope") is None
