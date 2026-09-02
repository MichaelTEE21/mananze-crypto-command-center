"""Design system tokens + page shell HTML."""
from __future__ import annotations

from mccc.design_system import COLORS, NAV_ICONS, build_css, page_shell_html


def test_tokens_present():
    assert COLORS.accent.startswith("#")
    assert "dashboard" in NAV_ICONS


def test_css_hides_streamlit_chrome():
    css = build_css()
    assert "#MainMenu" in css
    assert "stSidebarNav" in css
    assert "--mccc-accent" in css
    assert "IBM Plex Sans" in css


def test_page_shell_html_escapes():
    html = page_shell_html("<script>", "why", "invest", "learn")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "What happened" in html
    assert "Why it matters" in html
    assert "Investigate" in html
    assert "Learn next" in html
