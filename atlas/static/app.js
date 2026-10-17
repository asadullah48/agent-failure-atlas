'use strict';
const $ = id => document.getElementById(id);
let reports = null;
let activeMode = 'vulnerable';
let replayTimer = null;
const money = amount => (amount / 100).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
const labels = {'request.received': 'Purchase request received', 'approval.granted': 'Reviewer approves AED 1,250.00',
  'purchase.committed': 'Purchase committed to the ledger', 'fault.response_lost': 'Response lost after commit',
  'controller.claim': 'Controller reports success'};

function stopReplay() { clearInterval(replayTimer); replayTimer = null; $('replay').textContent = 'Replay trace ↻'; }
function renderCard(mode, prefix) {
  const r = reports[mode];
  $(prefix + '-status').textContent = r.verdict === 'pass' ? 'CHECKS PASS' : 'CHECKS FAIL';
  $(prefix + '-status').className = 'result-status ' + r.verdict;
  $(prefix + '-claim').textContent = '“' + r.claim + '”';
  $(prefix + '-orders').textContent = r.state.order_count;
  $(prefix + '-spend').textContent = money(r.state.spent_minor);
  $(prefix + '-message').className = 'outcome ' + r.verdict;
  $(prefix + '-message').textContent = r.verdict === 'fail'
    ? 'Claim–state gap: one request produced two purchases.'
    : r.fault_enabled ? 'Existing purchase recovered. No duplicate effect.' : 'Baseline completed. No failure was injected.';
}

function renderTrace(limit) {
  if (!reports) return;
  const r = reports[activeMode];
  const events = r.events.slice(0, limit ?? r.events.length);
  $('trace').replaceChildren();
  for (const e of events) {
    const row = document.createElement('details');
    row.className = 'event' + (e.kind.startsWith('fault.') ? ' fault' : e.kind === 'controller.decision' ? ' decision' : '');
    const summary = document.createElement('summary');
    const seq = document.createElement('span'); seq.className = 'event-seq'; seq.textContent = String(e.seq).padStart(2, '0');
    const title = document.createElement('span'); title.className = 'event-title';
    title.textContent = labels[e.kind] || (e.kind === 'controller.decision' ? e.payload.action.replaceAll('_', ' ') : e.kind + ' · ' + (e.payload.tool || 'gateway'));
    summary.append(seq, title);
    const payload = document.createElement('pre'); payload.textContent = JSON.stringify({actor: e.actor, ...e.payload}, null, 2);
    row.append(summary, payload); $('trace').append(row);
  }
  $('trace-count').textContent = `${events.length} / ${r.events.length} recorded events`;
}

function renderChecks() {
  const r = reports[activeMode]; $('checks').replaceChildren();
  for (const check of r.assertions) {
    const row = document.createElement('div'); row.className = 'check ' + check.status;
    const mark = document.createElement('span'); mark.className = 'indicator'; mark.textContent = check.status === 'pass' ? 'PASS' : 'FAIL';
    const detail = document.createElement('div'); detail.textContent = check.label;
    const observed = document.createElement('small'); observed.textContent = check.observed;
    detail.append(observed); row.append(mark, detail); $('checks').append(row);
  }
  $('hash').hidden = false;
  $('hash').textContent = 'REPORT SHA-256\n' + r.report_sha256 + '\nSelf-consistency hash; not independent provenance.';
}

function selectMode(mode) {
  stopReplay(); activeMode = mode;
  $('view-v').setAttribute('aria-pressed', String(mode === 'vulnerable'));
  $('view-r').setAttribute('aria-pressed', String(mode === 'repaired'));
  if (reports) { renderTrace(); renderChecks(); }
}

async function run(mode, injectFault) {
  const response = await fetch('/api/run', {method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({mode, inject_fault: injectFault})});
  if (!response.ok) throw new Error('The local simulator could not complete the run. Check the terminal and try again.');
  return response.json();
}

$('compare').addEventListener('click', async () => {
  stopReplay(); $('error').hidden = true;
  $('compare').disabled = true; $('fault').disabled = true; $('download').disabled = true; $('replay').disabled = true;
  $('run-status').textContent = 'Running…';
  try {
    const fault = $('fault').checked;
    const [vulnerable, repaired] = await Promise.all([run('vulnerable', fault), run('repaired', fault)]);
    reports = {vulnerable, repaired};
    renderCard('vulnerable', 'v'); renderCard('repaired', 'r'); selectMode(activeMode);
    $('run-status').textContent = fault ? 'Fault comparison complete' : 'Baseline complete';
    $('download').disabled = false; $('replay').disabled = false;
  } catch (err) {
    $('error').textContent = err.message; $('error').hidden = false; $('run-status').textContent = 'Run failed';
    // Previous evidence, if present, remains visibly labelled by the run's fault setting.
    $('download').disabled = !reports; $('replay').disabled = !reports;
  } finally { $('compare').disabled = false; $('fault').disabled = false; }
});
$('fault').addEventListener('change', () => {
  $('fault-label').textContent = $('fault').checked ? 'Enabled' : 'Disabled';
  $('run-status').textContent = reports ? 'Settings changed · run again' : 'Ready to run';
});
$('view-v').addEventListener('click', () => selectMode('vulnerable'));
$('view-r').addEventListener('click', () => selectMode('repaired'));
$('replay').addEventListener('click', () => {
  if (!reports) return;
  if (replayTimer) { stopReplay(); renderTrace(); return; }
  let index = 0; renderTrace(0); $('replay').textContent = 'Show complete trace';
  replayTimer = setInterval(() => { renderTrace(++index); if (index >= reports[activeMode].events.length) stopReplay(); }, 220);
});
$('download').addEventListener('click', () => {
  if (!reports) return;
  const file = new Blob([JSON.stringify({atlas_version:'0.1.0', case_id:'AFA-001', reports}, null, 2)], {type:'application/json'});
  const url = URL.createObjectURL(file); const link = document.createElement('a');
  link.href = url; link.download = 'AFA-001-evidence.json'; document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
