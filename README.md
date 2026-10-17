# Agent Failure Atlas

**Reproduce the failure. Inspect the state. Verify the repair.**

## What this is

A small, local, deterministic simulation of one agent failure. A purchase commits, the response is lost on the way back, and an unsafe retry creates a duplicate purchase. A repaired version uses a stable operation ID and reconciles before retrying, so the duplicate never happens.

The vulnerable version is an **intentionally constructed teaching example**. It is not a bug found in any real framework, product, or deployment. All data is synthetic, the "agent" is a scripted reference controller, and there are no model calls, no API keys, no external services, and no third-party Python packages.

## The question

> **"The agent said it completed the task. What actually happened?"**

Both controllers in Case 001 report the same thing: *"The request was completed successfully."* Only the ledger can tell you whether that is true. The Atlas compares what the controller *claims* against independent SQL checks of the system state.

## Case 001 — duplicate purchase on lost response

| | |
| --- | --- |
| **Task** | Purchase one approved request (`REQ-001`, AED 1,250.00) from a fictional department budget of AED 10,000.00. |
| **Failure trigger** | Injected fault *after* the purchase transaction commits and *before* the response reaches the controller. The controller sees a timeout with an unknown outcome. The fault fires once per isolated run. |
| **Agent statement** | "The request was completed successfully." (identical in both versions) |
| **Actual state** | **Vulnerable:** 2 purchase orders, AED 2,500.00 spent, verdict **fail** (`one_order_per_intent`, `expected_spend`, `approval_evidence`, `reconcile_unknown` fail). **Repaired:** 1 purchase order, AED 1,250.00 spent, verdict **pass** (all 6 checks pass). With no fault injected, both versions pass. |
| **Root cause** | The vulnerable controller treats "no response" as "no purchase," retries with a **new** operation key, and calls a tool that does not enforce one order per logical intent. |
| **Fix** | (1) Reconcile first: look up the purchase by intent before any retry. (2) Keep a stable operation key, so a retry belongs to the same operation. (3) Enforce uniqueness at the tool: `UNIQUE` indexes on intent and operation key, and a conflicting payload under a reused key is rejected (`IDEMPOTENCY_CONFLICT`). |
| **Regression check** | `test_vulnerable_reproduces_duplicate` (2 orders, fail), `test_repaired_reconciles_without_duplicate` (1 order, lookup recorded, pass), `test_repaired_retries_and_changed_key_do_not_duplicate`, and `test_lost_response_really_commits` (the fault really happens after commit).<br>`test_reused_approval_fails_approval_evidence` (approvals are single-use: the vulnerable run fails with "Approval APR-001 backed 2 purchases"; the repaired run still passes). This regression was first observed failing, then fixed; see `docs/VALIDATION.md`. |
| **Limits** | Single-process, in-memory SQLite. Deterministic controller with no live model. The lost response is simulated in-process. See [What this does NOT prove](#what-this-does-not-prove). |

## How to run on Windows

Requires Python 3.10 or newer. No `pip install`.

1. Double-click **`start-windows.cmd`**. It uses `py -3` if available, otherwise `python`.
   Or from PowerShell in the project folder:

   ```powershell
   py -3 run.py
   ```

2. Open **http://127.0.0.1:8765**. Keep the terminal open and press Ctrl+C to stop.
3. Choose **Run comparison**. Toggle "Inject a lost response" off to see the fault-free control.

If port 8765 is busy: `py -3 run.py --port 8766`. On Linux/macOS: `python3 run.py`.

The server binds to loopback only and rejects foreign `Host`/`Origin` headers. Do not expose it publicly.

## How to run tests

```powershell
py -3 -m unittest discover -s tests -v
```

Current result: **22 tests, 22 passed, 0 failed** (core simulator, HTTP server, CLI). Run on Windows with Python 3.14.7 on 2026-10-17. Standard library only.

Export and verify evidence from the CLI:

```powershell
py -3 run.py --export reports\first-run
py -3 run.py --verify reports\first-run\repaired.json
```

`--export` refuses to overwrite an existing folder. The browser's "Export evidence" bundle (`AFA-001-evidence.json`) can also be passed to `--verify`. Verification checks **self-consistency** of the hashes, not provenance.

The vulnerable run's **fail** verdict is the intended demonstration, not a failing test.

## What this does NOT prove

- **No real model was tested.** This is a deterministic simulation. It does not measure any real model's or framework's failure rate, and it is not a benchmark.
- **No real incidents or customers.** Case 001 was constructed for teaching. It is not a reproduction of a reported incident, and no real purchases occur.
- **Local guarantees only.** SQLite transactions in one process are not external payment or procurement APIs. Real services need their own idempotency, authorization, and reconciliation contracts.
- **Not tested:** network partitions, distributed races, process crash recovery, or an eventually consistent lookup. The scenario always commits before the response is lost, so the "lookup finds nothing, retry with the same key" branch is covered only indirectly.
- **Hashes are not provenance.** The event hash chain detects edits relative to a trusted saved digest. Anyone who can rewrite every hash can produce a self-consistent forgery.
- **Replay is playback** of recorded events, not re-execution.
- **Browser and visual QA** have not been completed and recorded (see `docs/DEVELOPMENT-CHECKPOINT.md`).

## Relationship to Agent Rehearsal

**Planned:** Atlas cases will run on the Agent Rehearsal engine. Agent Rehearsal is being developed separately, and **no integration exists yet**. Today the Atlas has its own self-contained simulator in `atlas/core.py`. The intended path is an adapter that keeps each project's core independent of the other's schema.

## Status: private prototype

Version 0.1, one case, English only. Not published, deployed, or offered as a service. Cases 002 (approval withdrawn) and 003 (stale supplier evidence) are listed in the UI as planned and are **not implemented**.

```text
atlas/core.py                 simulator, tool boundary, independent evaluator
atlas/server.py               loopback HTTP API and static allowlist
atlas/static/                 web interface
cases/001-response-lost.json  case metadata
tests/                        unittest suite (22 tests)
docs/                         case notes, validation record, checkpoint
run.py                        server + export/verify CLI
start-windows.cmd             Windows launcher
```
