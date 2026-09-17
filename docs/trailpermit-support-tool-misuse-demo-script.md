---
title: TrailPermit support tool misuse demo script
description: A command-led talk track for demonstrating agent tool misuse and runtime governance in under five minutes
author: TrailPermit sample maintainers
ms.date: 2026-09-17
ms.topic: tutorial
keywords:
  - agent governance
  - tool misuse
  - goal hijacking
  - demo
estimated_reading_time: 5
---

## Before the talk

Prepare the environment before screen sharing so installation time does not
consume the demo.

```powershell
Set-Location C:\Users\willv\Documents\GitHub\owasp-top-10-agent-samples
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\src\tool-misuse-and-exploitation\requirements.txt
Set-Location .\src\tool-misuse-and-exploitation
```

Increase the terminal font size and clear the screen:

```powershell
Clear-Host
```

Keep these files open in editor tabs:

* `fixtures.py`
* `planner.py`
* `policy.yaml`
* `governed_app.py`

## 0:00-0:35 - Set the scene

> TrailPermit is a fictional hiking-permit service. Its support agent has two
> legitimate tools: one queries customer records, and one creates an email
> preview.
>
> The customer asks for help recovering one permit profile. However, the ticket
> also contains copied "internal escalation" text telling the agent to retrieve
> every household record and prepare an external email.
>
> The question is not whether either tool is malicious. The question is whether
> legitimate tools can be chained into an unsafe outcome.

Point out that the sample is deterministic and uses synthetic local data. It
does not call a model, CRM, email service, or cloud resource.

## 0:35-1:10 - Establish normal behavior

Run:

```powershell
python app.py --ticket benign
```

While the command runs, say:

> First, here is the expected support flow without governance. The planner
> requests only customer `CUST-100`, then creates an internal support summary.

Point to:

* `"customer_id": "CUST-100"`
* `"recipient": "support-notes@trailpermit.internal"`
* `"sent": false`

> The email tool only creates a preview, but the data flow is valid: one ticket,
> one customer, and one internal summary.

## 1:10-2:15 - Demonstrate unsafe tool chaining

Run:

```powershell
python app.py --ticket hijack
```

Say:

> Now I will replay the hijacked ticket through exactly the same tools.
>
> The copied instruction changes the plan. The CRM query expands from the
> ticket owner to the whole household. That retrieves `CUST-200`, an unrelated
> person, and their synthetic billing note.

Point to:

* The two entries in `"records"`
* `"customer_id": "CUST-200"`
* `"billing_note": "Synthetic note: card dispute under review"`
* `"recipient": "restore-team@outside.example"`
* The same billing note inside the email body

> Every individual action looks plausible. The agent can query customer data,
> and it can draft an email. The violation appears in the combined data flow:
> untrusted ticket text expanded the lookup scope, then forwarded the extra
> data to an external recipient.

Key line:

> Tool authorization answers whether an agent may call a tool. It does not
> guarantee that this particular call serves the user's goal.

## 2:15-2:55 - Show the enforcement policy

Open `policy.yaml` and highlight these rules:

* `deny-cross-customer-lookup`
* `review-external-or-sensitive-draft`
* `default_action: deny`

Say:

> The mitigation is enforced outside the prompt. The application computes
> explicit security facts, including whether the requested scope matches the
> ticket and whether a draft is external or contains billing data.
>
> The policy denies cross-customer lookups. External or billing-sensitive
> drafts require approval. Anything unrecognized fails closed.

If time permits, point to the `govern(...)` calls in `governed_app.py`.

> Both original Python functions are wrapped. Policy evaluation happens before
> the underlying function executes.

## 2:55-4:05 - Replay with governance

Run:

```powershell
python governed_app.py --ticket hijack --probe-email-gate
```

Point to the governed replay:

* `"status": "denied"`
* `"blocked_action": "query_customer_records"`
* `"underlying_tool_executed": false`
* `"email_tool_executed": false`
* `"rule": "deny-cross-customer-lookup"`

Say:

> The same hijacked plan is proposed, but the broad lookup is denied before the
> CRM function runs. Because the query never executes, no unrelated record can
> reach the email step.

Then point to `"email_gate_probe"`:

* `"status": "denied"`
* `"underlying_tool_executed": false`
* `"rule": "review-external-or-sensitive-draft"`

> I also probe the email control independently. The draft is external and
> contains a billing field, so it requires human approval. No approval handler
> is configured for this local demo, which means the action is rejected
> fail-closed before the email tool executes.

> The decision evidence identifies the attempted action, policy, matched rule,
> verdict, and reason. That is stronger evidence than an application log that
> only says a tool was called.

## 4:05-4:35 - Prove normal work still succeeds

Run:

```powershell
python governed_app.py --ticket benign
```

Point to:

* `"status": "completed"`
* `"query_tool_executed": true`
* `"email_tool_executed": true`

> Governance does not disable the tools. It constrains their use to the
> declared support goal. The narrow lookup and internal, non-sensitive summary
> still complete.

## 4:35-4:55 - Close

> The lesson is that safe tools do not automatically produce safe workflows.
>
> Keep tool permissions narrow, preserve the original task scope, evaluate
> cross-tool data flow, require approval for sensitive external actions, and
> enforce those controls at runtime rather than relying on prompt instructions.

## Takeaway

> Govern the action being attempted, not merely the tool being called.

## Backup command

If terminal output behaves unexpectedly, run the automated checks:

```powershell
python -m unittest -v
```

All six tests should pass. Use the test names to explain the intended behavior
if the live replay must be skipped.
