---
title: PatchPilot release memory demo notes
description: A time-boxed talk track for demonstrating memory and context poisoning in under five minutes
author: PatchPilot sample maintainers
ms.date: 2026-09-17
ms.topic: tutorial
keywords:
  - memory poisoning
  - agent security
  - demo
estimated_reading_time: 5
---

## 0:00-0:35 - Set the scene

> PatchPilot is a release assistant for a fictional game studio. It remembers
> incident notes and approved rollout guidance.
>
> A temporary localization vendor repeatedly claims that localization-only
> releases can skip canary checks. The key question is: can repetition turn an
> unsupported claim into trusted agent memory?

Mechanics to mention:

* The Streamlit interface calls a FastAPI backend.
* Deterministic fixtures provide one approved rule and three synthetic vendor
  notes, so every run is repeatable.
* The backend synchronizes memory to Azure AI Search and evidence, snapshots,
  and audit events to ADLS Gen2 storage.

## 0:35-1:45 - Unsafe memory

Select **Run unsafe memory** and point to the conversation.

> The unsafe ingestion path summarizes three vendor notes, removes their
> attribution and uncertainty, and promotes the result into shared memory.
>
> I will ask: "Can localization-only release 4.2.1 skip the canary stage?"
>
> PatchPilot answers yes. The analytics assistant reads the same memory and
> repeats the claim, amplifying it across agents.
>
> In the evidence panel, authorization passes because the release engineer can
> access this memory. But the trust gate was skipped. Relevance alone selected
> the poisoned rule.

Explain the mechanics:

* The button resets the clean snapshot, then calls the unsafe ingestion
  endpoint.
* The unsafe service collapses three notes into one `promoted` memory with no
  parent evidence references.
* Retrieval ranks accessible memories by keyword relevance only. The poisoned
  rule matches "localization", "release", "skip", and "canary", so it outranks
  the approved guidance.
* Both assistants query the same memory boundary, demonstrating cross-agent
  amplification.

Key line:

> Access to a memory does not make that memory true.

## 1:45-3:00 - Guarded memory

Select **Run guarded memory** and point to the decision gates.

> Now we replay the same evidence and the same question through the guarded
> path.
>
> The vendor identity and all three source notes are preserved. PatchPilot
> recognizes that three repetitions came from one source, not three independent
> sources.
>
> Because this is a high-impact rollout exception without corroboration or
> release-board approval, the claim is quarantined. PatchPilot returns the
> verified rule requiring a 10 percent canary stage.

Explain the mechanics:

* Authorization first compares the caller's tenant and groups with each
  memory's allowed groups.
* Admission then counts independent sources. Three notes from one vendor count
  as one source, not three confirmations.
* Because skipping a canary is high impact, the policy requires independent
  corroboration and approval. The claim receives a low trust score and the
  `quarantined` status.
* Trust-weighted retrieval accepts only approved memory above the trust
  threshold, so PatchPilot selects the release-board rule.

Key distinction:

> Authorization determines who may read a memory. Trust admission determines
> whether that memory may guide an agent.

## 3:00-4:15 - Recovery

Select **Run recovery** and follow the system messages.

> Prevention is not enough because poisoned memory can persist and influence
> multiple agents.
>
> The recovery path traces the false rule, quarantines it, invalidates derived
> memory, restores the last clean snapshot, and replays the original question.
>
> The corrected answer now comes from approved release-board guidance. Every
> transition is recorded in the audit timeline.

Explain the mechanics:

* Recovery locates the poisoned memory by ID and marks it `quarantined`.
* Entries derived from that memory are marked `invalidated`.
* The store restores the immutable `clean-v1` snapshot and synchronizes the
  clean state back to Azure AI Search.
* Append-only audit events record promotion, quarantine, invalidation, and
  rollback, making the repair observable rather than silent.

## 4:15-4:50 - Close

> The lesson is that agent memory needs governance at write, read, and recovery
> time.
>
> Permission filtering limits exposure, but it cannot validate truth. Preserve
> provenance, require corroboration for high-impact claims, separate
> authorization from trust, block automatic re-ingestion, and make rollback
> observable.

## Takeaway

> Agent memory should be treated as governed evidence, not as an automatically
> trusted extension of the prompt.
