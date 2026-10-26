import os
import tempfile
import unittest
from http.cookies import SimpleCookie
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from database import get_db_connection, initialize_database
from routers.auth import SESSION_COOKIE_NAME, router
from services.session_service import create_session, get_session_user_id
from services.user_service import create_user_record


class TestAuthRouter(unittest.TestCase):
    def setUp(self):
        attempts = patch("services.login_rate_limit_service._attempts", {})
        attempts.start()
        self.addCleanup(attempts.stop)
        environment = patch.dict(os.environ, {"PP_APP_ORIGIN": "https://testserver"})
        environment.start()
        self.addCleanup(environment.stop)
        original_directory = os.getcwd()
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.addCleanup(os.chdir, original_directory)
        os.chdir(directory.name)
        initialize_database()
        self.user = create_user_record("alice", "test-only-password")
        app = FastAPI()
        app.include_router(router)
        self.client = TestClient(
            app, base_url="https://testserver", headers={"Origin": "https://testserver"}
        )
        self.addCleanup(self.client.close)

    def test_untrusted_origin_cannot_run_login(self):
        for origin in (None, "null", "https://evil.example"):
            with self.subTest(origin=origin):
                request = self.client.build_request(
                    "POST", "/auth/login",
                    json={"username": "alice", "password": "test-only-password"},
                )
                if origin is None:
                    request.headers.pop("origin", None)
                else:
                    request.headers["origin"] = origin
                with patch("routers.auth.login_user") as login:
                    response = self.client.send(request)
                self.assertEqual(response.status_code, 403)
                self.assertNotIn("set-cookie", response.headers)
                login.assert_not_called()

    def test_untrusted_origin_cannot_revoke_session(self):
        token = create_session(self.user["id"])
        for origin in (None, "null", "https://evil.example"):
            with self.subTest(origin=origin):
                request = self.client.build_request(
                    "POST", "/auth/logout",
                    headers={"Cookie": f"{SESSION_COOKIE_NAME}={token}"},
                )
                if origin is None:
                    request.headers.pop("origin", None)
                else:
                    request.headers["origin"] = origin
                response = self.client.send(request)
                self.assertEqual(response.status_code, 403)
                self.assertNotIn("set-cookie", response.headers)
                self.assertEqual(get_session_user_id(token), self.user["id"])

    def test_me_tracks_login_and_logout_and_rejects_revoked_token(self):
        self.assertEqual(self.client.get("/auth/me").status_code, 401)
        login_response = self.client.post(
            "/auth/login",
            json={"username": "alice", "password": "test-only-password"},
        )
        self.assertEqual(login_response.status_code, 200)
        token = self.client.cookies.get(SESSION_COOKIE_NAME)

        response = self.client.get("/auth/me?user_id=999")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"id": self.user["id"]})
        self.assertEqual(response.headers["cache-control"], "no-store")

        self.assertEqual(self.client.post("/auth/logout").status_code, 204)
        self.assertEqual(self.client.get("/auth/me").status_code, 401)
        replay = self.client.get(
            "/auth/me", headers={"Cookie": f"{SESSION_COOKIE_NAME}={token}"}
        )
        self.assertEqual(replay.status_code, 401)
        self.assertEqual(replay.json(), {"detail": "Authentication required"})
        self.assertEqual(replay.headers["cache-control"], "no-store")

    def test_me_rejects_unknown_cookie(self):
        response = self.client.get(
            "/auth/me",
            headers={"Cookie": f"{SESSION_COOKIE_NAME}=unknown-test-token"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Authentication required"})
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_me_rejects_expired_session_even_when_cookie_is_sent(self):
        with patch("services.session_service.time.time", return_value=2000000000):
            token = create_session(self.user["id"])
        with patch("services.session_service.time.time", return_value=2000003600):
            response = self.client.get(
                "/auth/me", headers={"Cookie": f"{SESSION_COOKIE_NAME}={token}"}
            )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Authentication required"})
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_success_returns_public_user_and_protected_session_cookie(self):
        response = self.client.post(
            "/auth/login",
            json={"username": "alice", "password": "test-only-password"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), self.user)
        self.assertEqual(response.headers["cache-control"], "no-store")
        cookie = SimpleCookie()
        cookie.load(response.headers["set-cookie"])
        session_cookie = cookie[SESSION_COOKIE_NAME]
        self.assertTrue(session_cookie["secure"])
        self.assertTrue(session_cookie["httponly"])
        self.assertEqual(session_cookie["samesite"], "strict")
        self.assertEqual(session_cookie["path"], "/")
        self.assertEqual(session_cookie["domain"], "")
        self.assertEqual(session_cookie["max-age"], "3600")
        token = self.client.cookies.get(SESSION_COOKIE_NAME)
        self.assertEqual(get_session_user_id(token), self.user["id"])
        self.assertNotIn(token, response.text)
        self.assertNotIn("test-only-password", response.text)

    def test_bad_credentials_return_identical_errors_without_creating_sessions(self):
        for username in ("alice", "missing-user"):
            with self.subTest(username=username):
                response = self.client.post(
                    "/auth/login",
                    json={"username": username, "password": "wrong-password"},
                )
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.json(), {"detail": "Invalid username or password"})
                self.assertEqual(response.headers["cache-control"], "no-store")
                self.assertNotIn("set-cookie", response.headers)

        connection = get_db_connection()
        try:
            count = connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(count, 0)

    def test_invalid_password_length_is_not_echoed_in_validation_error(self):
        password = "sensitive-test-marker-" + "x" * 1024
        response = self.client.post(
            "/auth/login", json={"username": "alice", "password": password}
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), {"detail": "Invalid login request"})
        self.assertNotIn("sensitive-test-marker", response.text)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertNotIn("set-cookie", response.headers)

    def test_malformed_json_returns_sanitized_validation_error(self):
        response = self.client.post(
            "/auth/login",
            content='{"password": "sensitive-test-marker",',
            headers={"Content-Type": "application/json"},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), {"detail": "Invalid login request"})
        self.assertNotIn("sensitive-test-marker", response.text)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertNotIn("set-cookie", response.headers)

    def test_logout_revokes_current_session_and_clears_cookie(self):
        other_token = create_session(self.user["id"])
        login_response = self.client.post(
            "/auth/login",
            json={"username": "alice", "password": "test-only-password"},
        )
        self.assertEqual(login_response.status_code, 200)
        token = self.client.cookies.get(SESSION_COOKIE_NAME)
        self.assertEqual(get_session_user_id(token), self.user["id"])

        response = self.client.post("/auth/logout")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertIsNone(get_session_user_id(token))
        self.assertEqual(get_session_user_id(other_token), self.user["id"])
        self.assertIsNone(self.client.cookies.get(SESSION_COOKIE_NAME))
        cookie = SimpleCookie()
        cookie.load(response.headers["set-cookie"])
        session_cookie = cookie[SESSION_COOKIE_NAME]
        self.assertEqual(session_cookie["max-age"], "0")
        self.assertEqual(session_cookie["path"], "/")
        self.assertEqual(session_cookie["domain"], "")
        self.assertTrue(session_cookie["secure"])
        self.assertTrue(session_cookie["httponly"])
        self.assertEqual(session_cookie["samesite"], "strict")

        repeated_response = self.client.post("/auth/logout")
        self.assertEqual(repeated_response.status_code, 204)
        self.assertEqual(repeated_response.content, b"")

    def test_logout_without_valid_cookie_preserves_existing_sessions(self):
        valid_token = create_session(self.user["id"])
        for headers in ({}, {"Cookie": f"{SESSION_COOKIE_NAME}=unknown-test-token"}):
            with self.subTest(headers=headers):
                response = self.client.post("/auth/logout", headers=headers)
                self.assertEqual(response.status_code, 204)
                self.assertEqual(response.content, b"")
                self.assertEqual(response.headers["cache-control"], "no-store")
                self.assertEqual(get_session_user_id(valid_token), self.user["id"])
