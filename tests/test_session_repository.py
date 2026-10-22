import os
import sqlite3
import tempfile
import unittest

from database import get_db_connection, initialize_database
from repositories.session_repository import delete_session, fetch_valid_session, insert_session
from repositories.user_repository import insert_user


class TestSessionRepository(unittest.TestCase):
    def setUp(self):
        original_directory = os.getcwd()
        temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temp_directory.cleanup)
        self.addCleanup(os.chdir, original_directory)
        os.chdir(temp_directory.name)
        initialize_database()
        self.user = insert_user("alice", "test-only-hash-placeholder")

    def test_insert_persists_session_and_returns_none(self):
        result = insert_session("test-token-hash", self.user["id"], 2000000000)

        self.assertIsNone(result)
        connection = get_db_connection()
        try:
            session = connection.execute(
                "SELECT * FROM sessions WHERE token_hash = ?", ("test-token-hash",)
            ).fetchone()
        finally:
            connection.close()

        self.assertIsNotNone(session)
        self.assertEqual(session["user_id"], self.user["id"])
        self.assertEqual(session["expires_at"], 2000000000)
        self.assertIsInstance(session["created_at"], int)

    def test_missing_user_is_rejected_without_leaving_a_session(self):
        with self.assertRaises(sqlite3.IntegrityError):
            insert_session("test-token-hash", 999, 2000000000)

        connection = get_db_connection()
        try:
            count = connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        finally:
            connection.close()

        self.assertEqual(count, 0)
        insert_session("valid-test-hash", self.user["id"], 2000000000)

    def test_matching_unexpired_session_is_returned(self):
        insert_session("other-test-hash", self.user["id"], 3000)
        insert_session("requested-test-hash", self.user["id"], 2000)

        session = fetch_valid_session("requested-test-hash", 1000)

        self.assertIsInstance(session, dict)
        self.assertEqual(session["token_hash"], "requested-test-hash")
        self.assertEqual(session["user_id"], self.user["id"])
        self.assertEqual(session["expires_at"], 2000)
        self.assertIsInstance(session["created_at"], int)

    def test_expired_session_returns_none(self):
        insert_session("test-token-hash", self.user["id"], 999)

        self.assertIsNone(fetch_valid_session("test-token-hash", 1000))

    def test_session_at_exact_expiration_returns_none(self):
        insert_session("test-token-hash", self.user["id"], 1000)

        self.assertIsNone(fetch_valid_session("test-token-hash", 1000))

    def test_unknown_hash_returns_none_even_when_another_session_is_valid(self):
        insert_session("existing-test-hash", self.user["id"], 2000)

        self.assertIsNone(fetch_valid_session("missing-test-hash", 1000))

    def test_delete_revokes_only_the_target_session(self):
        insert_session("desktop-test-hash", self.user["id"], 2000)
        insert_session("phone-test-hash", self.user["id"], 2000)

        result = delete_session("desktop-test-hash")

        self.assertIsNone(result)
        self.assertIsNone(fetch_valid_session("desktop-test-hash", 1000))
        remaining = fetch_valid_session("phone-test-hash", 1000)
        self.assertEqual(remaining["user_id"], self.user["id"])
        self.assertEqual(remaining["token_hash"], "phone-test-hash")

    def test_repeated_and_unknown_deletion_are_harmless(self):
        insert_session("test-token-hash", self.user["id"], 2000)

        delete_session("test-token-hash")
        self.assertIsNone(delete_session("test-token-hash"))
        self.assertIsNone(delete_session("unknown-test-hash"))
        self.assertIsNone(fetch_valid_session("test-token-hash", 1000))
