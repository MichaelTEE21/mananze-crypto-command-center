"""MCCC design system — tokens + CSS for a premium crypto intelligence terminal.

UI layer only. Does not invent chain data or touch secrets.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ColorTokens:
    bg: str = "#070b10"
    bg_elevated: str = "#0c1219"
    panel: str = "#101820"
    panel_2: str = "#0e1520"
    border: str = "#1c2a3a"
    border_soft: str = "#162030"
    text: str = "#e8eef5"
    text_secondary: str = "#b7c2ce"
    muted: str = "#8b9aab"
    accent: str = "#00d4aa"
    accent_dim: str = "#00a884"
    success: str = "#3dffb5"
    warn: str = "#ffb020"
    danger: str = "#ff6b6b"
    info: str = "#5eb3ff"
    pro: str = "#c4a0ff"
    chart_grid: str = "#1a2430"


@dataclass(frozen=True)
class TypeTokens:
    sans: str = "'IBM Plex Sans', system-ui, sans-serif"
    mono: str = "'JetBrains Mono', ui-monospace, monospace"
    size_xs: str = "0.68rem"
    size_sm: str = "0.78rem"
    size_md: str = "0.9rem"
    size_lg: str = "1.05rem"
    size_xl: str = "1.35rem"
    size_hero: str = "1.55rem"


@dataclass(frozen=True)
class SpaceTokens:
    xs: str = "0.25rem"
    sm: str = "0.45rem"
    md: str = "0.75rem"
    lg: str = "1.1rem"
    xl: str = "1.6rem"
    radius_sm: str = "6px"
    radius_md: str = "10px"
    radius_lg: str = "14px"


COLORS = ColorTokens()
TYPE = TypeTokens()
SPACE = SpaceTokens()

# Sparse nav icons — valid Streamlit emoji subset; keep minimal
NAV_ICONS = {
    "dashboard": "🏠",
    "explore": "🔍",
    "wallets": "👛",
    "onchain": "🔎",
    "analytics": "📊",
    "analyst": "🤖",
    "academy": "📘",
    "projects": "📁",
    "watchlist": "⭐",
    "support": "💜",
}


def build_css() -> str:
    c, t, s = COLORS, TYPE, SPACE
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

:root {{
  --mccc-bg: {c.bg};
  --mccc-bg-elevated: {c.bg_elevated};
  --mccc-panel: {c.panel};
  --mccc-panel-2: {c.panel_2};
  --mccc-border: {c.border};
  --mccc-border-soft: {c.border_soft};
  --mccc-text: {c.text};
  --mccc-text-secondary: {c.text_secondary};
  --mccc-muted: {c.muted};
  --mccc-accent: {c.accent};
  --mccc-accent-dim: {c.accent_dim};
  --mccc-success: {c.success};
  --mccc-warn: {c.warn};
  --mccc-danger: {c.danger};
  --mccc-info: {c.info};
  --mccc-pro: {c.pro};
  --mccc-radius: {s.radius_md};
  --mccc-font: {t.sans};
  --mccc-mono: {t.mono};
}}

/* --- Hide default Streamlit chrome aggressively --- */
#MainMenu {{visibility: hidden; height: 0;}}
header[data-testid="stHeader"] {{background: transparent;}}
header [data-testid="stToolbar"] {{visibility: hidden; height: 0;}}
div[data-testid="stDecoration"] {{display: none !important;}}
footer {{visibility: hidden; height: 0;}}
div[data-testid="stStatusWidget"] {{visibility: hidden;}}
section.main > div {{padding-top: 0.6rem;}}

html, body, [class*="css"], .stApp {{
  font-family: var(--mccc-font);
  color: var(--mccc-text);
  background: var(--mccc-bg) !important;
}}
.stApp {{
  background: radial-gradient(1200px 600px at 10% -10%, #0d1a22 0%, var(--mccc-bg) 55%) !important;
}}

/* Inputs / buttons — fintech density */
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stSelectbox"] > div {{
  background: var(--mccc-panel-2) !important;
  border: 1px solid var(--mccc-border-soft) !important;
  border-radius: {s.radius_sm} !important;
  color: var(--mccc-text) !important;
  font-size: {t.size_md} !important;
}}
div[data-testid="stButton"] button {{
  border-radius: {s.radius_sm} !important;
  font-weight: 600 !important;
  letter-spacing: 0.02em;
  border: 1px solid var(--mccc-border) !important;
}}
div[data-testid="stButton"] button[kind="primary"] {{
  background: linear-gradient(180deg, var(--mccc-accent) 0%, var(--mccc-accent-dim) 100%) !important;
  color: #04110c !important;
  border: none !important;
}}

/* Sidebar terminal rail */
div[data-testid="stSidebar"] {{
  background: var(--mccc-bg-elevated) !important;
  border-right: 1px solid var(--mccc-border-soft);
  min-width: 15.5rem;
}}
div[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
div[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span {{
  font-size: {t.size_sm};
}}
div[data-testid="stSidebarNav"] {{display: none !important;}} /* hide default page list — custom nav */

.mccc-hero {{
  background: linear-gradient(135deg, #0a1018 0%, #12202b 42%, #0c221c 100%);
  border: 1px solid var(--mccc-border-soft);
  border-radius: {s.radius_lg};
  padding: {s.md} {s.lg};
  margin-bottom: {s.md};
  box-shadow: 0 10px 36px rgba(0,0,0,0.4);
}}
.mccc-hero h1 {{
  margin: 0;
  font-size: {t.size_hero};
  letter-spacing: 0.03em;
  color: var(--mccc-text);
  font-weight: 700;
}}
.mccc-hero .tag {{
  color: var(--mccc-accent);
  font-family: var(--mccc-mono);
  font-size: {t.size_sm};
  margin-top: 0.3rem;
}}
.mccc-hero .sub {{
  color: var(--mccc-muted);
  margin-top: 0.35rem;
  font-size: {t.size_md};
  max-width: 52rem;
  line-height: 1.45;
}}

.mccc-shell-grid {{
  display: grid;
  grid-template-columns: 1fr;
  gap: {s.md};
  margin: {s.sm} 0 {s.lg};
}}
.mccc-shell-block {{
  background: var(--mccc-panel);
  border: 1px solid var(--mccc-border-soft);
  border-radius: var(--mccc-radius);
  padding: {s.md} {s.lg};
}}
.mccc-shell-block h4 {{
  margin: 0 0 {s.xs};
  font-size: {t.size_xs};
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--mccc-accent);
  font-family: var(--mccc-mono);
}}
.mccc-shell-block p {{
  margin: 0;
  color: var(--mccc-text-secondary);
  font-size: {t.size_md};
  line-height: 1.45;
}}

.mccc-section-header {{
  margin: {s.md} 0 {s.sm};
  padding-bottom: {s.sm};
  border-bottom: 1px solid var(--mccc-border-soft);
}}
.mccc-section-header h3 {{
  margin: 0;
  font-size: {t.size_lg};
  color: var(--mccc-text);
  letter-spacing: 0.02em;
}}
.mccc-section-header .sub {{
  color: var(--mccc-muted);
  font-size: {t.size_sm};
  margin-top: 0.2rem;
}}

.mccc-card, .mccc-card-dense {{
  background: var(--mccc-panel);
  border: 1px solid var(--mccc-border-soft);
  border-radius: var(--mccc-radius);
  padding: {s.md};
  margin-bottom: {s.sm};
  box-shadow: 0 4px 18px rgba(0,0,0,0.22);
}}
.mccc-card-dense {{ padding: {s.sm} {s.md}; }}

.mccc-metric {{
  font-family: var(--mccc-mono);
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--mccc-text);
  letter-spacing: 0.01em;
}}
.mccc-metric-label {{
  color: var(--mccc-muted);
  font-size: {t.size_sm};
  margin-top: 0.15rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}}
.mccc-metric-delta-up {{ color: var(--mccc-success); font-size: {t.size_sm}; font-family: var(--mccc-mono); }}
.mccc-metric-delta-down {{ color: var(--mccc-danger); font-size: {t.size_sm}; font-family: var(--mccc-mono); }}
.mccc-metric-delta-flat {{ color: var(--mccc-muted); font-size: {t.size_sm}; font-family: var(--mccc-mono); }}
.mccc-explainer {{
  color: var(--mccc-muted);
  font-size: {t.size_sm};
  margin-top: 0.2rem;
  line-height: 1.35;
}}

.mccc-badge, .mccc-badge-success, .mccc-badge-warn, .mccc-badge-danger,
.mccc-badge-info, .mccc-badge-pro, .mccc-badge-live, .mccc-badge-demo {{
  display: inline-block;
  padding: 0.12rem 0.5rem;
  border-radius: 999px;
  font-size: {t.size_xs};
  font-weight: 600;
  letter-spacing: 0.07em;
  margin-right: 0.2rem;
  vertical-align: middle;
  line-height: 1.35;
}}
.mccc-badge {{ background: #14241f; color: var(--mccc-accent); border: 1px solid #00d4aa44; }}
.mccc-badge-success {{ background: #0f2a1c; color: var(--mccc-success); border: 1px solid #3dffb544; }}
.mccc-badge-warn {{ background: #2e241a; color: var(--mccc-warn); border: 1px solid #ffb02044; }}
.mccc-badge-danger {{ background: #2a1414; color: var(--mccc-danger); border: 1px solid #ff6b6b44; }}
.mccc-badge-info {{ background: #142030; color: var(--mccc-info); border: 1px solid #5eb3ff44; }}
.mccc-badge-pro {{ background: #221833; color: var(--mccc-pro); border: 1px solid #c4a0ff44; }}
.mccc-badge-live {{ background: #0f2a1c; color: var(--mccc-success); border: 1px solid #3dffb544; }}
.mccc-badge-demo {{ background: #2e241a; color: var(--mccc-warn); border: 1px solid #ffb02044; }}

.mccc-chip-live, .mccc-chip-demo {{
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  font-size: {t.size_xs};
  font-weight: 700;
  letter-spacing: 0.08em;
  font-family: var(--mccc-mono);
}}
.mccc-chip-live {{ background: #0f2a1c; color: var(--mccc-success); border: 1px solid #3dffb555; }}
.mccc-chip-demo {{ background: #2e241a; color: var(--mccc-warn); border: 1px solid #ffb02055; }}
.mccc-chip-dot {{
  width: 0.4rem; height: 0.4rem; border-radius: 50%;
  background: currentColor; display: inline-block;
}}

.mccc-empty {{
  background: var(--mccc-panel-2);
  border: 1px dashed var(--mccc-border);
  border-radius: var(--mccc-radius);
  padding: {s.lg};
  text-align: center;
  color: var(--mccc-muted);
  margin: {s.sm} 0;
}}
.mccc-empty strong {{ color: var(--mccc-text); display: block; margin-bottom: 0.35rem; }}
.mccc-error {{
  background: #2a1414;
  border: 1px solid #5a2020;
  border-radius: var(--mccc-radius);
  padding: {s.sm} {s.md};
  color: #ffb0b0;
  margin: {s.sm} 0;
  font-size: {t.size_md};
}}
.mccc-alert-info {{
  background: #142030;
  border: 1px solid #2a4560;
  border-radius: var(--mccc-radius);
  padding: {s.sm} {s.md};
  color: var(--mccc-text-secondary);
  font-size: {t.size_md};
  margin: {s.sm} 0;
}}

.mccc-kanban {{
  background: var(--mccc-panel-2);
  border: 1px solid var(--mccc-border);
  border-radius: {s.radius_sm};
  padding: {s.sm};
  margin-bottom: {s.sm};
  min-height: 2.9rem;
}}
.mccc-kanban .title {{ color: var(--mccc-text); font-weight: 600; font-size: {t.size_md}; }}
.mccc-kanban .meta {{ color: var(--mccc-muted); font-size: {t.size_sm}; margin-top: 0.15rem; }}

.mccc-list-row {{
  display: flex; justify-content: space-between; gap: 0.75rem;
  padding: 0.45rem 0; border-bottom: 1px solid var(--mccc-border-soft); font-size: {t.size_md};
}}
.mccc-list-row:last-child {{ border-bottom: none; }}
.mccc-list-row .title {{ color: var(--mccc-text); font-weight: 500; }}
.mccc-list-row .meta {{ color: var(--mccc-muted); font-size: {t.size_sm}; white-space: nowrap; }}

.mccc-footer {{
  margin-top: {s.xl};
  padding-top: {s.md};
  border-top: 1px solid var(--mccc-border-soft);
  color: var(--mccc-muted);
  font-size: {t.size_sm};
}}
.mccc-footer .ver {{ font-family: var(--mccc-mono); color: var(--mccc-accent); }}

.mccc-nav-group {{
  font-family: var(--mccc-mono);
  font-size: {t.size_xs};
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--mccc-muted);
  margin: 0.55rem 0 0.25rem;
}}

div[data-testid="stDataFrame"] {{
  border: 1px solid var(--mccc-border-soft);
  border-radius: var(--mccc-radius);
  overflow: hidden;
}}
div[data-testid="stDataFrame"] th {{
  background: var(--mccc-panel-2) !important;
  color: var(--mccc-muted) !important;
  font-weight: 600 !important;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  font-size: {t.size_xs} !important;
}}
div[data-testid="stMetricValue"] {{ font-family: var(--mccc-mono); }}

/* Charts */
div[data-testid="stPlotlyChart"], .stAltairChart {{
  background: var(--mccc-panel);
  border: 1px solid var(--mccc-border-soft);
  border-radius: var(--mccc-radius);
  padding: {s.sm};
}}

@media (max-width: 992px) {{
  .mccc-hero h1 {{ font-size: 1.3rem; }}
  .mccc-shell-block {{ padding: {s.sm} {s.md}; }}
}}
@media (max-width: 768px) {{
  .mccc-hero {{ padding: {s.sm} {s.md}; border-radius: {s.radius_md}; }}
  .mccc-hero h1 {{ font-size: 1.15rem; }}
  .mccc-card, .mccc-card-dense {{ padding: {s.sm}; }}
  .mccc-metric {{ font-size: 1.05rem; }}
  .mccc-list-row {{ flex-direction: column; gap: 0.15rem; }}
  section.main > div {{ padding-left: 0.6rem; padding-right: 0.6rem; }}
}}
</style>
"""


def page_shell_html(
    what_happened: str,
    why_it_matters: str,
    investigate: str,
    learn_next: str,
) -> str:
    """Pure HTML hierarchy strip for page tops (testable)."""
    import html as _html

    def block(title: str, body: str) -> str:
        return (
            f'<div class="mccc-shell-block"><h4>{_html.escape(title)}</h4>'
            f"<p>{_html.escape(body)}</p></div>"
        )

    return (
        '<div class="mccc-shell-grid">'
        + block("What happened", what_happened)
        + block("Why it matters", why_it_matters)
        + block("Investigate", investigate)
        + block("Learn next", learn_next)
        + "</div>"
    )
