"""Pure UI helper + announcements list tests (no Streamlit render)."""
from __future__ import annotations

from mccc.announcements import create, list_published
from mccc.ui import data_mode_chip_html, status_badge_html
from mccc import __version__


def test_status_badge_html_kinds():
    html = status_badge_html("OK", "success")
    assert "mccc-badge-success" in html
    assert "OK" in html
    assert "<script>" not in status_badge_html("<script>", "danger")
    assert "&lt;script&gt;" in status_badge_html("<script>", "danger")
    assert "mccc-badge-warn" in status_badge_html("Soon", "warn")
    assert "mccc-badge-info" in status_badge_html("Note", "info")
    assert "mccc-badge-danger" in status_badge_html("Risk", "danger")


def test_data_mode_chip_html():
    live = data_mode_chip_html(True)
    demo = data_mode_chip_html(False)
    assert "LIVE" in live and "mccc-chip-live" in live
    assert "DEMO" in demo and "mccc-chip-demo" in demo
    assert live != demo


def test_version_present():
    assert __version__ == "2.3.0"


def test_list_published_announcements(db_path):
    assert list_published(db_path=db_path) == []
    create("Hello", "Body text", published=True, db_path=db_path)
    create("Draft", "Hidden", published=False, db_path=db_path)
    create("Expired", "Old", published=True, expires_at="2000-01-01T00:00:00Z", db_path=db_path)
    rows = list_published(limit=10, db_path=db_path)
    assert len(rows) == 1
    assert rows[0]["title"] == "Hello"
