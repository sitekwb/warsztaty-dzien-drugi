"""Append-only audit log for banking-grade traceability.

Every consequential action (a transfer, a score, a config change) should be
recorded as an attributable, append-only entry. In Block 4 ("the audit trail is
the feature") this backs the point that *"the model decided"* is never an
acceptable answer to a regulator -- a named actor on a recorded action is.

Deliberately tiny and in-memory: real deployments would append to a WORM store
or an append-only table. The shape (who / what / when / detail) is the lesson.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class AuditEntry:
    """One immutable audit record."""

    timestamp: datetime
    actor: str
    action: str
    detail: str


class AuditLog:
    """In-memory append-only audit log. Entries cannot be mutated or removed."""

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def record(self, actor: str, action: str, detail: str = "") -> AuditEntry:
        """Append an attributable entry and return it.

        ``actor`` must be a named human or system principal -- never empty,
        so every action is attributable.
        """
        if not actor:
            raise ValueError("audit entry requires a named actor")
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc),
            actor=actor,
            action=action,
            detail=detail,
        )
        self._entries.append(entry)
        return entry

    def entries(self) -> tuple[AuditEntry, ...]:
        """Return all entries as an immutable snapshot (read-only)."""
        return tuple(self._entries)

    def __len__(self) -> int:
        return len(self._entries)
