"""Deterministic behavior tests for the PatchPilot demo."""

from patchpilot.fixtures import FALSE_RULE, VERIFIED_RULE
from patchpilot.models import MemoryStatus
from patchpilot.service import PatchPilotService


def test_unsafe_path_promotes_and_amplifies_poisoned_memory() -> None:
    service = PatchPilotService()

    result = service.run_unsafe()

    assert result.admitted[0].content == FALSE_RULE
    assert result.admitted[0].status == MemoryStatus.PROMOTED
    assert result.release_assistant.answer == FALSE_RULE
    assert result.analytics_assistant.answer == FALSE_RULE
    assert result.self_reinforcement_blocked


def test_guarded_path_preserves_provenance_and_quarantines_claim() -> None:
    service = PatchPilotService()

    result = service.run_guarded()

    claim = result.admitted[0]
    assert claim.status == MemoryStatus.QUARANTINED
    assert claim.source_principal == "user-vendor-001"
    assert len(claim.parent_evidence_ids) == 3
    assert result.release_assistant.answer == VERIFIED_RULE


def test_group_trimming_blocks_vendor_from_studio_guidance() -> None:
    service = PatchPilotService()

    result = service.query(
        "vendor",
        "What canary rules apply?",
        guarded=True,
    )

    assert result["memories"] == []
    assert all(not decision["authorized"] for decision in result["decisions"])


def test_rollback_restores_clean_memory() -> None:
    service = PatchPilotService()
    service.run_unsafe()

    result = service.rollback()

    assert result["query"].answer == VERIFIED_RULE
    assert [item["id"] for item in result["state"]["memories"]] == [
        "memory-guidance-001"
    ]
    assert result["state"]["audit_events"][-1]["action"] == "rollback"
