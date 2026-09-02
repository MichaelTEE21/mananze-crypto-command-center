"""Dev diagnostics — only when MCCC_DEV=1. No secrets shown."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc import APP_NAME, __version__
from mccc.config import config_status_public, env_flag
from mccc.db import connect, get_feature_flags, init_db, list_settings
from mccc.paths import DB_PATH
from mccc.ui import footer, hero, page_setup, section_header

page_setup("diagnostics", "Diagnostics")
hero("Diagnostics", "Dev-only health panel. Secrets are never displayed.")

if not env_flag("MCCC_DEV"):
    st.error("Diagnostics disabled. Set environment variable `MCCC_DEV=1` to open this page.")
    st.info("Admins can also view a gated diagnostics section on the Admin page when MCCC_DEV=1.")
    footer("Diagnostics")
    st.stop()

init_db()
section_header("Version", "Package + runtime")
st.write(f"**App:** {APP_NAME}")
st.write(f"**Version:** `{__version__}`")
st.write(f"**MCCC_DEV:** on")
st.write(f"**MCCC_PRO_UNLOCK:** {'on' if env_flag('MCCC_PRO_UNLOCK') else 'off'}")

section_header("Database", "SQLite connectivity (no data dump)")
try:
    with connect() as conn:
        tables = conn.execute(
            "SELECT COUNT(*) AS c FROM sqlite_master WHERE type='table'"
        ).fetchone()["c"]
        ok = True
    st.success(f"DB OK · path=`{DB_PATH}` · tables={tables}")
except Exception as exc:  # noqa: BLE001
    ok = False
    st.error(f"DB error: {exc}")

section_header("Config / flags", "Optional keys — set vs unset only")
status = config_status_public()
if status.get("warnings"):
    for w in status["warnings"]:
        st.warning(w)
else:
    st.caption("No config warnings.")
st.json(
    {
        "optional_keys": status.get("optional_keys"),
        "mccc_pro_unlock": status.get("mccc_pro_unlock"),
        "bootstrap_admin_email_set": status.get("bootstrap_admin_email_set"),
    }
)

section_header("Feature flags", "Local SQLite flags")
flags = get_feature_flags()
st.dataframe(
    [{"key": f["key"], "enabled": bool(f["enabled"]), "description": f["description"]} for f in flags],
    use_container_width=True,
    hide_index=True,
)

section_header("App settings keys", "Names only")
try:
    settings = list_settings()
    st.write(sorted(settings.keys()) or "(none)")
except Exception as exc:  # noqa: BLE001
    st.error(str(exc))

section_header("API status", "Reachability probes — no API keys echoed")
# Light CoinGecko ping
try:
    import requests

    r = requests.get("https://api.coingecko.com/api/v3/ping", timeout=5)
    st.write(f"CoinGecko `/ping`: HTTP {r.status_code}")
except Exception as exc:  # noqa: BLE001
    st.write(f"CoinGecko `/ping`: unavailable ({exc})")

ai_set = bool(os.environ.get("AI_API_KEY", "").strip())
cg_set = bool(os.environ.get("COINGECKO_API_KEY", "").strip())
es_set = bool(os.environ.get("ETHERSCAN_API_KEY", "").strip())
st.write(f"AI_API_KEY set: **{ai_set}** · COINGECKO_API_KEY set: **{cg_set}** · ETHERSCAN_API_KEY set: **{es_set}**")

section_header("Cache", "Market provider TTL cache")
try:
    from mccc.market_provider import _CACHE  # noqa: SLF001

    size = len(getattr(_CACHE, "_store", {}) or {})
    st.write(f"In-process TTL entries: **{size}**")
    if st.button("Clear market cache"):
        _CACHE.clear()
        st.success("Cache cleared.")
        st.rerun()
except Exception as exc:  # noqa: BLE001
    st.caption(f"Cache introspection unavailable: {exc}")

footer("Diagnostics")
