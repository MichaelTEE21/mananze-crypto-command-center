"""Stage 8 — Education modules (static markdown)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.paths import EDUCATION_DIR, ensure_dirs
from mccc.ui import hero, page_setup

page_setup("education", "Education")
hero("Education", "Crypto research basics — static local lessons. Not financial advice.")

ensure_dirs()
lessons = sorted(EDUCATION_DIR.glob("*.md"))
if not lessons:
    st.error("No lessons found in content/education/")
else:
    titles = [p.stem.replace("_", " ").title() for p in lessons]
    pick = st.selectbox("Module", titles)
    path = lessons[titles.index(pick)]
    st.markdown(path.read_text(encoding="utf-8"))
