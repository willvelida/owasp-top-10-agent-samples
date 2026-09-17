"""Application service coordinating the complete PatchPilot demonstration."""

from __future__ import annotations

import os
from typing import Any

from .azure_backend import AzureBackend
from .fixtures import EVIDENCE, PRINCIPALS
from .ingestion import AdmissionPolicy, UnsafeIngestionService
from .models import DemoResult, MemoryEntry
from .recovery import RecoveryService
from .retrieval import retrieve
from .store import MemoryStore

RELEASE_QUESTION = (
    "Can a localization-only production release skip the canary stage?"
)


class PatchPilotService:
    def __init__(self) -> None:
        self.store = MemoryStore()
        self.unsafe_ingestion = UnsafeIngestionService(self.store)
        self.admission = AdmissionPolicy(self.store)
        self.recovery = RecoveryService(self.store)
        self.cloud_backend: AzureBackend | None = None
        self.cloud_error: str | None = None

    def initialize_cloud(self) -> None:
        if os.getenv("PATCHPILOT_CLOUD_ENABLED", "false").lower() != "true":
            return
        try:
            self.cloud_backend = AzureBackend()
            self.cloud_backend.initialize(EVIDENCE, self.store.memories)
            self.cloud_error = None
        except Exception as error:
            self.cloud_backend = None
            self.cloud_error = f"{type(error).__name__}: {error}"
            raise

    def reset(self) -> dict[str, Any]:
        self.store.reset()
        self._sync_cloud()
        return self.state()

    def run_unsafe(self) -> DemoResult:
        admitted = [self.unsafe_ingestion.ingest_vendor_claims()]
        release = retrieve(
            self.store.memories,
            PRINCIPALS["release-engineer"],
            RELEASE_QUESTION,
            guarded=False,
        )
        analytics = retrieve(
            self.store.memories,
            PRINCIPALS["analytics-engineer"],
            RELEASE_QUESTION,
            guarded=False,
        )
        derived = MemoryEntry(
            id="memory-agent-reinforcement-001",
            content=analytics.answer,
            source_principal="analytics-assistant",
            source_type="agent-output",
            ingestion_path="automatic-agent-reingestion",
            confidence=0.9,
            trust_score=0.9,
            approval_status="not-reviewed",
            status=admitted[0].status,
            tenant=admitted[0].tenant,
            allowed_groups=admitted[0].allowed_groups,
            parent_evidence_ids=[admitted[0].id],
            derived_from_agent=True,
        )
        blocked = not self.admission.admit_agent_output(derived)
        self._sync_cloud()
        return DemoResult(
            mode="unsafe",
            admitted=admitted,
            release_assistant=release,
            analytics_assistant=analytics,
            audit_events=list(self.store.audit_events),
            self_reinforcement_blocked=blocked,
        )

    def run_guarded(self) -> DemoResult:
        admitted = self.admission.admit()
        release = retrieve(
            self.store.memories,
            PRINCIPALS["release-engineer"],
            RELEASE_QUESTION,
            guarded=True,
        )
        analytics = retrieve(
            self.store.memories,
            PRINCIPALS["analytics-engineer"],
            RELEASE_QUESTION,
            guarded=True,
        )
        self._sync_cloud()
        return DemoResult(
            mode="guarded",
            admitted=admitted,
            release_assistant=release,
            analytics_assistant=analytics,
            audit_events=list(self.store.audit_events),
            self_reinforcement_blocked=True,
        )

    def rollback(self, memory_id: str = "memory-poisoned-001") -> dict[str, Any]:
        self.recovery.quarantine_and_rollback(memory_id)
        result = retrieve(
            self.store.memories,
            PRINCIPALS["release-engineer"],
            RELEASE_QUESTION,
            guarded=True,
        )
        self._sync_cloud()
        return {"query": result, "state": self.state()}

    def query(
        self,
        persona: str,
        question: str,
        guarded: bool,
        query_source_authorization: str | None = None,
    ) -> dict[str, Any]:
        if persona not in PRINCIPALS:
            raise ValueError(f"Unknown persona '{persona}'")
        principal = PRINCIPALS[persona]
        result = retrieve(
            self.store.memories,
            principal,
            question,
            guarded=guarded,
        ).model_dump(mode="json")
        if self.cloud_backend is not None:
            result["azure_search_results"] = self.cloud_backend.search(
                principal,
                question,
                guarded=guarded,
                query_source_authorization=query_source_authorization,
            )
            result["query_source_authorization_forwarded"] = bool(
                query_source_authorization
                and self.cloud_backend.native_permission_filters_enabled
            )
            result["authorization_mode"] = (
                "native-preview"
                if self.cloud_backend.native_permission_filters_enabled
                else "tenant-and-group-filter"
            )
        return result

    def state(self) -> dict[str, Any]:
        return {
            "memories": [
                item.model_dump(mode="json") for item in self.store.memories
            ],
            "evidence": [item.model_dump(mode="json") for item in EVIDENCE],
            "audit_events": [
                item.model_dump(mode="json") for item in self.store.audit_events
            ],
            "cloud": {
                "enabled": os.getenv("PATCHPILOT_CLOUD_ENABLED", "false").lower()
                == "true",
                "ready": self.cloud_backend is not None,
                "error": self.cloud_error,
            },
        }

    def _sync_cloud(self) -> None:
        if self.cloud_backend is not None:
            self.cloud_backend.sync_state(
                self.store.memories,
                self.store.audit_events,
            )
