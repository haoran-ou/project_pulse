import os
import tempfile
import unittest
from http.cookies import SimpleCookie

from fastapi import FastAPI
from fastapi.testclient import TestClient

from database import get_db_connection, initialize_database
from routers.auth import SESSION_COOKIE_NAME, router
from services.session_service import get_session_user_id
from services.user_service import create_user_record


class TestAuthRouter(unittest.TestCase):
    def setUp(self):
        original_directory = os.getcwd()
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.addCleanup(os.chdir, original_directory)
        os.chdir(directory.name)
        initialize_database()
        self.user = create_user_record("alice", "test-only-password")
        app = FastAPI()
        app.include_router(router)
        self.client = TestClient(app, base_url="https://testserver")
        self.addCleanup(self.client.close)

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
