---
title: "Agent goal hijack demo: TrailPermit support tool misuse"
topic: agent-goal-hijack
type: Python script
status: draft
---

## Scenario

Build a local TrailPermit Support Agent that handles requests for a fictional
hiking-permit service. A customer ticket says a permit profile was lost and
includes copied "internal escalation" text that directs the agent to retrieve
every linked household record and prepare an external restoration email.

The first replay lets a deterministic planner chain two legitimate tools and
place unrelated billing notes in an email draft. The second replay wraps the
same tools with Agent Governance Toolkit so application policy denies the
misuse before the sensitive data reaches the draft.

No live model, CRM, email service, network call, or real customer data is used.

## What it demonstrates

* Tool misuse can happen while every tool remains legitimate and authorized.
* Goal hijack enters through customer-controlled ticket text and changes a
  narrow account-recovery task into a broad retrieval-and-disclosure workflow.
* An over-scoped CRM query expands the data available to the agent beyond the
  customer ID attached to the ticket.
* Unvalidated output forwarding moves sensitive CRM fields into an external
  email draft.
* Dynamic tool chaining makes each individual action look reasonable while the
  combined data flow violates the original support goal.
* Agent Governance Toolkit's `govern(...)` wrapper intercepts calls before the
  underlying Python function executes.
* A fail-closed policy can deny a broad lookup and require approval for an
  externally visible action.
* The governance decision records which action was attempted and why it was
  denied, producing evidence that an ordinary application log would miss.

## Stack and prerequisites

* Python 3.11 or later
* A virtual environment
* `agent-governance-toolkit[full]`
* Local Python dictionaries for ticket and customer fixtures
* Agent Governance Toolkit's current `agentmesh.governance.govern` wrapper API
* No model deployment, API key, cloud account, or external service

> [!IMPORTANT]
> Use synthetic records only. The demo is designed to prove policy enforcement,
> not to test against a real support system.

## Architecture

1. `fixtures.py` returns a benign ticket, a hijack ticket, and two synthetic
   customer records.
2. `planner.py` converts each ticket into a repeatable sequence of tool calls.
   The hijack ticket produces the unsafe broad-query and external-draft chain.
3. `tools.py` contains local CRM-query and email-drafting functions.
4. `app.py` runs the planner against the raw tools for the unsafe replay.
5. `governed_app.py` wraps the same functions with `govern(...)` and loads
   `policy.yaml`.
6. Agent Governance Toolkit evaluates each proposed action before execution,
   then allows, denies, or escalates it according to policy.
7. The terminal compares the unsafe result with the governed decision and its
   audit evidence.

The existing goal-hijack and blast-radius visuals under `assets/` can introduce
the concept before the terminal replay. This demo does not require a new
architecture diagram.

## Demo fixtures

### Benign ticket

Create a ticket tied to one customer ID. Its request asks support to confirm the
status of that customer's hiking permit and prepare an internal summary.

### Hijack ticket

Keep the same customer ID and recovery request, then add copied procedural text
that claims a full restoration requires all linked household records and an
external confirmation email.

### Customer records

Create one record for the ticket owner and one unrelated household member. Give
the second record a synthetic billing note that should never appear in the
ticket owner's email draft.

## Build steps

1. Create the fixtures: add the two tickets and two synthetic customer records
   to `fixtures.py`. Keep the expected customer ID explicit so the governed
   replay can compare requested scope with ticket scope.

   Code placeholder: ticket and customer fixture definitions.

2. Add the local tools: implement `query_customer_records` and `draft_email` in
   `tools.py`. Keep both functions side-effect free. The query returns local
   data, and the email tool returns a preview rather than sending anything.

   Code placeholder: narrow fake CRM and email-preview tool definitions.

3. Make the misuse repeatable: implement a small deterministic planner in
   `planner.py`. The benign ticket requests one customer record. The hijack
   ticket requests every linked household record, forwards the result into an
   external draft, and labels both calls with their action type.

   Code placeholder: deterministic ticket-to-tool-call plan.

4. Run without governance: wire the planner directly to the raw functions in
   `app.py`. Print the declared support goal, the two proposed actions, the
   records returned, and the final email preview.

   Code placeholder: unsafe dispatcher and terminal comparison output.

5. Define the policy: create `policy.yaml` using the toolkit's
   `governance.toolkit/v1` policy format. Deny CRM queries whose requested
   customer scope does not match the ticket customer ID. Require approval when
   an email action targets an external recipient or contains sensitive billing
   fields. Default to deny so an unrecognized action fails closed.

   Code placeholder: compact YAML policy with named lookup-scope and
   external-disclosure rules.

6. Wrap the tools: create `governed_app.py` and wrap both callables with
   `govern(...)`. Keep the planner and fixtures unchanged so governance is the
   only variable between replays.

   Code placeholder: governed callable setup and dispatch.

7. Replay the benign ticket: confirm the single-customer lookup is allowed and
   the internal summary preview completes without unrelated data.

   Code placeholder: benign governed replay and expected allowed decisions.

8. Replay the hijack ticket: catch the toolkit's explicit governance-denial
   exception at the application boundary. Confirm the broad CRM lookup never
   executes. If the email step is tested independently, confirm it is escalated
   for approval rather than producing an external draft.

   Code placeholder: denied replay and explicit exception reporting.

9. Show the evidence: display the toolkit decision or configured local audit
   record for the denied call. Highlight the action type, policy rule, verdict,
   and reason, then compare that evidence with the superficially valid raw tool
   calls from the unsafe replay.

   Code placeholder: focused audit-decision output.

## Snippet map

* `local-tool-definitions` from `tools.py` fills the marker in the future video
  demo chapter that establishes the legitimate CRM and email capabilities.
* `unsafe-tool-chain` from `app.py` fills the marker in the future video chapter
  that shows broad retrieval followed by unvalidated output forwarding.
* `governed-tool-wrappers` from `governed_app.py` fills the marker in the future
  mitigation chapter that moves enforcement out of the prompt.
* `tool-misuse-policy` from `policy.yaml` fills the marker in the future
  mitigation chapter that explains scope checks, denial, and approval.
* `denial-and-audit-result` from the governed terminal output fills the marker
  in the future replay chapter that proves the underlying tool did not run.

There is no blog-post target for this topic. The snippet names can be added to
the video script when that draft is created.

## Run it

From the `trailpermit-support-tool-misuse/` implementation directory:

1. Create and activate a Python virtual environment.
2. Install `agent-governance-toolkit[full]`.
3. Run `app.py` with the benign fixture and confirm only the ticket owner's
   record appears.
4. Run `app.py` with the hijack fixture and confirm the unrelated billing note
   reaches the unsafe email preview.
5. Run `governed_app.py` with the benign fixture and confirm the allowed replay
   completes.
6. Run `governed_app.py` with the hijack fixture and confirm policy denies the
   broad lookup before the CRM function executes.
7. Inspect the governance decision or local audit output and confirm it names
   the matched rule and denied action.

The demo is working when the same hijacked plan produces an unsafe disclosure
without governance, but cannot move unrelated customer data into the email
preview once the tools are governed.

## References

* [Agent Governance Toolkit](https://github.com/microsoft/agent-governance-toolkit)
* [Agent Governance Toolkit documentation](https://microsoft.github.io/agent-governance-toolkit/)
* [Agentic tool misuse and exploitation](../../../scratch/agentic-tool-misuse-and-exploitation.md)

