import os
import tempfile
import unittest
from unittest.mock import patch

from database import get_db_connection, initialize_database
from repositories.user_repository import fetch_user_by_username
from services.password_service import verify_password
from services.session_service import get_session_user_id
from services.user_service import (
    DUMMY_PASSWORD_HASH,
    authenticate_user,
    create_user_record,
    login_user,
)


class TestUserService(unittest.TestCase):
    def setUp(self):
        original_directory = os.getcwd()
        temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temp_directory.cleanup)
        self.addCleanup(os.chdir, original_directory)
        os.chdir(temp_directory.name)
        initialize_database()

    def test_creation_stores_verifiable_hash_and_returns_public_fields(self):
        password = "test-only-password"

        result = create_user_record("alice", password)

        self.assertEqual(result, {"id": 1, "username": "alice"})
        stored_user = fetch_user_by_username("alice")
        self.assertEqual(stored_user["id"], result["id"])
        self.assertNotEqual(stored_user["password_hash"], password)
        self.assertTrue(verify_password(password, stored_user["password_hash"]))
        self.assertFalse(verify_password("wrong-password", stored_user["password_hash"]))

    def test_correct_credentials_return_public_user_fields(self):
        created_user = create_user_record("alice", "test-only-password")

        result = authenticate_user("alice", "test-only-password")

        self.assertEqual(result, created_user)
        self.assertEqual(set(result), {"id", "username"})

    def test_wrong_password_returns_none(self):
        create_user_record("alice", "test-only-password")

        self.assertIsNone(authenticate_user("alice", "wrong-password"))

    def test_missing_user_checks_dummy_hash_but_always_returns_none(self):
        for password in ("wrong-password", "not-a-real-account-password"):
            with self.subTest(password=password):
                with patch(
                    "services.user_service.verify_password",
                    wraps=verify_password,
                ) as verify:
                    result = authenticate_user("missing-user", password)

                self.assertIsNone(result)
                verify.assert_called_once_with(password, DUMMY_PASSWORD_HASH)

    def test_login_creates_a_session_for_the_authenticated_user(self):
        created_user = create_user_record("alice", "test-only-password")

        result = login_user("alice", "test-only-password")

        self.assertEqual(result["user"], created_user)
        self.assertEqual(set(result), {"user", "token"})
        self.assertIsInstance(result["token"], str)
        self.assertEqual(get_session_user_id(result["token"]), created_user["id"])
        connection = get_db_connection()
        try:
            count = connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(count, 1)

    def test_failed_logins_do_not_create_sessions(self):
        create_user_record("alice", "test-only-password")
        for username, password in (
            ("alice", "wrong-password"),
            ("missing-user", "test-only-password"),
        ):
            with self.subTest(username=username):
                with patch("services.user_service.create_session") as create:
                    self.assertIsNone(login_user(username, password))
                    create.assert_not_called()

        connection = get_db_connection()
        try:
            count = connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(count, 0)
