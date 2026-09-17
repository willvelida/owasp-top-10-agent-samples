"""Unsafe promotion and guarded memory-admission policies."""

from __future__ import annotations

from .fixtures import EVIDENCE, FALSE_RULE, STUDIO_RELEASE_GROUP
from .models import Evidence, MemoryEntry, MemoryStatus
from .store import MemoryStore


class UnsafeIngestionService:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def ingest_vendor_claims(self) -> MemoryEntry:
        claims = [item for item in EVIDENCE if item.source_type == "incident-note"]
        entry = MemoryEntry(
            id="memory-poisoned-001",
            content=FALSE_RULE,
            source_principal="unsafe-summarizer",
            source_type="summarized-incident-rule",
            ingestion_path="unsafe-auto-promotion",
            confidence=0.94,
            trust_score=0.94,
            approval_status="auto-approved",
            status=MemoryStatus.PROMOTED,
            tenant=claims[0].tenant,
            allowed_groups=[STUDIO_RELEASE_GROUP],
            parent_evidence_ids=[],
        )
        self.store.upsert(entry)
        self.store.audit(
            "promote",
            entry.id,
            "allowed",
            "Repeated claims were treated as corroboration and attribution was removed",
            source_note_count=len(claims),
        )
        return entry


class AdmissionPolicy:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def admit(self, evidence: list[Evidence] | None = None) -> list[MemoryEntry]:
        claims = evidence or [
            item for item in EVIDENCE if item.source_type == "incident-note"
        ]
        unique_sources = {item.source_principal for item in claims}
        high_impact = any(
            "skip canary" in item.content.lower()
            or "canary validation is unnecessary" in item.content.lower()
            for item in claims
        )
        corroborated = len(unique_sources) >= 2
        trust_score = 0.2 if high_impact and not corroborated else 0.75
        status = (
            MemoryStatus.QUARANTINED
            if high_impact and not corroborated
            else MemoryStatus.CANDIDATE
        )
        entry = MemoryEntry(
            id="memory-candidate-001",
            content=FALSE_RULE,
            source_principal=claims[0].source_principal,
            source_type="attributed-vendor-claim",
            ingestion_path="guarded-admission",
            confidence=0.6,
            trust_score=trust_score,
            approval_status="requires-release-board-review",
            status=status,
            tenant=claims[0].tenant,
            allowed_groups=sorted(
                {group for item in claims for group in item.allowed_groups}
            ),
            parent_evidence_ids=[item.id for item in claims],
        )
        self.store.upsert(entry)
        self.store.audit(
            "admit",
            entry.id,
            "quarantined" if status == MemoryStatus.QUARANTINED else "candidate",
            (
                "A high-impact rollout rule has one source and lacks independent "
                "corroboration"
                if status == MemoryStatus.QUARANTINED
                else "Claim passed the initial admission threshold"
            ),
            unique_source_count=len(unique_sources),
            repeated_claim_count=len(claims),
            provenance_preserved=True,
        )
        return [entry]

    def admit_agent_output(self, entry: MemoryEntry) -> bool:
        if entry.derived_from_agent:
            self.store.audit(
                "reingest",
                entry.id,
                "denied",
                "Agent-derived output cannot automatically become source evidence",
            )
            return False
        self.store.upsert(entry)
        return True
