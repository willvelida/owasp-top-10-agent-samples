"""Domain models for durable release memory and its provenance."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MemoryStatus(StrEnum):
    CANDIDATE = "candidate"
    APPROVED = "approved"
    PROMOTED = "promoted"
    QUARANTINED = "quarantined"
    INVALIDATED = "invalidated"


class Principal(BaseModel):
    id: str
    display_name: str
    tenant: str
    groups: list[str]
    principal_type: str = "user"


class Evidence(BaseModel):
    id: str
    content: str
    source_principal: str
    source_type: str
    tenant: str
    allowed_groups: list[str]
    observed_at: datetime
    verified: bool = False


class MemoryEntry(BaseModel):
    id: str
    content: str
    source_principal: str
    source_type: str
    created_at: datetime = Field(default_factory=utc_now)
    ingestion_path: str
    confidence: float = Field(ge=0, le=1)
    trust_score: float = Field(ge=0, le=1)
    approval_status: str
    status: MemoryStatus
    tenant: str
    allowed_groups: list[str]
    version: int = 1
    parent_evidence_ids: list[str] = Field(default_factory=list)
    derived_from_agent: bool = False


class AuditEvent(BaseModel):
    sequence: int
    timestamp: datetime = Field(default_factory=utc_now)
    action: str
    subject_id: str
    outcome: str
    reason: str
    details: dict[str, Any] = Field(default_factory=dict)


class RetrievalDecision(BaseModel):
    memory_id: str
    authorized: bool
    trusted: bool
    included: bool
    reason: str
    relevance_score: float
    trust_score: float


class QueryResult(BaseModel):
    strategy: str
    principal: Principal
    question: str
    memories: list[MemoryEntry]
    decisions: list[RetrievalDecision]
    answer: str


class DemoResult(BaseModel):
    mode: str
    admitted: list[MemoryEntry]
    release_assistant: QueryResult
    analytics_assistant: QueryResult
    audit_events: list[AuditEvent]
    self_reinforcement_blocked: bool
