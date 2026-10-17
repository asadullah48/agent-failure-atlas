# Validation record — 2026-10-17

Executed in the Codex Linux workspace, not on the user's Windows machine.

## Automated checks

Command: `python3 -m unittest discover -s tests -v`

Result: **20 tests passed**. Includes simulator state, genuine commit before response loss, vulnerable duplication, repaired reconciliation, idempotency, conflicting payload, approval denial, independent evaluator negative controls, hash edit detection, HTTP validation, local origin/host restrictions, path allowlist, evidence export, non-overwrite behavior, and comparison-bundle verification.

JavaScript syntax: `node --check atlas/static/app.js` — exit 0.

CLI: `python3 run.py --export <new-directory>` — exit 0:

```text
vulnerable: fail / 2 order(s) / 250000 minor units
repaired: pass / 1 order(s) / 125000 minor units
```

`python3 run.py --verify <new-directory>/repaired.json` — exit 0, self-consistent.

The vulnerable evaluation failure is intentional and is distinct from a failing regression test.

## Red-to-green regression

The initial suite ran 10 tests with one failure: `test_repaired_reconciles_without_duplicate`. At that point the repaired service prevented duplication, but the controller still retried without reconciliation. Changing the repaired controller to look up the existing intent made that test pass. The final suite includes 20 passing tests.

## Browser verification: blocked

Playwright could not launch because its Chromium executable was missing. Installing Chromium returned invalid/truncated ZIP downloads. Therefore visual layout, mobile behavior, browser interaction, and actual browser downloads are not verified. HTTP tests do verify served assets and live API responses; CLI tests verify the same comparison-bundle format used by the browser.

Before publishing, run the manual browser checklist in DEVELOPMENT-CHECKPOINT.md. No screenshots or visual pass claims are included.

## Scope of evidence

One intentionally constructed case, two controller strategies, and a fault-free control. No live-model evaluation, load test, external procurement integration, process crash recovery, Windows execution test, or independent security audit was performed.
