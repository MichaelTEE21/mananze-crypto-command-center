"""Global search — projects, airdrops, wallets, exchanges, education, resources, notes."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.search import SEARCH_CATEGORIES, search_all
from mccc.ui import empty_state, hero, page_setup, footer

page_setup("search", "Search")
hero(
    "SEARCH THE BLOCKCHAIN",
    "WHAT DO YOU WANT TO UNDERSTAND? · Journey: Search → Analyse → Understand",
)
st.caption(
    "Search a wallet, token, contract, project, or supported on-chain entity in the local research store. "
    "For a full Intelligence Report, continue in Intelligence Center → Analyse."
)
st.error(
    "PUBLIC ADDRESS ONLY when searching wallets — never seed phrases, private keys, passwords, or recovery phrases. "
    "MCCC does not need control of your wallet to analyse public blockchain activity."
)
st.page_link("pages/24_Intelligence_Center.py", label="ANALYSE → Intelligence Report", icon="🛰️")


if "mccc_recent_searches" not in st.session_state:
    st.session_state["mccc_recent_searches"] = []

recent = st.session_state["mccc_recent_searches"]
if recent:
    st.caption("Recent searches (this session)")
    cols = st.columns(min(5, len(recent)))
    for i, rq in enumerate(recent[:5]):
        if cols[i].button(rq, key=f"recent_{i}"):
            st.session_state["mccc_search_q"] = rq
            st.rerun()

q = st.text_input(
    "Query",
    value=st.session_state.get("mccc_search_q", ""),
    placeholder="wallet 0x… · bitcoin · uniswap · rwa · project name…",
).strip()
st.session_state["mccc_search_q"] = q

cats = st.multiselect(
    "Categories",
    list(SEARCH_CATEGORIES),
    default=list(SEARCH_CATEGORIES),
)

if not q:
    empty_state("WHAT DO YOU WANT TO UNDERSTAND?", "Matches name, notes, chain, public address, lessons, resources, RWA, intelligence — then ANALYSE →")
    st.stop()

# Record recent (dedupe, cap 8)
prev = [x for x in recent if x.lower() != q.lower()]
st.session_state["mccc_recent_searches"] = ([q] + prev)[:8]

results = search_all(q, categories=cats or list(SEARCH_CATEGORIES))

total = sum(len(v) for v in results.values())
st.caption(f"{total} hit(s) across {len(cats)} categor{'y' if len(cats)==1 else 'ies'}")

for cat in cats:
    hits = results.get(cat) or []
    st.subheader(f"{cat.title()} ({len(hits)})")
    if not hits:
        st.caption("No hits.")
        continue
    if cat == "projects":
        for p in hits[:25]:
            st.markdown(
                f"**#{p['id']} {p['name']}** · `{p.get('stage') or p.get('status')}` · {p.get('chain')}"
            )
            if p.get("notes"):
                st.caption((p["notes"] or "")[:160])
    elif cat == "airdrops":
        for a in hits[:25]:
            st.markdown(
                f"**#{a['id']} {a['project_name']}** · `{a.get('status')}` · {a.get('chain')}"
            )
    elif cat == "wallets":
        for w in hits[:25]:
            st.markdown(f"**#{w['id']} {w['label']}** · `{w.get('address')}` · {w.get('chain')}")
    elif cat == "exchanges":
        for e in hits[:25]:
            st.markdown(
                f"**#{e['id']} {e['name']}** · `{e.get('type')}` · {e.get('status')} · {e.get('region')}"
            )
    elif cat == "education":
        for path_hit in hits[:25]:
            with st.expander(path_hit.get("title") or path_hit.get("key", "lesson")):
                st.caption(path_hit.get("snippet") or "")
                st.markdown(f"`{path_hit.get('key')}`")
    elif cat == "resources":
        for r in hits[:25]:
            official = " · official" if r.get("is_official") else ""
            st.markdown(
                f"**#{r['id']} {r['title']}** · `{r.get('resource_type')}`{official} · clicks={r.get('click_count', 0)}"
            )
            if r.get("url"):
                st.caption(r["url"])
    elif cat == "notes":
        for n in hits[:25]:
            with st.expander(n.get("title") or f"Note #{n.get('id')}"):
                st.markdown((n.get("body") or "")[:2000])
                if n.get("project_id"):
                    st.caption(f"project_id={n['project_id']}")


    elif cat == "rwa":
        for r in hits[:25]:
            demo = " · DEMO / SYNTHETIC" if r.get("is_demo") else ""
            name = r.get("display_name") or r.get("project_name")
            st.markdown(
                f"**{name}** · `{r.get('rwa_category')}` · {r.get('blockchain')}{demo}"
            )
            st.caption((r.get("description") or "")[:160])
    elif cat == "intelligence":
        for e in hits[:25]:
            demo = " · DEMO" if e.get("is_demo") else ""
            st.markdown(
                f"**{e.get('title')}** · `{e.get('category')}` · {e.get('project')}{demo}"
            )

if q:
    st.divider()
    st.markdown("### Continue journey")
    st.caption("Search → Analyse → Understand")
    if st.button("ANALYSE →", type="primary", key="search_analyse_cta"):
        st.session_state["intel_report_q"] = q
        st.switch_page("pages/24_Intelligence_Center.py")

footer("Search")
