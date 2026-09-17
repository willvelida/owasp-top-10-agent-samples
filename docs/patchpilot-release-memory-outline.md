---
title: "Memory and Context Poisoning demo: PatchPilot release memory"
topic: memory-and-context-poisoning
type: python-web-app
status: draft
date: 2026-09-17
---

## Scenario

PatchPilot is a RAG assistant for an indie game studio's release teams. It
remembers incident notes and approved rollout guidance, but a temporary
localization vendor repeatedly claims that localization-only releases can skip
canary checks.

An unsafe ingestion path summarizes those claims, removes their attribution,
and promotes the result into shared memory. A release engineer later retrieves
the poisoned rule as authoritative guidance, while an analytics agent
reinforces it through a shared index.

The hardened path separates authorization from trust. Azure AI Search
document-level access control limits which memories each signed-in user can
retrieve. A memory-admission policy then preserves provenance, scores trust,
quarantines unverified claims, blocks automatic re-ingestion, and supports
rollback.

## What it demonstrates

* Repeated-claim ingestion maps to a scripted vendor session that submits the
  same unsupported rollout exception through several incident notes.
* Attribution collapse maps to an unsafe summarizer that turns attributed,
  uncertain reports into a generalized release rule.
* Retrieval becoming authority maps to a relevance-only query that ranks the
  poisoned rule above verified release guidance.
* Shared-memory amplification maps to release and analytics agents reading
  from the same promoted-memory index.
* Document-level access control maps to ADLS Gen2 ACL or RBAC metadata
  synchronized into Azure AI Search and enforced from the signed-in caller's
  Microsoft Entra token.
* Trust-weighted retrieval maps to a guarded query that combines semantic
  relevance with source, approval, freshness, tenant, and status signals.
* Segmentation maps to separate studio-team and vendor scopes so one
  principal's accessible content does not become global memory.
* Quarantine and rollback map to an immutable audit trail, a quarantine store,
  and replay from the last clean memory snapshot.
* The limits of authorization map to a comparison where an authorized user can
  still submit a false claim. Access control contains exposure but does not
  validate truth.

## Stack and prerequisites

* Python 3.12
* FastAPI for the backend API
* Streamlit for the operator and incident-review interface
* Azure Identity for local developer credentials and signed-in user tokens
* Azure AI Search for indexed memory and query-time document trimming
* ADLS Gen2 for source documents with ACL or RBAC permission metadata
* Azure OpenAI as an optional provider for summarization and grounded answers
* Deterministic local fixtures for rehearsing the complete poisoning and
  recovery sequence before Azure resources exist
* The `2026-08-01-preview` Azure AI Search REST API, or a preview Python SDK
  version that explicitly supports native permission filters
* Future deployment target: Azure subscription
  `96539a54-3b23-4128-afed-a22d88a8a523`
* Microsoft Entra app registrations and delegated search access for a future
  deployed version

> [!IMPORTANT]
> This outline does not provision resources. Native ACL and RBAC permission
> filtering is a preview capability, so the implementation must confirm the
> supported API or SDK version before deployment.

## Architecture

* A fixture generator creates verified release guidance, attributed vendor
  claims, incident notes, and a clean memory snapshot.
* ADLS Gen2 holds the source documents and their studio-team or vendor
  permissions.
* An unsafe ingestion pipeline summarizes every eligible note and writes
  directly to promoted memory.
* A guarded ingestion pipeline preserves provenance, calculates trust signals,
  and routes entries to candidate, approved, or quarantined memory.
* Azure AI Search indexes approved memory with synchronized permission
  metadata, provenance, trust, status, tenant, and version fields.
* The FastAPI query layer passes the signed-in user's Microsoft Entra token to
  Azure AI Search for query-time document trimming.
* A release assistant and an analytics assistant retrieve from the same memory
  boundary to expose cross-agent amplification.
* An audit and recovery service records every transition and restores the last
  clean snapshot after the poisoned entry is quarantined.
* The Streamlit interface compares unsafe and guarded ingestion, retrieval,
  agent output, and recovery side by side.
* Add an architecture diagram under `assets/` when the implementation begins.
  Show permission trimming and trust admission as separate gates.

## Build steps

1. Create the release-memory fixtures. Define verified studio guidance,
   repeated vendor claims, user and group identities, tenant boundaries, and a
   clean snapshot. This establishes a deterministic baseline.

   Code placeholder: fixture models and seed data.

2. Model durable memory metadata. Give each entry a source principal,
   timestamp, ingestion path, confidence, approval status, tenant, allowed
   groups, version, and parent evidence references. This preserves attribution
   through summarization.

   Code placeholder: memory and provenance models.

3. Build the unsafe ingestion path. Accept repeated incident notes, summarize
   them without preserving uncertainty or attribution, and promote the result
   directly into shared memory. This reproduces context becoming trusted
   memory.

   Code placeholder: unsafe ingestion service.

4. Build the guarded memory-admission path. Detect repeated claims from one
   source, require corroboration for high-impact rollout rules, score trust,
   and route unverified entries to quarantine. This prevents repetition from
   becoming validation.

   Code placeholder: admission policy and quarantine routing.

5. Define the permission-aware search schema. Store the searchable content,
   synchronized ACL or RBAC metadata, provenance, trust, status, tenant, and
   version fields. Keep authorization metadata distinct from trust metadata.

   Code placeholder: index schema and field mapping.

6. Plan ADLS Gen2 permission ingestion. Assign studio-team and vendor
   permissions to source documents, enable native permission filters, and
   preserve the permission metadata during indexing. This creates the
   document-level security boundary.

   Code placeholder: ingestion and permission synchronization setup.

7. Implement signed-in retrieval. Acquire the caller's Microsoft Entra token,
   forward it through the `x-ms-query-source-authorization` request header, and
   confirm that Azure AI Search excludes unauthorized documents before
   grounding. This follows the signed-in query pattern from the reference
   sample without copying its scenario or code.

   Code placeholder: authenticated search client.

8. Compare relevance-only and trust-weighted retrieval. Run the same release
   question through both paths. The unsafe path should surface the poisoned
   memory, while the guarded path should exclude quarantined or low-trust
   entries even when they are semantically relevant.

   Code placeholder: retrieval strategies and comparison result.

9. Demonstrate shared-memory amplification. Let the release assistant and
   analytics assistant consume the unsafe memory, then show how the second
   agent's output can reinforce the false rule if automatic re-ingestion is
   enabled.

   Code placeholder: two assistant adapters and re-ingestion guard.

10. Add quarantine, audit, and rollback. Trace the poisoned rule to its source
    notes, quarantine it, invalidate derived entries, restore the last clean
    snapshot, and replay the queries. This makes recovery observable and
    reversible.

    Code placeholder: audit events, dependency invalidation, and snapshot
    restore.

11. Build the comparison interface. Show the source notes, memory transitions,
    caller identity, permission decisions, trust decisions, retrieved context,
    agent answers, and rollback result in one timeline.

    Code placeholder: Streamlit views and FastAPI endpoints.

12. Add deterministic tests. Verify cross-group trimming, poisoned-memory
    promotion in the unsafe path, quarantine in the guarded path, blocked
    self-reinforcement, provenance retention, and clean results after rollback.

    Code placeholder: unit and integration tests.

## Snippet map

Each name is reserved for a future
`<!-- demo: <snippet name> -->` marker in the blog post and video script.

* `memory-provenance-model` from `app/models/memory.py` fills the future blog
  section about attribution collapse and the video chapter about durable
  context.
* `unsafe-memory-promotion` from `app/services/unsafe_ingestion.py` fills the
  future blog section about repeated claims becoming memory and the video
  poisoning walkthrough.
* `guarded-memory-admission` from `app/services/admission.py` fills the future
  blog section about validating memory writes and the video mitigation
  walkthrough.
* `permission-aware-index` from `app/search/schema.py` fills the future blog
  section about memory segmentation and the video architecture chapter.
* `signed-in-document-trimming` from `app/search/retrieval.py` fills the future
  blog section about query-time authorization and the video access-control
  demonstration.
* `trust-weighted-retrieval` from `app/search/ranking.py` fills the future blog
  section about trust versus relevance and the video comparison.
* `quarantine-and-rollback` from `app/services/recovery.py` fills the future
  blog section about recovery and the video rollback demonstration.

## Run it

The implementation should support two modes.

### Local rehearsal

1. Install the Python dependencies.
2. Seed the deterministic clean and poisoned fixtures.
3. Start the FastAPI backend and Streamlit interface.
4. Run the poisoning sequence as the vendor, then query as the release
   engineer.
5. Switch from unsafe to guarded mode, quarantine the entry, and replay from
   the clean snapshot.

Working means the unsafe path promotes and retrieves the false release rule,
both assistants amplify it, and the guarded path preserves attribution,
quarantines the claim, blocks re-ingestion, and returns only verified guidance
after rollback.

### Future Azure-backed run

1. Select subscription `96539a54-3b23-4128-afed-a22d88a8a523`.
2. Provision the approved Azure resources in a later deployment phase.
3. Upload the fixtures to ACL-protected ADLS Gen2 paths.
4. Synchronize permission metadata into Azure AI Search.
5. Sign in as the vendor and release engineer test identities.
6. Confirm that the same query returns different authorized document sets,
   then repeat the trust, quarantine, and rollback sequence.

Working means Azure AI Search first trims documents to the caller's effective
permissions, then the application applies the independent memory-trust policy.
The interface must explain both decisions rather than presenting an empty or
filtered result as a successful answer.

## Reference boundaries

* The topic notes define the poisoning sequence, persistence risks, shared
  memory amplification, and mitigation goals.
* The Microsoft Learn document-level access control overview defines the
  permission-ingestion and query-time enforcement patterns.
* The Azure sample informs the signed-in Python RAG architecture, citation
  surface, and separation between client authentication and backend retrieval.
* PatchPilot, its game-release domain, its data, and its poisoning sequence are
  original to this demo.
