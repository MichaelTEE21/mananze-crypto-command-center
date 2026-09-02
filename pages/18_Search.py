"""Global search across projects, airdrops, wallets, education."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.db import list_airdrops, list_projects, list_wallets
from mccc.paths import EDUCATION_DIR, ensure_dirs
from mccc.ui import empty_state, hero, page_setup

page_setup("search", "Search")
hero("Search", "Find projects, airdrops, wallets, and education lessons.")

q = st.text_input("Query", placeholder="bridge, DEMO, ethereum…").strip().lower()

if not q:
    empty_state("Type to search", "Matches name, notes, chain, address, and lesson titles.")
    st.stop()

projects = [p for p in list_projects() if q in " ".join(str(v) for v in p.values()).lower()]
airdrops = [a for a in list_airdrops() if q in " ".join(str(v) for v in a.values()).lower()]
wallets = [w for w in list_wallets() if q in " ".join(str(v) for v in w.values()).lower()]

ensure_dirs()
lessons = []
for path in sorted(EDUCATION_DIR.glob("*.md")):
    text = path.read_text(encoding="utf-8")
    if q in path.stem.lower() or q in text.lower():
        lessons.append(path)

st.subheader(f"Projects ({len(projects)})")
if not projects:
    st.caption("No project hits.")
else:
    for p in projects[:25]:
        st.markdown(f"**#{p['id']} {p['name']}** · `{p.get('stage') or p.get('status')}` · {p.get('chain')}")
        if p.get("notes"):
            st.caption((p["notes"] or "")[:160])

st.subheader(f"Airdrops ({len(airdrops)})")
if not airdrops:
    st.caption("No airdrop hits.")
else:
    for a in airdrops[:25]:
        st.markdown(
            f"**#{a['id']} {a['project_name']}** · `{a.get('status')}` · {a.get('chain')}"
        )

st.subheader(f"Wallets ({len(wallets)})")
if not wallets:
    st.caption("No wallet hits.")
else:
    for w in wallets[:25]:
        st.markdown(f"**#{w['id']} {w['label']}** · `{w.get('address')}` · {w.get('chain')}")

st.subheader(f"Education ({len(lessons)})")
if not lessons:
    st.caption("No lesson hits.")
else:
    for path in lessons[:25]:
        with st.expander(path.stem.replace("_", " ").title()):
            st.markdown(path.read_text(encoding="utf-8")[:2000])
