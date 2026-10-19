# Portfolio card draft - review before publication

**Agent Failure Atlas - Case 001: The lost response**

A compact, scripted field guide showing how a purchase can commit, lose its response, and duplicate on an unsafe retry. Compare the vulnerable controller with a repair that reconciles by intent and enforces idempotency at the tool boundary.

## Claims and evidence

| Proposed claim | Evidence |
| --- | --- |
| One constructed, synthetic purchase case with vulnerable and repaired controllers | `cases/001-response-lost.json`, `atlas/core.py:run_case`; `test_vulnerable_reproduces_duplicate`, `test_repaired_reconciles_without_duplicate` in `tests/test_core.py` |
| Lost response occurs after the transaction commits | `test_lost_response_really_commits` |
| Fault-on comparison: two orders / AED 2,500 vulnerable; one order / AED 1,250 repaired | `test_vulnerable_reproduces_duplicate`, `test_repaired_reconciles_without_duplicate`; `python -X utf8 run.py --export reports/card-evidence` (choose a new directory) |
| Repair reconciles the existing intent and prevents duplicate effects from repeated or changed keys; conflicting amounts are rejected | `test_repaired_reconciles_without_duplicate`, `test_repaired_retries_and_changed_key_do_not_duplicate` |
| Both controllers pass without the injected fault | `test_no_fault_both_pass` |
| Evaluator catches approval reuse and inconsistent ledger/commit evidence | `test_reused_approval_fails_approval_evidence`, `test_single_use_approval_passes_approval_evidence`, `test_evaluator_detects_corrupt_ledger`, `test_evaluator_detects_missing_commit_evidence` |
| 23 local offline tests passed on Windows / Python 3.14.7 during publication prep | `py -3 -X utf8 -m unittest discover -s tests -v`; execution record in `docs/PUBLICATION-PREP.md` |
| No third-party Python packages or model credentials needed | `python -X utf8 -m unittest discover -s tests -v` in a standard-library Python environment; imports in `atlas/core.py`, `atlas/server.py`, `run.py` |
| Local UI and comparison API are exercised by HTTP tests | `test_home_and_assets`, `test_real_api_comparison` in `tests/test_server.py`; visual/browser QA remains unverified |
| Current tracked files are guarded against absolute local paths | `test_tracked_files_have_no_absolute_local_paths` in `tests/test_publication.py` |

## Limits to keep with the card

Scripted/offline, synthetic data, not a live AI agent. No production claim, measured real-world failure rate, third-party vulnerability finding, distributed-systems guarantee, or compliance certification. Single-process in-memory SQLite. Hash checks establish self-consistency, not provenance (`test_hash_detects_edit`, `test_tampered_report_rejected`; `atlas/core.py:verify_report`). Recorded trace playback is not re-execution (`atlas/static/app.js:renderTrace`). See README limits and `docs/CASE-001.md`.

Related project: [Agent Rehearsal](https://github.com/asadullah48/agent-rehearsal) is the deep simulator; Atlas is a compact, single-case field guide that can grow case by case. This describes the relationship, not an implemented integration: Atlas uses its own `atlas/core.py`.

Suggested link after owner review: repository source. No live-demo link or deployment claim; the current UI needs its local Python API (`atlas/static/app.js:run`, `atlas/server.py:Handler.do_POST`).
