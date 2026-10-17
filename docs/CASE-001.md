# Case 001: successful commit, missing acknowledgement

## Reproduction

Run the local app, keep “Inject a lost response” enabled, and choose “Run comparison.” Expand the purchase commit and response-loss events. The ledger mutation precedes the simulated timeout. The controller does not receive the committed result in that response.

## Root cause

An unknown outcome is incorrectly treated as a failed transaction. The vulnerable controller retries with a fresh operation key, and the deliberately vulnerable service accepts a second purchase for the same request. Both controllers report success, but only the ledger establishes whether the requested work happened once.

## Repair

The repaired controller performs an authoritative lookup by logical intent. If the purchase exists, it returns that result. If absent, it retains the original key for a retry. The repaired service independently enforces unique intent and operation keys and rejects conflicting payloads.

The present scenario always commits before response loss, so the lookup-found branch is the scenario path. Tests separately exercise stable-key replay and changed-key duplicate prevention. External lookup consistency and retry after a genuinely absent purchase require additional scenarios.

## Verification method

The initial suite deliberately ran the repaired controller with the unsafe retry strategy. The reconciliation regression failed even though the repaired service's uniqueness constraint prevented an extra order. After changing the controller to reconcile, the test passed. The vulnerable case remains a negative demonstration.

This separates two useful guarantees: a tool can block duplicate effects while a controller still handles an unknown outcome incorrectly. Both should be inspected.

## Evidence interpretation

Event sequence numbers are logical order, not elapsed time. Approval is a synthetic scripted reviewer event. JSON evidence includes policy, mode, fault setting, tool calls/results, commits, final state, independent checks, and hashes. The browser's replay button displays recorded data only.
