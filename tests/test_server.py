import json
import threading
import time
import unittest
from http.client import HTTPConnection
from socketserver import TCPServer

from server import Handler


class ArenaServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = TCPServer(("127.0.0.1", 0), Handler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def req(self, method, path, body=None, expect_json=True):
        conn = HTTPConnection("127.0.0.1", self.port)
        headers = {"Content-Type": "application/json"}
        payload = json.dumps(body) if body is not None else None
        conn.request(method, path, payload, headers)
        resp = conn.getresponse()
        raw = resp.read().decode("utf-8")
        conn.close()
        if expect_json:
            return resp.status, json.loads(raw)
        return resp.status, raw

    def test_health_and_web(self):
        status, html = self.req("GET", "/", expect_json=False)
        self.assertEqual(status, 200)
        self.assertIn("AI Arena MVP", html)

        status, body = self.req("GET", "/healthz")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "ok")

    def test_duel_flow(self):
        status, auth = self.req("POST", "/api/v1/auth/guest")
        self.assertEqual(status, 200)

        status, _ = self.req("GET", "/api/v1/ai-models")
        self.assertEqual(status, 200)

        status, created = self.req(
            "POST",
            "/api/v1/matches",
            {
                "user_id": auth["user_id"],
                "ai_model_code": "gpt-4o",
                "mode": "duel",
                "round_count": 3,
                "difficulty": "normal",
                "set_code": "quick_mix_5",
            },
        )
        self.assertEqual(status, 200)
        match_id = created["match_id"]

        status, _ = self.req("POST", f"/api/v1/matches/{match_id}/start")
        self.assertEqual(status, 200)

        for round_no in [1, 2, 3]:
            status, _ = self.req("GET", f"/api/v1/matches/{match_id}/rounds/{round_no}")
            self.assertEqual(status, 200)

            status, result = self.req(
                "POST",
                f"/api/v1/matches/{match_id}/rounds/{round_no}/submit",
                {"answer": {"final_answer": "tap"}, "latency_ms": 900},
            )
            self.assertEqual(status, 200)
            self.assertIn("round_result", result)

        status, _ = self.req("POST", f"/api/v1/matches/{match_id}/finish")
        self.assertEqual(status, 200)

        status, report = self.req("GET", f"/api/v1/matches/{match_id}/report")
        self.assertEqual(status, 200)
        self.assertIn("winner", report)


if __name__ == "__main__":
    unittest.main()
