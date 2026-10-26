import unittest
from unittest.mock import Mock, call, patch

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.testclient import TestClient

from dependencies import require_login_budget
from models import LoginRequest


class TestLoginBudget(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        self.endpoint_called = Mock()

        @app.post("/login", dependencies=[Depends(require_login_budget)])
        def login(data: LoginRequest):
            self.endpoint_called()
            return {"ok": True}

        self.client = TestClient(app, base_url="https://testserver")
        self.addCleanup(self.client.close)
        self.payload = {"username": "alice", "password": "test-only-password"}

    def test_checks_ip_and_account_before_running_endpoint(self):
        with patch("dependencies.allow_login_attempt", return_value=True) as allow:
            response = self.client.post("/login", json=self.payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(allow.call_args_list, [call("ip:testclient"), call("account:alice")])
        self.endpoint_called.assert_called_once_with()

    def test_exhausted_budget_blocks_endpoint(self):
        for decisions in ([False], [True, False]):
            with self.subTest(decisions=decisions):
                with patch("dependencies.allow_login_attempt", side_effect=decisions) as allow:
                    response = self.client.post("/login", json=self.payload)
                self.assertEqual(response.status_code, 429)
                self.assertEqual(response.json(), {"detail": "Too many login attempts"})
                self.assertEqual(response.headers["retry-after"], "60")
                self.assertEqual(response.headers["cache-control"], "no-store")
                self.assertEqual(allow.call_count, len(decisions))
                self.assertNotIn(self.payload["password"], response.text)
        self.endpoint_called.assert_not_called()

    def test_missing_client_address_fails_without_consuming_budget(self):
        request = Request({"type": "http", "headers": [], "client": None})
        with patch("dependencies.allow_login_attempt") as allow:
            with self.assertRaises(HTTPException) as caught:
                require_login_budget(request, LoginRequest(**self.payload))
        self.assertEqual(caught.exception.status_code, 503)
        allow.assert_not_called()
