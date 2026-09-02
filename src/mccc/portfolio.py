"""Portfolio CRUD + valuation helpers (local SQLite).

user_id is optional (NULL) for the local-single-user mode.
Never treat DEMO prices as live — callers pass a price map + is_live flag.
"""
from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any, Optional

from mccc.db import connect, utc_now


def add_asset(
    symbol: str,
    quantity: float,
    purchase_price: float = 0.0,
    name: str = "",
    purchase_date: str = "",
    network: str = "",
    notes: str = "",
    user_id: Optional[int] = None,
    db_path: Optional[Path] = None,
) -> int:
    symbol_n = (symbol or "").strip().upper()
    if not symbol_n:
        raise ValueError("symbol is required")
    qty = float(quantity)
    if qty < 0:
        raise ValueError("quantity must be >= 0")
    now = utc_now()
    with connect(db_path) as conn:
        cur = conn.execute(
            """INSERT INTO portfolio_assets
               (user_id, symbol, name, quantity, purchase_price, purchase_date,
                network, notes, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                symbol_n,
                (name or symbol_n).strip(),
                qty,
                float(purchase_price or 0),
                purchase_date or "",
                network or "",
                notes or "",
                now,
                now,
            ),
        )
        return int(cur.lastrowid)


def list_assets(user_id: Optional[int] = None, db_path: Optional[Path] = None) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        if user_id is None:
            rows = conn.execute(
                "SELECT * FROM portfolio_assets ORDER BY symbol ASC, id ASC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM portfolio_assets WHERE user_id=? OR user_id IS NULL ORDER BY symbol ASC, id ASC",
                (user_id,),
            ).fetchall()
        return [dict(r) for r in rows]


def get_asset(asset_id: int, db_path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM portfolio_assets WHERE id=?", (asset_id,)).fetchone()
        return dict(row) if row else None


def update_asset(asset_id: int, **fields: Any) -> None:
    db_path = fields.pop("db_path", None)
    allowed = {
        "symbol",
        "name",
        "quantity",
        "purchase_price",
        "purchase_date",
        "network",
        "notes",
        "user_id",
    }
    updates = {k: v for k, v in fields.items() if k in allowed}
    if "symbol" in updates:
        updates["symbol"] = str(updates["symbol"]).strip().upper()
    if not updates:
        return
    updates["updated_at"] = utc_now()
    cols = ", ".join(f"{k}=?" for k in updates)
    vals = list(updates.values()) + [asset_id]
    with connect(db_path) as conn:
        conn.execute(f"UPDATE portfolio_assets SET {cols} WHERE id=?", vals)


def delete_asset(asset_id: int, db_path: Optional[Path] = None) -> None:
    with connect(db_path) as conn:
        conn.execute("DELETE FROM portfolio_assets WHERE id=?", (asset_id,))


def compute_positions(
    assets: list[dict[str, Any]],
    price_map: dict[str, float],
) -> list[dict[str, Any]]:
    """Enrich assets with current value / cost / pnl using a symbol→price map.

    Missing prices yield current_price=None and pnl=None (never invented).
    """
    out: list[dict[str, Any]] = []
    for a in assets:
        row = dict(a)
        symbol = str(row.get("symbol") or "").upper()
        qty = float(row.get("quantity") or 0)
        cost_px = float(row.get("purchase_price") or 0)
        cost = qty * cost_px
        price = price_map.get(symbol)
        if price is None:
            # also try name-less aliases
            price = price_map.get(symbol.lower())  # type: ignore[assignment]
        row["cost"] = round(cost, 8)
        if price is None:
            row["current_price"] = None
            row["value"] = None
            row["pnl"] = None
            row["pnl_pct"] = None
            row["allocation"] = None
        else:
            px = float(price)
            value = qty * px
            pnl = value - cost
            row["current_price"] = px
            row["value"] = round(value, 8)
            row["pnl"] = round(pnl, 8)
            row["pnl_pct"] = round((pnl / cost * 100) if cost else (0.0 if value == 0 else None), 4) if cost else (
                0.0 if value == 0 else None
            )
        out.append(row)
    total_value = sum(r["value"] or 0 for r in out)
    for r in out:
        if r["value"] is not None and total_value > 0:
            r["allocation"] = round(r["value"] / total_value * 100, 4)
        elif r["value"] is not None:
            r["allocation"] = 0.0
    return out


def compute_summary(
    assets: list[dict[str, Any]],
    price_map: dict[str, float],
    *,
    is_live: bool = False,
) -> dict[str, Any]:
    positions = compute_positions(assets, price_map)
    priced = [p for p in positions if p["value"] is not None]
    unpriced = [p for p in positions if p["value"] is None]
    total_value = sum(p["value"] or 0 for p in priced)
    total_cost = sum(float(p.get("cost") or 0) for p in positions)
    total_pnl = sum(p["pnl"] or 0 for p in priced)
    return {
        "positions": positions,
        "total_value": round(total_value, 8),
        "total_cost": round(total_cost, 8),
        "total_pnl": round(total_pnl, 8),
        "unpriced_count": len(unpriced),
        "is_live": bool(is_live),
        "source_note": "live prices" if is_live else "DEMO or incomplete price map — not live market quotes",
    }


CSV_FIELDS = (
    "symbol",
    "name",
    "quantity",
    "purchase_price",
    "purchase_date",
    "network",
    "notes",
)


def export_csv(assets: list[dict[str, Any]]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(CSV_FIELDS), extrasaction="ignore")
    writer.writeheader()
    for a in assets:
        writer.writerow({k: a.get(k, "") for k in CSV_FIELDS})
    return buf.getvalue()


def import_csv(
    text: str,
    user_id: Optional[int] = None,
    db_path: Optional[Path] = None,
) -> list[int]:
    """Parse CSV and insert assets. Returns created ids."""
    reader = csv.DictReader(io.StringIO(text))
    ids: list[int] = []
    for row in reader:
        symbol = (row.get("symbol") or "").strip()
        if not symbol:
            continue
        qty = float(row.get("quantity") or 0)
        px = float(row.get("purchase_price") or 0)
        ids.append(
            add_asset(
                symbol=symbol,
                quantity=qty,
                purchase_price=px,
                name=row.get("name") or "",
                purchase_date=row.get("purchase_date") or "",
                network=row.get("network") or "",
                notes=row.get("notes") or "",
                user_id=user_id,
                db_path=db_path,
            )
        )
    return ids
