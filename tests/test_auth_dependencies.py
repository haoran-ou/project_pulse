import os
import unittest
from unittest.mock import Mock, patch

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from dependencies import SESSION_COOKIE_NAME, require_trusted_origin, require_user_id


class TestAuthDependencies(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        self.endpoint_called = Mock()

        @app.get("/protected")
        def protected(user_id: int = Depends(require_user_id)):
            self.endpoint_called(user_id)
            return {"user_id": user_id}

        self.client = TestClient(app, base_url="https://testserver")
        self.addCleanup(self.client.close)

    def test_valid_session_uses_server_resolved_identity(self):
        with patch("dependencies.get_session_user_id", return_value=7) as lookup:
            response = self.client.get(
                "/protected?user_id=999",
                headers={"Cookie": f"{SESSION_COOKIE_NAME}=test-token"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"user_id": 7})
        lookup.assert_called_once_with("test-token")
        self.endpoint_called.assert_called_once_with(7)

    def test_missing_cookie_blocks_endpoint_without_session_lookup(self):
        with patch("dependencies.get_session_user_id") as lookup:
            response = self.client.get("/protected?user_id=999")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Authentication required"})
        self.assertEqual(response.headers["cache-control"], "no-store")
        lookup.assert_not_called()
        self.endpoint_called.assert_not_called()


    def test_invalid_session_blocks_endpoint(self):
        with patch("dependencies.get_session_user_id", return_value=None) as lookup:
            response = self.client.get(
                "/protected",
                headers={"Cookie": f"{SESSION_COOKIE_NAME}=invalid-test-token"},
            )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Authentication required"})
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertNotIn("invalid-test-token", response.text)
        lookup.assert_called_once_with("invalid-test-token")
        self.endpoint_called.assert_not_called()


class TestOriginDependency(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, {"PP_APP_ORIGIN": "https://testserver"})
        environment.start()
        self.addCleanup(environment.stop)
        self.endpoint_called = Mock()
        app = FastAPI()

        @app.post("/action", dependencies=[Depends(require_trusted_origin)])
        def action():
            self.endpoint_called()
            return {"ok": True}

        self.client = TestClient(app, base_url="https://testserver")
        self.addCleanup(self.client.close)

    def test_exact_origin_allows_endpoint(self):
        response = self.client.post("/action", headers={"Origin": "https://testserver"})
        self.assertEqual(response.status_code, 200)
        self.endpoint_called.assert_called_once_with()

    def test_missing_configuration_blocks_endpoint(self):
        for value in (None, ""):
            with self.subTest(value=value):
                if value is None:
                    os.environ.pop("PP_APP_ORIGIN", None)
                else:
                    os.environ["PP_APP_ORIGIN"] = value
                response = self.client.post(
                    "/action", headers={"Origin": "https://testserver"}
                )
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.headers["cache-control"], "no-store")
        self.endpoint_called.assert_not_called()

    def test_missing_or_different_origin_blocks_endpoint(self):
        for origin in (None, "null", "https://evil.example", "https://testserver.evil.example",
                       "http://testserver", "https://testserver:8443"):
            with self.subTest(origin=origin):
                headers = {} if origin is None else {"Origin": origin}
                response = self.client.post("/action", headers=headers)
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.json(), {"detail": "Untrusted request origin"})
                self.assertEqual(response.headers["cache-control"], "no-store")
        self.endpoint_called.assert_not_called()
