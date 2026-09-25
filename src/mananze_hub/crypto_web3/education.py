"""Education progress + lesson catalog (BEGINNER / INTERMEDIATE / ADVANCED)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

from mccc.db import connect, utc_now
from mccc.paths import EDUCATION_DIR, ensure_dirs

CATEGORIES = ("BEGINNER", "INTERMEDIATE", "ADVANCED")

# Explicit metadata for known lessons (category + related + glossary + quiz).
# Frontmatter in markdown overrides category/related when present.
LESSON_META: dict[str, dict[str, Any]] = {
    # BEGINNER
    "01_research_mindset": {
        "category": "BEGINNER",
        "related": ["05_market_data_literacy", "scams", "key_safety"],
        "glossary": {"primary source": "Docs, explorers, audits — not screenshots alone."},
    },
    "bitcoin": {"category": "BEGINNER", "related": ["blockchain", "wallet", "token"]},
    "blockchain": {"category": "BEGINNER", "related": ["bitcoin", "gas", "wallet"]},
    "wallet": {"category": "BEGINNER", "related": ["key_safety", "seed_phrase", "wallet_security"]},
    "token": {"category": "BEGINNER", "related": ["cex", "dex", "03_tokenomics_diligence"]},
    "gas": {"category": "BEGINNER", "related": ["blockchain", "02_onchain_basics"]},
    "cex": {"category": "BEGINNER", "related": ["dex", "phishing", "scams"]},
    "dex": {"category": "BEGINNER", "related": ["cex", "defi_basics", "approvals"]},
    "key_safety": {"category": "BEGINNER", "related": ["seed_phrase", "private_key", "wallet_security"]},
    "seed_phrase": {"category": "BEGINNER", "related": ["key_safety", "private_key", "phishing"]},
    "private_key": {"category": "BEGINNER", "related": ["seed_phrase", "key_safety"]},
    "wallet_security": {"category": "BEGINNER", "related": ["key_safety", "approvals", "phishing"]},
    "phishing": {"category": "BEGINNER", "related": ["scams", "fake_airdrops", "approvals"]},
    "scams": {"category": "BEGINNER", "related": ["phishing", "fake_airdrops", "04_airdrop_hygiene"]},
    "fake_airdrops": {"category": "BEGINNER", "related": ["04_airdrop_hygiene", "scams", "phishing"]},
    "approvals": {"category": "BEGINNER", "related": ["wallet_security", "dex", "defi_basics"]},
    "02_onchain_basics": {"category": "BEGINNER", "related": ["gas", "blockchain", "wallet"]},
    "03_tokenomics_diligence": {
        "category": "BEGINNER",
        "related": ["token", "05_market_data_literacy"],
    },
    "04_airdrop_hygiene": {
        "category": "BEGINNER",
        "related": ["fake_airdrops", "scams", "phishing"],
    },
    "05_market_data_literacy": {
        "category": "BEGINNER",
        "related": ["01_research_mindset", "03_tokenomics_diligence"],
    },
    # INTERMEDIATE
    "defi_basics": {
        "category": "INTERMEDIATE",
        "related": ["staking", "bridges", "approvals"],
        "glossary": {
            "TVL": "Total value locked — often self-reported; verify methodology.",
            "oracle": "Price/data feed contracts rely on; oracle failure is a common exploit path.",
        },
    },
    "bridges": {
        "category": "INTERMEDIATE",
        "related": ["l1_l2", "defi_basics", "scams"],
        "glossary": {"bridge": "Moves assets/messages across chains; custody and message verification matter."},
    },
    "staking": {
        "category": "INTERMEDIATE",
        "related": ["defi_basics", "l1_l2"],
        "glossary": {"slashing": "Penalty for validator misbehavior on PoS networks."},
    },
    "l1_l2": {
        "category": "INTERMEDIATE",
        "related": ["bridges", "zk_basics", "mev"],
        "glossary": {
            "L1": "Base settlement layer (e.g. Ethereum mainnet).",
            "L2": "Scaling layer that posts data/proofs to an L1.",
        },
    },
    "mev": {
        "category": "INTERMEDIATE",
        "related": ["l1_l2", "dex", "defi_basics"],
        "glossary": {"MEV": "Maximal extractable value — ordering/inclusion advantages around transactions."},
    },
    # ADVANCED
    "depin": {
        "category": "ADVANCED",
        "related": ["01_research_mindset", "03_tokenomics_diligence"],
        "glossary": {"DePIN": "Decentralized physical infrastructure networks (compute, wireless, sensors, etc.)."},
    },
    "zk_basics": {
        "category": "ADVANCED",
        "related": ["l1_l2", "bridges"],
        "glossary": {
            "ZK": "Zero-knowledge proofs — verify statements without revealing underlying data.",
            "validity proof": "Cryptographic proof that an L2 state transition is correct.",
        },
    },
    "ai_agents_crypto": {
        "category": "ADVANCED",
        "related": ["scams", "key_safety", "01_research_mindset"],
        "glossary": {
            "agent": "Software that acts semi-autonomously; never give it seed/private keys.",
        },
    },
    # RWA (Real-World Assets) — INTERMEDIATE education vertical
    "rwa_tokenization": {
        "category": "INTERMEDIATE",
        "related": ["rwa_treasuries", "rwa_private_credit", "rwa_risks"],
        "glossary": {
            "RWA": "Real-world asset — off-chain value represented via on-chain claims.",
            "tokenization": "Mapping an asset/claim to a ledger token; legal wrapper matters.",
        },
    },
    "rwa_treasuries": {
        "category": "INTERMEDIATE",
        "related": ["rwa_tokenization", "rwa_settlement", "rwa_risks"],
        "glossary": {"tokenized treasury": "On-chain claim designed to track treasury exposure — verify issuer docs."},
    },
    "rwa_private_credit": {
        "category": "INTERMEDIATE",
        "related": ["rwa_tokenization", "rwa_collateral", "rwa_risks"],
    },
    "rwa_real_estate": {
        "category": "INTERMEDIATE",
        "related": ["rwa_tokenization", "rwa_custody", "rwa_risks"],
    },
    "rwa_custody": {
        "category": "INTERMEDIATE",
        "related": ["rwa_settlement", "rwa_collateral", "rwa_risks"],
        "glossary": {"custody": "Who holds the underlying asset/cash and under what controls."},
    },
    "rwa_collateral": {
        "category": "INTERMEDIATE",
        "related": ["rwa_private_credit", "rwa_redemption", "rwa_risks"],
    },
    "rwa_redemption": {
        "category": "INTERMEDIATE",
        "related": ["rwa_settlement", "rwa_custody", "rwa_risks"],
    },
    "rwa_settlement": {
        "category": "INTERMEDIATE",
        "related": ["rwa_custody", "rwa_tokenization", "rwa_risks"],
    },
    "rwa_risks": {
        "category": "INTERMEDIATE",
        "related": ["rwa_tokenization", "rwa_custody", "rwa_redemption"],
        "glossary": {
            "disclosure indicator": "DISCLOSED / NOT DISCLOSED / UNKNOWN — not a buy/sell rating.",
        },
    },
}

# Simple knowledge-check banks keyed by lesson. Kept short; not graded inventively.
QUIZ_BANK: dict[str, list[dict[str, Any]]] = {
    "01_research_mindset": [
        {
            "q": "Which source class should you prefer?",
            "choices": ["Primary docs/explorers/audits", "Anonymous Discord screenshots only", "Unlabelled DEMO prices as live"],
            "answer": 0,
        }
    ],
    "key_safety": [
        {
            "q": "Should MCCC ever store your seed phrase?",
            "choices": ["Yes, for convenience", "No — never accept/store seeds or private keys", "Only in DEMO mode"],
            "answer": 1,
        }
    ],
    "defi_basics": [
        {
            "q": "A core DeFi research habit is:",
            "choices": ["Ignore audits", "Track protocols with dated primary sources", "Paste private keys into dashboards"],
            "answer": 1,
        }
    ],
    "bridges": [
        {
            "q": "Bridge risk primarily comes from:",
            "choices": ["Custody + message verification failures", "Higher gas alone", "Having a referral link"],
            "answer": 0,
        }
    ],
    "staking": [
        {
            "q": "Slashing means:",
            "choices": ["A marketing airdrop", "Penalty for validator misbehavior", "Free leverage"],
            "answer": 1,
        }
    ],
    "l1_l2": [
        {
            "q": "An L2 typically:",
            "choices": ["Replaces the need for any L1 forever", "Scales by posting data/proofs to an L1", "Stores your seed phrase"],
            "answer": 1,
        }
    ],
    "mev": [
        {
            "q": "MEV refers to:",
            "choices": ["A stablecoin peg mechanism", "Value from tx ordering/inclusion advantages", "A wallet brand"],
            "answer": 1,
        }
    ],
    "zk_basics": [
        {
            "q": "A validity proof is used to:",
            "choices": ["Prove an L2 transition without trusting operators blindly", "Invent live prices", "Bypass seed-phrase rules"],
            "answer": 0,
        }
    ],
    "depin": [
        {
            "q": "DePIN diligence should focus on:",
            "choices": ["Physical unit economics + honest metrics", "Only Twitter followers", "DEMO PnL as revenue"],
            "answer": 0,
        }
    ],
    "ai_agents_crypto": [
        {
            "q": "Giving an AI agent your seed phrase is:",
            "choices": ["Recommended for automation", "Unsafe — never share seeds/keys with agents", "Fine if labelled DEMO"],
            "answer": 1,
        }
    ],
    "scams": [
        {
            "q": "Fake support asking for a seed is:",
            "choices": ["Normal onboarding", "A common scam — refuse", "Required for LIVE mode"],
            "answer": 1,
        }
    ],
    "rwa_tokenization": [
        {
            "q": "Tokenization always means you legally own the off-chain asset?",
            "choices": ["Yes, always", "No — legal wrappers/custody/jurisdiction matter", "Only if labelled DEMO"],
            "answer": 1,
        }
    ],
    "rwa_risks": [
        {
            "q": "MCCC RWA risk framework uses:",
            "choices": ["Buy/sell ratings", "Disclosure indicators (DISCLOSED / NOT DISCLOSED / UNKNOWN)", "Guaranteed yields"],
            "answer": 1,
        }
    ],
    "rwa_treasuries": [
        {
            "q": "A calculated estimate of tokenized asset value should be labelled:",
            "choices": ["TVL", "Calculated estimate (not TVL)", "Verified price target"],
            "answer": 1,
        }
    ],
}


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_WARN_RE = re.compile(r"(?im)^(>|\*\*warning\*\*|##\s*warnings?\b).*")


def upsert_progress(
    lesson_key: str,
    completed: bool = True,
    quiz_score: Optional[float] = None,
    user_id: Optional[int] = None,
    db_path: Optional[Path] = None,
) -> None:
    key = (lesson_key or "").strip()
    if not key:
        raise ValueError("lesson_key is required")
    now = utc_now()
    with connect(db_path) as conn:
        if user_id is None:
            row = conn.execute(
                "SELECT id FROM education_progress WHERE lesson_key=? AND user_id IS NULL",
                (key,),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT id FROM education_progress WHERE lesson_key=? AND user_id=?",
                (key, user_id),
            ).fetchone()
        if row:
            conn.execute(
                """UPDATE education_progress
                   SET completed=?, quiz_score=?, updated_at=? WHERE id=?""",
                (1 if completed else 0, quiz_score, now, row["id"]),
            )
        else:
            conn.execute(
                """INSERT INTO education_progress
                   (user_id, lesson_key, completed, quiz_score, updated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, key, 1 if completed else 0, quiz_score, now),
            )


def list_progress(
    user_id: Optional[int] = None,
    db_path: Optional[Path] = None,
) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        if user_id is None:
            rows = conn.execute(
                "SELECT * FROM education_progress ORDER BY updated_at DESC"
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM education_progress
                   WHERE user_id=? OR user_id IS NULL
                   ORDER BY updated_at DESC""",
                (user_id,),
            ).fetchall()
        return [dict(r) for r in rows]


def get_progress(
    lesson_key: str,
    user_id: Optional[int] = None,
    db_path: Optional[Path] = None,
) -> Optional[dict[str, Any]]:
    key = (lesson_key or "").strip()
    with connect(db_path) as conn:
        if user_id is None:
            row = conn.execute(
                "SELECT * FROM education_progress WHERE lesson_key=? AND user_id IS NULL",
                (key,),
            ).fetchone()
        else:
            row = conn.execute(
                """SELECT * FROM education_progress
                   WHERE lesson_key=? AND (user_id=? OR user_id IS NULL)
                   ORDER BY user_id DESC LIMIT 1""",
                (key, user_id),
            ).fetchone()
        return dict(row) if row else None


def completed_keys(user_id: Optional[int] = None, db_path: Optional[Path] = None) -> set[str]:
    return {r["lesson_key"] for r in list_progress(user_id=user_id, db_path=db_path) if r.get("completed")}


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse optional YAML-like frontmatter (key: value lines). Returns (meta, body)."""
    m = _FRONTMATTER_RE.match(text or "")
    if not m:
        return {}, text or ""
    meta: dict[str, Any] = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        key = k.strip().lower()
        val = v.strip().strip("\"'")
        if key == "related":
            meta["related"] = [p.strip() for p in val.replace(";", ",").split(",") if p.strip()]
        elif key == "category":
            cat = val.upper()
            meta["category"] = cat if cat in CATEGORIES else "BEGINNER"
        elif key == "glossary":
            # simple "term=def; term2=def2"
            gloss: dict[str, str] = {}
            for part in val.split(";"):
                if "=" in part:
                    t, d = part.split("=", 1)
                    gloss[t.strip()] = d.strip()
            meta["glossary"] = gloss
        else:
            meta[key] = val
    body = text[m.end() :]
    return meta, body


def infer_category_from_name(stem: str) -> str:
    """Naming convention fallback: advanced_*, intermediate_*, or LESSON_META."""
    s = (stem or "").lower()
    if s.startswith("advanced_") or s.startswith("adv_"):
        return "ADVANCED"
    if s.startswith("intermediate_") or s.startswith("int_"):
        return "INTERMEDIATE"
    if s.startswith("beginner_") or s.startswith("beg_"):
        return "BEGINNER"
    meta = LESSON_META.get(stem) or {}
    cat = meta.get("category", "BEGINNER")
    return cat if cat in CATEGORIES else "BEGINNER"


def lesson_title_from_body(body: str, stem: str) -> str:
    for line in (body or "").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return stem.replace("_", " ").title()


def extract_warnings(body: str) -> list[str]:
    warnings: list[str] = []
    for line in (body or "").splitlines():
        stripped = line.strip()
        if stripped.startswith(">") or stripped.lower().startswith("**warning"):
            warnings.append(stripped.lstrip("> ").strip())
        elif re.match(r"(?i)^##\s*warnings?\b", stripped):
            warnings.append(stripped)
    # Always surface security reminder for education
    if not any("not financial advice" in w.lower() for w in warnings):
        warnings.append("Not financial advice. Education only.")
    return warnings[:8]


def get_quiz(lesson_key: str) -> list[dict[str, Any]]:
    return list(QUIZ_BANK.get(lesson_key) or [])


def score_quiz(lesson_key: str, answers: list[int]) -> Optional[float]:
    """Return fraction correct 0..1, or None if no quiz / empty answers. Does not invent scores."""
    bank = get_quiz(lesson_key)
    if not bank or not answers:
        return None
    n = min(len(bank), len(answers))
    if n == 0:
        return None
    correct = sum(1 for i in range(n) if answers[i] == bank[i].get("answer"))
    return correct / n


def load_lesson(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(raw)
    stem = path.stem
    base = dict(LESSON_META.get(stem) or {})
    category = fm.get("category") or base.get("category") or infer_category_from_name(stem)
    if category not in CATEGORIES:
        category = "BEGINNER"
    related = fm.get("related") or base.get("related") or []
    glossary = dict(base.get("glossary") or {})
    glossary.update(fm.get("glossary") or {})
    return {
        "key": stem,
        "path": path,
        "title": lesson_title_from_body(body, stem),
        "category": category,
        "body": body,
        "related": list(related),
        "glossary": glossary,
        "warnings": extract_warnings(body),
        "quiz": get_quiz(stem),
    }


def list_lessons(education_dir: Optional[Path] = None) -> list[dict[str, Any]]:
    ensure_dirs()
    root = education_dir or EDUCATION_DIR
    lessons = [load_lesson(p) for p in sorted(root.glob("*.md"))]
    order = {c: i for i, c in enumerate(CATEGORIES)}
    lessons.sort(key=lambda L: (order.get(L["category"], 99), L["title"].lower()))
    return lessons


def lessons_by_category(education_dir: Optional[Path] = None) -> dict[str, list[dict[str, Any]]]:
    out = {c: [] for c in CATEGORIES}
    for L in list_lessons(education_dir=education_dir):
        out.setdefault(L["category"], []).append(L)
    return out


def category_of(lesson_key: str, education_dir: Optional[Path] = None) -> str:
    ensure_dirs()
    root = education_dir or EDUCATION_DIR
    path = root / f"{lesson_key}.md"
    if path.exists():
        return load_lesson(path)["category"]
    return infer_category_from_name(lesson_key)
