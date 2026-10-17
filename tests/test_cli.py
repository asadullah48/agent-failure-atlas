import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from atlas.core import run_case

ROOT = Path(__file__).resolve().parents[1]


class CLITests(unittest.TestCase):
    def invoke(self, *args):
        return subprocess.run([sys.executable, str(ROOT / 'run.py'), *map(str, args)],
                              capture_output=True, text=True, timeout=10, cwd=ROOT)

    def test_export_and_verify(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'new-run'
            result = self.invoke('--export', out)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self.invoke('--verify', out / 'repaired.json').returncode, 0)
            self.assertEqual(json.loads((out / 'vulnerable.json').read_text())['verdict'], 'fail')

    def test_export_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / 'keep.txt'
            marker.write_text('original')
            self.assertNotEqual(self.invoke('--export', tmp).returncode, 0)
            self.assertEqual(marker.read_text(), 'original')

    def test_browser_bundle_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'bundle.json'
            p.write_text(json.dumps({'reports': {m: run_case(m) for m in ['vulnerable', 'repaired']}}))
            self.assertEqual(self.invoke('--verify', p).returncode, 0)

    def test_tampered_report_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'tampered.json'
            report = run_case()
            report['state']['order_count'] = 100
            p.write_text(json.dumps(report))
            self.assertEqual(self.invoke('--verify', p).returncode, 1)
