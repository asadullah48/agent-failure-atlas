import copy
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import urlsplit

from atlas.core import run_case, verify_report
from atlas.snapshot import generate, record, render_html, LABEL
from test_publication import LOCAL_PATH

ROOT = Path(__file__).resolve().parents[1]


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.cards = {}
        self.resources = []
        self.links = []
        self.content = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append(tag)
        if tag == 'article':
            self.cards[attrs['data-mode']] = attrs
        if tag == 'a':
            self.links.append(attrs.get('href', ''))
        for key in ('src', 'srcset', 'poster', 'data', 'action'):
            if key in attrs:
                self.resources.append(attrs[key])
        if tag == 'link':
            self.resources.append(attrs.get('href', ''))

    def handle_data(self, data):
        self.content.append(data)


class SnapshotTests(unittest.TestCase):
    def test_generated_github_source_links_target_main(self):
        page = PageParser()
        page.feed(render_html(record()))
        source_links = []
        for link in page.links + page.resources:
            parsed = urlsplit(link)
            parts = parsed.path.strip('/').split('/')
            if parsed.hostname == 'github.com' and len(parts) >= 3 and parts[2] in {'blob', 'tree', 'raw'}:
                source_links.append(link)
                self.assertGreaterEqual(len(parts), 5, link)
                self.assertEqual(parts[3], 'main', link)
        self.assertTrue(source_links, 'Expected at least one GitHub source link')


    def test_snapshot_values_match_fresh_runs_and_rendered_cards(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'site'
            generate(out)
            saved = json.loads((out / 'reports.json').read_text(encoding='utf-8'))
            page = PageParser()
            page.feed((out / 'index.html').read_text(encoding='utf-8'))
            for mode, count in [('vulnerable', 2), ('repaired', 1)]:
                report = saved['reports'][mode]
                self.assertEqual(report, run_case(mode, True))
                self.assertTrue(verify_report(report))
                self.assertEqual(report['state']['order_count'], count)
                self.assertEqual(int(page.cards[mode]['data-orders']), count)
                self.assertEqual(int(page.cards[mode]['data-spent-minor']), report['state']['spent_minor'])
            visible = ''.join(page.content)
            for value in [LABEL, 'AED 2,500.00', 'AED 1,250.00', 'fault.response_lost',
                          'Approval APR-001 backed 2 purchases',
                          'test_repaired_reconciles_without_duplicate', '1 duplicate purchase order beyond', '1 purchase order', '2 purchase orders',
                          '0 duplicate purchase orders', 'single-use approval rule']:
                self.assertIn(value, visible)
            self.assertNotIn('1 purchase orders', visible)
            self.assertNotIn('1 duplicate purchase orders', visible)
            self.assertNotIn('Pages status:', visible)

    def test_generated_files_have_no_external_resources_or_absolute_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'site'
            generate(out)
            self.assertEqual({p.name for p in out.iterdir()}, {'index.html', 'styles.css', 'reports.json'})
            page = PageParser()
            page.feed((out / 'index.html').read_text(encoding='utf-8'))
            self.assertEqual(page.resources, ['styles.css'])
            self.assertFalse(set(page.tags) & {'script', 'iframe', 'object', 'embed', 'form', 'base'})
            self.assertIn('https://github.com/asadullah48/agent-failure-atlas', page.links)
            self.assertIn('https://asadullah48.github.io/agent-rehearsal/', page.links)
            for p in out.iterdir():
                self.assertIsNone(LOCAL_PATH.search(p.read_bytes()), p.name)
            css = (out / 'styles.css').read_text(encoding='utf-8')
            self.assertNotRegex(css, r'(?i)@import|url\s*\(')
            self.assertIn('grid-template-columns:1fr', css)
            self.assertIn('max-width:680px', css)

    def test_report_content_is_html_escaped(self):
        recording = copy.deepcopy(record())
        payload = '<script src="https://invalid.example/x">&\'test</script>'
        report = recording['reports']['vulnerable']
        report['claim'] = payload
        report['events'][0]['kind'] = payload
        report['events'][0]['actor'] = payload
        report['events'][0]['payload'] = {'unsafe': payload}
        report['assertions'][0]['label'] = payload
        report['assertions'][0]['observed'] = payload
        report['report_sha256'] = payload
        html = render_html(recording)
        self.assertNotIn('<script', html)
        self.assertIn('&lt;script', html)
        self.assertIn('&quot;', html)
        self.assertIn('&#x27;', html)
        page = PageParser()
        page.feed(html)
        self.assertNotIn('script', page.tags)
        self.assertIn(payload, ''.join(page.content))
        self.assertEqual(page.resources, ['styles.css'])

    def test_snapshot_is_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp) / 'one', Path(tmp) / 'two'
            generate(first)
            generate(second)
            for p in first.iterdir():
                self.assertEqual(p.read_bytes(), (second / p.name).read_bytes())

    def test_existing_directory_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'site'
            generate(out)
            before = (out / 'index.html').read_bytes()
            with self.assertRaises(FileExistsError):
                generate(out)
            self.assertEqual((out / 'index.html').read_bytes(), before)

    def test_generator_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'site'
            result = subprocess.run([sys.executable, '-m', 'atlas.snapshot', '--output', str(out)],
                                    cwd=ROOT, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((out / 'index.html').is_file())
