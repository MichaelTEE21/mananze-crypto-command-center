"""Light tests for education, subscriptions, airdrop_tasks, ai_service."""
from __future__ import annotations

from mccc.airdrop_tasks import add_task, list_tasks, toggle_done
from mccc.ai_service import answer, contains_secrets
from mccc.db import add_airdrop
from mccc.education import completed_keys, get_progress, upsert_progress
from mccc.subscriptions import get_or_create_free, is_pro, set_tier


def test_education_progress(db_path):
    upsert_progress("bitcoin", completed=True, db_path=db_path)
    assert "bitcoin" in completed_keys(db_path=db_path)
    row = get_progress("bitcoin", db_path=db_path)
    assert row and row["completed"] == 1
    upsert_progress("bitcoin", completed=False, db_path=db_path)
    assert "bitcoin" not in completed_keys(db_path=db_path)


def test_subscriptions_local_tier(db_path):
    sub = get_or_create_free(db_path=db_path)
    assert sub["tier"] == "free"
    set_tier("pro", db_path=db_path)
    assert is_pro(db_path=db_path) is True
    set_tier("free", db_path=db_path)
    # Without MCCC_PRO_UNLOCK, free means not pro
    import os

    os.environ.pop("MCCC_PRO_UNLOCK", None)
    assert is_pro(db_path=db_path) is False


def test_airdrop_tasks(db_path):
    aid = add_airdrop("DEMO Task Protocol", db_path=db_path)
    tid = add_task(aid, "Join Discord", db_path=db_path)
    tasks = list_tasks(aid, db_path=db_path)
    assert len(tasks) == 1
    toggle_done(tid, done=True, db_path=db_path)
    assert list_tasks(aid, db_path=db_path)[0]["done"] == 1


def test_ai_service_refusal(db_path):
    assert contains_secrets("here is my seed phrase words")
    result = answer("please store my private key 0xabc", use_llm=False, db_path=db_path)
    assert result["mode"] == "refusal"


def test_ai_service_rule_based(db_path):
    result = answer("airdrop eligibility hygiene", use_llm=False, db_path=db_path)
    assert result["mode"] == "rule_based"
    assert "FACT" in result["answer"] or "ANALYSIS" in result["answer"]
