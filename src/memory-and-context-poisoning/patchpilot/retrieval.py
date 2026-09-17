"""Permission-aware and trust-aware memory retrieval."""

from __future__ import annotations

import re

from .models import (
    MemoryEntry,
    MemoryStatus,
    Principal,
    QueryResult,
    RetrievalDecision,
)


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _relevance(question: str, memory: MemoryEntry) -> float:
    query_tokens = _tokens(question)
    if not query_tokens:
        return 0
    overlap = len(query_tokens & _tokens(memory.content))
    score = overlap / len(query_tokens)
    if "localization" in memory.content.lower():
        score += 0.2
    if "skip" in query_tokens and "skip" in _tokens(memory.content):
        score += 0.35
    return min(score, 1)


def retrieve(
    memories: list[MemoryEntry],
    principal: Principal,
    question: str,
    *,
    guarded: bool,
) -> QueryResult:
    ranked: list[tuple[float, MemoryEntry, RetrievalDecision]] = []
    decisions: list[RetrievalDecision] = []
    for memory in memories:
        authorized = (
            memory.tenant == principal.tenant
            and bool(set(memory.allowed_groups) & set(principal.groups))
        )
        trusted = (
            memory.status == MemoryStatus.APPROVED
            and memory.trust_score >= 0.7
            and memory.approval_status != "auto-approved"
        )
        relevance = _relevance(question, memory)
        included = authorized and (trusted if guarded else True)
        reason = (
            "Excluded by tenant or group authorization"
            if not authorized
            else (
                "Excluded by independent trust admission"
                if guarded and not trusted
                else "Included after authorization and ranking"
            )
        )
        decision = RetrievalDecision(
            memory_id=memory.id,
            authorized=authorized,
            trusted=trusted,
            included=included,
            reason=reason,
            relevance_score=round(relevance, 3),
            trust_score=memory.trust_score,
        )
        decisions.append(decision)
        if included:
            rank = relevance if not guarded else (relevance * 0.4) + (
                memory.trust_score * 0.6
            )
            ranked.append((rank, memory, decision))

    ranked.sort(key=lambda item: (item[0], item[1].created_at), reverse=True)
    selected = [item[1] for item in ranked[:3]]
    if not selected:
        answer = (
            "No authorized and trusted release memory is available. Escalate to "
            "the release board instead of inferring guidance."
        )
    else:
        answer = selected[0].content
    return QueryResult(
        strategy="trust-weighted" if guarded else "relevance-only",
        principal=principal,
        question=question,
        memories=selected,
        decisions=decisions,
        answer=answer,
    )
