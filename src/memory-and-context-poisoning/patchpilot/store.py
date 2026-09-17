"""In-memory state with immutable audit events and clean snapshots."""

from __future__ import annotations

from copy import deepcopy

from .fixtures import CLEAN_MEMORY
from .models import AuditEvent, MemoryEntry


class MemoryStore:
    def __init__(self) -> None:
        self._clean_snapshot = deepcopy(CLEAN_MEMORY)
        self.memories = deepcopy(CLEAN_MEMORY)
        self.audit_events: list[AuditEvent] = []

    def reset(self) -> None:
        self.memories = deepcopy(self._clean_snapshot)
        self.audit_events = []
        self.audit("snapshot", "clean-v1", "restored", "Reset to deterministic baseline")

    def upsert(self, entry: MemoryEntry) -> None:
        self.memories = [item for item in self.memories if item.id != entry.id]
        self.memories.append(entry)

    def audit(
        self,
        action: str,
        subject_id: str,
        outcome: str,
        reason: str,
        **details: object,
    ) -> AuditEvent:
        event = AuditEvent(
            sequence=len(self.audit_events) + 1,
            action=action,
            subject_id=subject_id,
            outcome=outcome,
            reason=reason,
            details=details,
        )
        self.audit_events.append(event)
        return event

    def snapshot(self) -> list[MemoryEntry]:
        return deepcopy(self.memories)
