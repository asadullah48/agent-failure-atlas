"""Build a read-only, deterministic Case 001 recording using only the stdlib.

Goal: publish a compact evidence snapshot, separate from the interactive server.
Input: fixed Case 001 fixture with response loss enabled in both controller modes.
Output: a new directory containing index.html, styles.css and reports.json.
Rules: no network, model calls, timestamps, scripts, or third-party packages.
Edge cases: refuse an existing output directory; escape all report text as HTML.
"""
import argparse
from html import escape
import json
from pathlib import Path

from .core import run_case

REPO = "https://github.com/asadullah48/agent-failure-atlas"
DEEP = "https://asadullah48.github.io/agent-rehearsal/"
LABEL = "Recorded snapshot · scripted/offline · synthetic data · not a live AI agent"

CSS = """*{box-sizing:border-box}body{margin:0;background:#f5f3ec;color:#202b30;font:17px/1.6 system-ui,sans-serif}main{max-width:1140px;margin:auto;padding:32px 24px}a{color:#15576b}header{border-bottom:2px solid #202b30;padding-bottom:24px}h1{font-size:clamp(2rem,5vw,3.5rem);line-height:1.12}h2,h3{line-height:1.3}.label{font-weight:700;color:#334b50}.comparison{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px;margin:28px 0}.card,section.note{background:white;border:1px solid #c4cecb;padding:24px;border-radius:8px}.metric{font-size:2rem;font-weight:750;margin:8px 0}.fail{color:#8c2921}.pass{color:#176047}ol,ul{padding-left:24px}li{margin:12px 0}code,pre{font-size:.86em}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f5f4;padding:12px}code,a{overflow-wrap:anywhere}summary{cursor:pointer}footer{border-top:1px solid #c4cecb;margin-top:28px;padding-top:16px}@media(max-width:680px){main{padding:20px 14px}.comparison{grid-template-columns:1fr;gap:16px}.card,section.note{padding:18px}.metric{font-size:1.65rem}}"""


def record():
    return {"label": LABEL, "case_id": "AFA-001", "inject_fault": True,
            "reports": {mode: run_case(mode, inject_fault=True)
                        for mode in ("vulnerable", "repaired")}}


def text(value):
    return escape(str(value), quote=True)


def money(minor):
    return f"AED {minor // 100:,}.{minor % 100:02d}"


def render_card(mode, report):
    state = report["state"]
    orders = state["order_count"]
    extra = max(0, orders - 1)
    timeline = []
    for event in report["events"]:
        payload = json.dumps(event["payload"], ensure_ascii=False, sort_keys=True, indent=2)
        timeline.append(f'<li><strong>{text(event["kind"])}</strong> '
                        f'({text(event["actor"])})<pre>{text(payload)}</pre></li>')
    checks = "".join(f'<li><strong>{text(check["status"].upper())}: '
                     f'{text(check["label"])}</strong><br>{text(check["observed"])}</li>'
                     for check in report["assertions"])
    return f'''<article class="card" data-mode="{text(mode)}" data-orders="{text(orders)}"
 data-spent-minor="{text(state['spent_minor'])}">
<h2>{text(mode.title())}</h2><p class="metric">{text(orders)} purchase {'order' if orders == 1 else 'orders'}</p>
<p>{text(extra)} duplicate purchase {'order' if extra == 1 else 'orders'} beyond the one approved request.<br>
<strong>{text(money(state['spent_minor']))} spent</strong></p>
<p>Controller claim: <q>{text(report['claim'])}</q></p>
<p class="{text(mode == 'repaired' and 'pass' or 'fail')}">Recorded evaluator verdict:
<strong>{text(report['verdict'].upper())}</strong></p>
<h3>Independent state checks</h3><ul>{checks}</ul>
<h3>Lost-response timeline</h3><p>Recorded sequence, in execution order. No events execute in this page.</p>
<ol>{''.join(timeline)}</ol>
<details><summary>Recorded report digest</summary><code>{text(report['report_sha256'])}</code>
<p>Self-consistency only; not independently attested provenance.</p></details></article>'''


def render_html(recording):
    cards = "".join(render_card(mode, recording["reports"][mode])
                    for mode in ("vulnerable", "repaired"))
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Recorded, scripted/offline Case 001 using synthetic data; not a live AI agent.">
<title>Case 001 · recorded snapshot · Agent Failure Atlas</title>
<link rel="stylesheet" href="styles.css"></head><body><main>
<header><p class="label">{text(LABEL)}</p><p>AGENT FAILURE ATLAS / CASE 001</p>
<h1>A lost response.<br>Two purchases.</h1>
<p>One approved request, two controller strategies. The purchase commits before its response is lost.
The vulnerable controller assumes nothing happened and retries with a new key. The repaired controller
looks up the existing purchase by intent and keeps a stable operation key.</p>
<p><a href="{REPO}">Repository and source tests</a> ·
<a href="{DEEP}">Agent Rehearsal — the deep version</a> ·
<a href="reports.json">Download recorded evidence (JSON)</a></p>
<p>Fixed input: REQ-001, one approval APR-001 for AED 1,250.00; budget AED 10,000.00.
Response loss is injected once after commit in each isolated run.</p></header>
<div class="comparison">{cards}</div>
<section class="note"><h2>One approval backs one purchase</h2>
<p>The single-use approval rule requires each committed purchase to have its own prior approval.
Reusing APR-001 for two purchases fails <code>approval_evidence</code>, even if the budget still balances.
The repaired run reuses the existing purchase, not the approval for another purchase.</p>
<h2>Which tests prove the repair?</h2><ul>
<li><a href="{REPO}/blob/main/tests/test_core.py"><code>test_repaired_reconciles_without_duplicate</code></a>
checks one order, the approved spend, a recorded intent lookup, and a passing verdict.</li>
<li><code>test_vulnerable_reproduces_duplicate</code> checks the negative control: two orders and a failing verdict.</li>
<li><code>test_lost_response_really_commits</code> verifies that the injected timeout follows the committed purchase.</li>
<li><code>test_repaired_retries_and_changed_key_do_not_duplicate</code> verifies idempotency and conflicting-payload rejection.</li>
<li><code>test_reused_approval_fails_approval_evidence</code> and
<code>test_single_use_approval_passes_approval_evidence</code> check the single-use rule.</li></ul>
<h2>Limits of this recording</h2><p>Scripted/offline, synthetic data, not a live AI agent.
This is a constructed teaching example with in-memory, single-process SQLite, no model calls and no real purchases.
It makes no production claim or real-world failure-rate claim. It does not test distributed races,
process-crash recovery or external payment APIs. The page only displays recorded results; use the local Python
app to run interactive comparisons. Atlas is a compact field guide; Agent Rehearsal is the deep version,
with no implemented integration between them.</p>
<p>Pages status: deployed from main by the Pages workflow.</p></section>
<footer><p class="label">{text(LABEL)}</p><p>Generated offline with
<code>python -m atlas.snapshot --output site/</code>. No browser scripts or external resource loads.</p></footer>
</main></body></html>
'''


def generate(output):
    recording = record()
    page = render_html(recording)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output / "index.html").write_text(page, encoding="utf-8")
    (output / "styles.css").write_text(CSS, encoding="utf-8")
    (output / "reports.json").write_text(
        json.dumps(recording, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return recording


def main():
    parser = argparse.ArgumentParser(description="Generate a recorded, offline Case 001 snapshot")
    parser.add_argument("--output", type=Path, default=Path("site"), help="New output directory")
    args = parser.parse_args()
    try:
        generate(args.output)
    except FileExistsError:
        parser.error("Output directory already exists; choose a new directory")
    print("Recorded snapshot generated: vulnerable 2 orders; repaired 1 order. Synthetic/offline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
