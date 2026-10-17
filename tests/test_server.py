import http.client
import json
import threading
import unittest

from atlas.server import make_server


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = make_server(0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            return response.status, response.read(), dict(response.getheaders())
        finally:
            connection.close()

    def test_home_and_assets(self):
        for path in ['/', '/app.js', '/styles.css', '/api/cases']:
            with self.subTest(path=path):
                status, body, headers = self.request('GET', path)
                self.assertEqual(status, 200)
                self.assertTrue(body)
                self.assertIn('Content-Security-Policy', headers)

    def test_real_api_comparison(self):
        for mode, count in [('vulnerable', 2), ('repaired', 1)]:
            status, raw, _ = self.request('POST', '/api/run',
                json.dumps({'mode': mode, 'inject_fault': True}), {'Content-Type': 'application/json'})
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(raw)['state']['order_count'], count)

    def test_invalid_input_rejected(self):
        for data in [{'mode': 'other', 'inject_fault': True},
                     {'mode': 'repaired', 'inject_fault': 'true'},
                     {'mode': 'repaired', 'inject_fault': True, 'url': 'https://example.com'}, []]:
            with self.subTest(data=data):
                status, _, _ = self.request('POST', '/api/run', json.dumps(data), {'Content-Type': 'application/json'})
                self.assertEqual(status, 400)

    def test_untrusted_origin_and_host_denied(self):
        status, _, _ = self.request('POST', '/api/run', '{}',
            {'Content-Type': 'application/json', 'Origin': 'https://example.com'})
        self.assertEqual(status, 403)
        status, _, _ = self.request('GET', '/', headers={'Host': 'attacker.invalid'})
        self.assertEqual(status, 403)

    def test_files_outside_allowlist_are_not_served(self):
        for path in ['/../run.py', '/run.py', '/.env']:
            self.assertEqual(self.request('GET', path)[0], 404)

    def test_non_json_and_large_body_rejected(self):
        self.assertEqual(self.request('POST', '/api/run', '{}')[0], 415)
        self.assertEqual(self.request('POST', '/api/run', 'x' * 4097,
            {'Content-Type': 'application/json'})[0], 413)
