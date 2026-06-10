"""Tests for the append-only audit log."""

from __future__ import annotations

import pytest

from minibank.audit import AuditLog


def test_record_appends_attributable_entry() -> None:
    log = AuditLog()
    entry = log.record(actor="j.kowalski", action="transfer", detail="ACC-SRC->ACC-DST 70.00")
    assert len(log) == 1
    assert entry.actor == "j.kowalski"
    assert entry.action == "transfer"
    assert entry.timestamp.tzinfo is not None  # timezone-aware


def test_actor_is_required() -> None:
    log = AuditLog()
    with pytest.raises(ValueError):
        log.record(actor="", action="transfer")


def test_log_is_append_only_snapshot() -> None:
    log = AuditLog()
    log.record(actor="system", action="score", detail="tx-1 -> 42")
    snapshot = log.entries()
    log.record(actor="system", action="score", detail="tx-2 -> 7")
    # The earlier snapshot is immutable and unaffected by later appends.
    assert len(snapshot) == 1
    assert len(log) == 2
    assert isinstance(snapshot, tuple)
