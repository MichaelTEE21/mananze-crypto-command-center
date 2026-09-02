"""Terms — lightweight."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.ui import footer, hero, page_setup

page_setup("terms", "Terms")
hero("Terms of use", "Research software — not financial advice.")

st.markdown(
    """
    ## Terms (short)

    1. MCCC is provided **as-is** for research and education.
    2. **Not financial, legal, or tax advice.** Do your own research.
    3. You are responsible for verifying networks, addresses, and transactions.
    4. Do not submit seed phrases, private keys, or account-recovery secrets to MCCC.
    5. DEMO / EXAMPLE data is practice data — not live balances or eligibility guarantees.
    6. Partner / referral links may compensate MCCC at no extra cost to you when disclosed.
    7. Donations are voluntary and do **not** purchase PRO or services.
    8. PRO payments are **not yet enabled** — never trust a fake checkout success.
    9. Operators may suspend abuse (spam, malware, credential stuffing).

    If you disagree, do not use the software.
    """
)
st.page_link("pages/30_Privacy.py", label="Privacy", icon="🔒")
st.page_link("pages/28_Support_MCCC.py", label="Support MCCC", icon="💜")
footer("Terms")
