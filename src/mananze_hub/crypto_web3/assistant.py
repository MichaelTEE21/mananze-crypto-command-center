"""Local rule-based research assistant — no LLM, no invented live prices."""
from __future__ import annotations

from typing import Any

TIPS: list[dict[str, str]] = [
    {
        "id": "diligence",
        "title": "Project diligence checklist",
        "keywords": "diligence audit team tokenomics unlock research",
        "body": (
            "1. Read official docs & whitepaper summaries.\n"
            "2. Verify team / entity disclosure and prior work.\n"
            "3. Check audit reports (who audited, what scope).\n"
            "4. Map token unlock schedule and circulating supply claims.\n"
            "5. Note bridge / custody / admin-key risks.\n"
            "6. Log sources in Project Tracker — never rely on rumour alone."
        ),
    },
    {
        "id": "airdrop",
        "title": "Airdrop research hygiene",
        "keywords": "airdrop points eligibility sybil claim",
        "body": (
            "1. Prefer official docs over screenshots.\n"
            "2. Track eligibility criteria in Airdrop Tracker with dates.\n"
            "3. Avoid sharing seed phrases or signing unknown permits.\n"
            "4. Separate research wallets from long-term storage (public watch only here).\n"
            "5. Mark estimates as DEMO / unknown until confirmed on-chain."
        ),
    },
    {
        "id": "security",
        "title": "Wallet & security basics",
        "keywords": "wallet security seed private key phishing hardware",
        "body": (
            "1. MCCC never stores seed phrases or private keys — by design.\n"
            "2. Use hardware wallets for meaningful funds.\n"
            "3. Verify URLs; bookmark official sites.\n"
            "4. Revoke unused token approvals periodically (external tools).\n"
            "5. Treat unexpected airdrops / DMs as hostile until proven otherwise."
        ),
    },
    {
        "id": "market",
        "title": "Reading market data responsibly",
        "keywords": "price market chart volume coingecko",
        "body": (
            "1. Always check the labelled source (CoinGecko vs DEMO fallback).\n"
            "2. 24h change is not a thesis — pair with fundamentals.\n"
            "3. Do not invent prices; if offline, use DEMO tables consciously.\n"
            "4. Cross-check market cap vs fully diluted valuation narratives."
        ),
    },
    {
        "id": "workflow",
        "title": "Research workflow OS",
        "keywords": "workflow notes tracker command center habit",
        "body": (
            "1. Capture every open question in Project Tracker.\n"
            "2. Attach sources & dates in notes.\n"
            "3. Review Airdrop Tracker weekly; archive claimed / dead deals.\n"
            "4. Use Education modules before chasing narratives.\n"
            "5. Log page usage locally — privacy-friendly self-analytics."
        ),
    },
    {
        "id": "onchain",
        "title": "On-chain observation checklist",
        "keywords": "on-chain tvl bridge explorer contract",
        "body": (
            "1. Verify contract addresses from official channels only.\n"
            "2. Read explorer activity: holders, large transfers, deploy age.\n"
            "3. For L2s: understand bridge trust assumptions.\n"
            "4. Record watch addresses as public-only entries in Wallet Tracking."
        ),
    },
]


def match_tips(query: str, limit: int = 3) -> list[dict[str, str]]:
    q = (query or "").lower().strip()
    if not q:
        return TIPS[:limit]
    scored: list[tuple[int, dict[str, str]]] = []
    for tip in TIPS:
        score = 0
        for word in tip["keywords"].split():
            if word in q:
                score += 2
        for word in q.split():
            if word in tip["title"].lower() or word in tip["body"].lower():
                score += 1
        if score:
            scored.append((score, tip))
    scored.sort(key=lambda x: x[0], reverse=True)
    if not scored:
        return [
            {
                "id": "default",
                "title": "How to use this assistant",
                "keywords": "",
                "body": (
                    "Ask about diligence, airdrops, security, market data hygiene, "
                    "workflow, or on-chain checks. I return curated checklists — "
                    "I never invent live prices or alpha claims."
                ),
            }
        ]
    return [t for _, t in scored[:limit]]


def structure_research_note(topic: str, context: str = "") -> dict[str, Any]:
    topic = (topic or "Untitled research").strip()
    ctx = (context or "").strip()
    template = (
        f"# {topic}\n\n"
        "## Question\n- What am I trying to learn?\n\n"
        "## Sources\n- [ ] Official docs\n- [ ] Explorer / contracts\n- [ ] Audit links\n\n"
        "## Risks\n- [ ] Admin keys / upgradeability\n- [ ] Liquidity / unlocks\n- [ ] Bridge assumptions\n\n"
        "## Decision log\n- Date:\n- Stance: watching / pass / deeper dive\n- Why:\n"
    )
    if ctx:
        template += f"\n## Case context\n{ctx}\n"
    template += (
        "\n---\n_Generated by MCCC local assistant (rule-based). "
        "Not financial advice. No live prices invented._\n"
    )
    return {"title": f"Research note: {topic}", "body": template, "tags": "assistant,checklist"}
