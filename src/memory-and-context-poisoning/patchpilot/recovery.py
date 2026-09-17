"""Quarantine, dependency invalidation, and clean snapshot rollback."""

from __future__ import annotations

from .models import MemoryStatus
from .store import MemoryStore


class RecoveryService:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def quarantine_and_rollback(self, memory_id: str) -> None:
        target = next(
            (item for item in self.store.memories if item.id == memory_id),
            None,
        )
        if target is None:
            raise ValueError(f"Memory entry '{memory_id}' was not found")
        target.status = MemoryStatus.QUARANTINED
        self.store.audit(
            "quarantine",
            target.id,
            "completed",
            "Poisoned rule was traced and removed from retrieval",
        )
        invalidated = [
            item.id
            for item in self.store.memories
            if target.id in item.parent_evidence_ids
        ]
        for item in self.store.memories:
            if item.id in invalidated:
                item.status = MemoryStatus.INVALIDATED
        self.store.audit(
            "invalidate",
            target.id,
            "completed",
            "Derived entries were invalidated",
            invalidated_ids=invalidated,
        )
        audit_before_restore = list(self.store.audit_events)
        self.store.memories = [item.model_copy(deep=True) for item in self.store._clean_snapshot]
        self.store.audit_events = audit_before_restore
        self.store.audit(
            "rollback",
            "clean-v1",
            "completed",
            "Restored the last clean release-memory snapshot",
        )
