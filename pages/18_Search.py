"""Universal Search — entity chips + route ANALYSE into Intelligence Report."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.search import SEARCH_CATEGORIES, search_all
from mccc.universal_search import (
    ENTITY_CHIPS,
    analyse_session_payload,
    detect_search_entity,
    homepage_search_placeholder,
    unified_search_results,
)
from mccc.ui import empty_state, footer, hero, page_setup, section_header, status_badge

page_setup("search", "Search")
hero(
    "SEARCH",
    "One search · wallet · token · contract · project · protocol · airdrop · Journey: Search → Analyse → Understand",
)
st.caption("No crypto jargon required upfront. Entity type is detected automatically when possible.")
st.error(
    "PUBLIC ADDRESS ONLY when searching wallets — never seed phrases, private keys, passwords, or recovery phrases. "
    "MCCC does not need control of your wallet to analyse public blockchain activity."
)

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
    placeholder=homepage_search_placeholder(),
).strip()
st.session_state["mccc_search_q"] = q

chip_filter = st.multiselect(
    "Entity type chips (filter typed hits)",
    list(ENTITY_CHIPS),
    default=list(ENTITY_CHIPS),
)
cats = st.multiselect(
    "Local store categories",
    list(SEARCH_CATEGORIES),
    default=list(SEARCH_CATEGORIES),
)

if not q:
    empty_state(
        "WHAT DO YOU WANT TO UNDERSTAND?",
        "Search a wallet (0x…), $TICKER, project name, protocol, or airdrop — then ANALYSE →",
    )
    st.stop()

detected = detect_search_entity(q)
if detected.rejected_secret:
    st.error(detected.error)
    st.stop()

# Record recent
prev = [x for x in recent if x.lower() != q.lower()]
st.session_state["mccc_recent_searches"] = ([q] + prev)[:8]

section_header("Detected entity", "FACT of detection is best-effort — verify before acting")
if detected.ok:
    status_badge(detected.chip, "info")
    st.markdown(
        f"**Type:** `{detected.entity_type}` · **Normalised:** `{detected.normalized}`"
    )
    for w in detected.warnings:
        st.caption(w)
else:
    st.warning(detected.error or "Could not classify — still searching local store.")

c1, c2 = st.columns(2)
with c1:
    if st.button("ANALYSE", type="primary", key="search_analyse_cta"):
        if not detected.ok:
            st.error(detected.error or "Cannot analyse this input.")
        else:
            for k, v in analyse_session_payload(detected).items():
                st.session_state[k] = v
            st.switch_page("pages/24_Intelligence_Center.py")
with c2:
    st.page_link("pages/24_Intelligence_Center.py", label="Open Intelligence Center", icon="🛰️")

unified = unified_search_results(q)
typed = [h for h in unified["typed_hits"] if h["chip"] in chip_filter]
st.subheader(f"Typed hits ({len(typed)})")
if not typed:
    st.caption("No typed hits for selected chips.")
else:
    for h in typed[:40]:
        status_badge(h["chip"], "info")
        st.markdown(f"**{h['title']}** · {h.get('subtitle') or ''}")

st.divider()
results = search_all(q, categories=cats or list(SEARCH_CATEGORIES))
total = sum(len(v) for v in results.values())
st.caption(f"{total} category hit(s) across {len(cats)} categor{'y' if len(cats)==1 else 'ies'}")

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

footer("Search")
