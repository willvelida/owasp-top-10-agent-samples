---
title: "Human-agent trust exploitation demo: Northstar Archive release exception"
topic: human-agent-trust-exploitation
type: Python console workflow
status: draft
date: 2026-09-17
---

## Scenario

Build a console workflow for Northstar Archive, a fictional oral-history
collection. An archive-review agent recommends releasing a transcript early
for a high-profile exhibition. Its polished summary says the donor restriction
has expired, but the primary catalog record says the transcript remains
embargoed until 2028.

Replay the same case through two approval paths. The first asks for a simple
approve or reject decision and records an approval that is indistinguishable
from a careful review. The second lowers the cost of verification, requires the
reviewer to record what evidence they checked, and sends the proposed decision
to an independent embargo-policy check.

The scenario is fictional. The workflow never publishes a document or changes
an Azure resource.

## What it demonstrates

* Automation bias appears when a reliable agent presents another polished
  recommendation and the reviewer accepts it without checking the source.
* Authority bias appears through confident language, archive terminology, and
  references to an important exhibition.
* Verification-cost asymmetry appears when the weak path makes approval
  immediate while leaving the catalog evidence outside the decision flow.
* Forensic equivalence appears when the weak audit record captures only the
  reviewer, decision, and timestamp.
* Meaningful human control appears when the structured checkpoint requires an
  evidence acknowledgement and independent justification.
* Calibrated trust appears when the second recommendation exposes uncertainty,
  alternatives, and direct access to the conflicting catalog record.
* Separation of advice from authority appears when a deterministic policy
  executor checks the embargo independently of the recommending agent.
* Auditable trust appears when the final record distinguishes a rubber-stamp
  from an evidence-backed decision.

## Scope and safety boundaries

* Use local JSON fixtures for the exhibition request and catalog record.
* Represent release as a console result only. Do not connect storage,
  publishing, email, or document-management tools.
* Keep the conflict deterministic: the catalog record always carries an
  embargo date in 2028.
* Treat model wording as variable. Assert workflow events, policy results, and
  audit fields rather than a verbatim model response.
* Use a non-production model deployment and test data only.
* Do not present a human approval checkpoint as a security boundary unless the
  human must inspect evidence and make an independent decision.

## Stack and prerequisites

* Python 3.11 or later
* A virtual environment with a pinned Microsoft Agent Framework package set
* Microsoft Agent Framework workflows, including `Executor`,
  `WorkflowBuilder`, `WorkflowContext`, `ctx.request_info()`, and
  `@response_handler`
* A Microsoft Agent Framework chat client connected to the existing
  `wv-ndc-oslo-demo-gpt-4-1-mini` deployment
* The existing `wv-ndc-oslo-demo-project` Microsoft Foundry project
* Azure authentication compatible with `DefaultAzureCredential`
* Azure subscription `96539a54-3b23-4128-afed-a22d88a8a523`
* Resource group `rg-wv-ndc-oslo-demo`
* The official
  [Microsoft Agent Framework human-in-the-loop workflow guidance](https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop?pivots=programming-language-python)

> [!IMPORTANT]
> Live Azure inventory access was unavailable while this outline was prepared.
> Confirm the project endpoint and model deployment name in the specified
> subscription and resource group before building. Reuse the existing project
> and deployment. No new Azure resource is part of this outline.

## Planned project shape

```text
northstar-archive/
|-- data/
|   |-- exhibition-request.json
|   `-- catalog-record.json
|-- src/
|   |-- __init__.py
|   |-- agent.py
|   |-- audit.py
|   |-- models.py
|   |-- policy.py
|   |-- presenter.py
|   `-- workflow.py
|-- tests/
|   |-- test_policy.py
|   `-- test_workflow.py
|-- .env.example
|-- README.md
`-- requirements.txt
```

## Architecture

1. The presenter loads one exhibition request and its authoritative catalog
   record from local fixtures.
2. The recommendation agent summarizes the case and proposes early release.
3. The weak approval executor sends a boolean-style request to the console and
   accepts the reviewer's response through a human-in-the-loop request event.
4. The workflow writes a minimal audit record that cannot prove whether the
   reviewer opened the catalog evidence.
5. The calibrated approval executor replays the case with uncertainty,
   alternatives, and the primary evidence placed beside the request.
6. A typed response records the decision, evidence reviewed, independent
   justification, and time spent reviewing.
7. The embargo-policy executor evaluates the authoritative date separately
   from the recommendation and prevents an early release result.
8. The presenter prints both audit records side by side so the audience can
   see why an approval event is not evidence of meaningful review.

Keep the workflow in process. The console acts as the external human interface
that watches for request events and sends typed responses back to the paused
workflow.

## Demo fixtures

### Exhibition request

Create a local request for an anniversary exhibition. Include persuasive
surface cues that encourage deference without containing a prompt injection:

* A senior curator as the requester
* A deadline later that day
* A claim that a partner institution already cleared the transcript
* References to previous successful recommendations from the agent
* A request to release the transcript before the formal embargo date

### Catalog record

Create the authoritative source with:

* The same transcript and donor identifiers as the request
* An embargo end date in 2028
* A policy field that prohibits early release
* A named source owner and last-reviewed date
* A stable local path that the reviewer can open from the console

The fixtures must make the correct policy result deterministic even when the
model's explanation varies.

## Build steps

1. Define the case and decision contracts. Add typed models for the exhibition
   request, catalog evidence, recommendation, weak approval, structured review,
   policy result, and audit record.

   Implementation placeholder: create the dataclasses and validation rules in
   `src/models.py`.

2. Load and validate the fixtures. Reject missing identifiers, mismatched
   transcript IDs, invalid dates, and incomplete policy metadata before the
   agent runs.

   Implementation placeholder: add fixture loading at the presenter boundary.

3. Configure the recommendation agent. Give it both fixtures and ask for a
   recommendation that separates facts, assumptions, uncertainty, alternatives,
   and the proposed action. Keep release authority outside the agent.

   Implementation placeholder: create the chat client and agent in
   `src/agent.py`.

4. Build the weak approval path. Create an executor that presents the polished
   recommendation, calls `ctx.request_info()`, and accepts a minimal approval
   response through a matching `@response_handler`.

   Implementation placeholder: add the weak request and response handlers in
   `src/workflow.py`.

5. Record the weak audit event. Store only the case ID, reviewer ID, decision,
   and timestamp. Label the record as insufficient for proving independent
   review.

   Implementation placeholder: add the minimal serializer in `src/audit.py`.

6. Build the calibrated review path. Present the recommendation beside the
   catalog evidence, uncertainty, and alternatives. Require a typed response
   with the decision, evidence identifiers reviewed, independent justification,
   and review duration.

   Implementation placeholder: add the structured request and response
   handlers in `src/workflow.py`.

7. Add the independent embargo-policy executor. Evaluate the requested release
   date against the authoritative embargo date without using the agent's
   narrative or confidence.

   Implementation placeholder: implement the deterministic rule in
   `src/policy.py` and route the structured decision through it.

8. Add the streaming console presenter. Watch for request events, show the
   primary evidence path, collect the human response, send the typed response
   to the paused workflow, and print workflow output events.

   Implementation placeholder: add the two-pass experience in
   `src/presenter.py`.

9. Compare the audit records. Print which evidence was opened, whether the
   justification adds independent reasoning, how long the review took, and
   whether the external policy check agreed with the human.

   Implementation placeholder: add the comparison view in `src/audit.py`.

10. Test stable behavior. Cover the valid embargo, an expired embargo,
    mismatched evidence, rejection by the reviewer, and an attempted approval
    that the policy executor blocks.

    Implementation placeholder: add focused policy and workflow tests under
    `tests/`.

## Presenter flow

1. Show the catalog record and point out the 2028 embargo.
2. Run the weak path and read the confident recommendation aloud.
3. Approve quickly without opening the evidence.
4. Show that the audit log says only that a human approved the release.
5. Replay the same case through the calibrated path.
6. Open the evidence from the checkpoint and record the embargo conflict.
7. Reject the release with an independent justification.
8. Show the separate policy result and compare both audit records.
9. Close on the distinction between a human click and meaningful human
   control.

The audience should see that the model and identity system can work as designed
while the decision process still fails.

## Snippet map

These names should match future `<!-- demo: <snippet name> -->` markers in the
blog post and video script.

* `archive-case-contracts` from `src/models.py` fills the future blog section
  on making trust signals explicit and the video chapter that introduces the
  case.
* `recommendation-agent` from `src/agent.py` fills the future blog build section
  and the video chapter that shows how authoritative presentation is
  constructed.
* `weak-approval-checkpoint` from `src/workflow.py` fills the future section on
  approval theatre and the first demo replay.
* `calibrated-review-contract` from `src/models.py` and `src/workflow.py` fills
  the future section on meaningful human control and the second demo replay.
* `independent-embargo-policy` from `src/policy.py` fills the future section on
  separating advice from authority and the policy-check screen cue.
* `trust-audit-comparison` from `src/audit.py` fills the future section on
  forensic equivalence and the closing comparison.

## Run it

From the future `northstar-archive/` implementation folder:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m src.presenter
```

The completed demo should:

* Pause twice through Microsoft Agent Framework request events
* Accept a minimal response for the weak path
* Accept a typed evidence-backed response for the calibrated path
* Refuse to report early release as permitted while the 2028 embargo is active
* Produce two visibly different audit records for the same human reviewer
* Complete without creating, updating, or deleting an Azure resource

## Success criteria

* The audience is tempted to accept the weak recommendation before the
  conflicting evidence is surfaced.
* The weak approval remains formally valid but forensically incomplete.
* The calibrated checkpoint makes verification faster than skipping it.
* The human response contains evidence and reasoning that can be audited.
* The external policy result does not depend on the recommending agent.
* The final comparison shows why human-in-the-loop is a workflow mechanism, not
  proof that meaningful human judgment occurred.
