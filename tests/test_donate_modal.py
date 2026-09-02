"""Support MCCC soft prompt — first visit delayed, not every nav."""
from __future__ import annotations

import types
import sys

from mccc.donations import (
    DELAY_HOME_INTERACTIONS,
    SESSION_DISMISSED_KEY,
    SESSION_HOME_RUNS_KEY,
    SESSION_PROMPT_SHOWN_KEY,
    dismiss_donate_prompt,
    is_donate_prompt_dismissed,
    should_show_donate_soft_prompt,
)


def _fake_st(monkeypatch, sess: dict):
    fake = types.ModuleType("streamlit")
    fake.session_state = sess
    monkeypatch.setitem(sys.modules, "streamlit", fake)


def test_delayed_first_visit_only(monkeypatch):
    sess: dict = {}
    _fake_st(monkeypatch, sess)
    # not on other pages
    assert should_show_donate_soft_prompt("markets") is False
    # first home runs — delayed
    for i in range(DELAY_HOME_INTERACTIONS - 1):
        assert should_show_donate_soft_prompt("command_center") is False
    # after delay — show once
    assert should_show_donate_soft_prompt("command_center") is True
    sess[SESSION_PROMPT_SHOWN_KEY] = True
    assert should_show_donate_soft_prompt("command_center") is False


def test_dismiss_session(monkeypatch):
    sess: dict = {SESSION_HOME_RUNS_KEY: 99}
    _fake_st(monkeypatch, sess)
    dismiss_donate_prompt(user_id=None, durable=False)
    assert sess.get(SESSION_DISMISSED_KEY) is True
    assert is_donate_prompt_dismissed() is True
    assert should_show_donate_soft_prompt("command_center") is False
