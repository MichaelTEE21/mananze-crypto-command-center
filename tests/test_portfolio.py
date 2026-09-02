"""Portfolio CRUD + valuation + CSV helpers."""
from __future__ import annotations

from mccc.portfolio import (
    add_asset,
    compute_summary,
    delete_asset,
    export_csv,
    import_csv,
    list_assets,
    update_asset,
)


def test_asset_crud(db_path):
    aid = add_asset("eth", 2.0, purchase_price=2000.0, name="Ethereum", db_path=db_path)
    assert aid > 0
    rows = list_assets(db_path=db_path)
    hit = next(r for r in rows if r["id"] == aid)
    assert hit["symbol"] == "ETH"
    assert hit["quantity"] == 2.0
    update_asset(aid, quantity=3.0, db_path=db_path)
    hit2 = next(r for r in list_assets(db_path=db_path) if r["id"] == aid)
    assert hit2["quantity"] == 3.0
    delete_asset(aid, db_path=db_path)
    assert all(r["id"] != aid for r in list_assets(db_path=db_path))


def test_compute_summary_pnl_and_allocation(db_path):
    add_asset("BTC", 1.0, purchase_price=50000.0, db_path=db_path)
    add_asset("ETH", 10.0, purchase_price=2000.0, db_path=db_path)
    assets = list_assets(db_path=db_path)
    price_map = {"BTC": 60000.0, "ETH": 2500.0}
    summary = compute_summary(assets, price_map, is_live=True)
    assert summary["is_live"] is True
    assert summary["total_value"] == 60000.0 + 25000.0
    assert summary["total_cost"] == 50000.0 + 20000.0
    assert summary["total_pnl"] == 15000.0
    allocs = [p["allocation"] for p in summary["positions"]]
    assert abs(sum(allocs) - 100.0) < 0.01


def test_missing_prices_not_invented(db_path):
    add_asset("XYZ", 5.0, purchase_price=10.0, db_path=db_path)
    summary = compute_summary(list_assets(db_path=db_path), {}, is_live=False)
    assert summary["is_live"] is False
    assert summary["unpriced_count"] == 1
    assert summary["positions"][0]["value"] is None
    assert "DEMO" in summary["source_note"] or "not live" in summary["source_note"].lower()


def test_csv_roundtrip(db_path):
    add_asset("SOL", 40.0, purchase_price=100.0, network="solana", notes="demo", db_path=db_path)
    csv_text = export_csv(list_assets(db_path=db_path))
    assert "SOL" in csv_text
    # wipe and re-import into same db (adds more rows)
    ids = import_csv(csv_text, db_path=db_path)
    assert len(ids) >= 1
    assert any(a["symbol"] == "SOL" for a in list_assets(db_path=db_path))
