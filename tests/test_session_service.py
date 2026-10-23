import hashlib
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from database import get_db_connection, initialize_database
from repositories.session_repository import delete_session, fetch_valid_session
from repositories.user_repository import insert_user
from services.session_service import create_session, get_session_user_id, hash_session_token


class TestSessionService(unittest.TestCase):
    def setUp(self):
        original_directory = os.getcwd()
        temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temp_directory.cleanup)
        self.addCleanup(os.chdir, original_directory)
        os.chdir(temp_directory.name)
        initialize_database()
        self.user = insert_user("alice", "test-only-hash-placeholder")

    def test_creation_stores_hash_and_expires_after_one_hour(self):
        with patch("services.session_service.time.time", return_value=2000000000.5):
            token = create_session(self.user["id"])

        self.assertIsInstance(token, str)
        self.assertTrue(token)
        expected_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        self.assertEqual(hash_session_token(token), expected_hash)
        session = fetch_valid_session(expected_hash, 2000000000)
        self.assertEqual(session["user_id"], self.user["id"])
        self.assertEqual(session["expires_at"], 2000003600)

        connection = get_db_connection()
        try:
            rows = connection.execute("SELECT * FROM sessions").fetchall()
        finally:
            connection.close()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["token_hash"], expected_hash)
        self.assertNotIn(token, tuple(rows[0]))

    def test_repeated_creation_produces_distinct_valid_credentials(self):
        with patch("services.session_service.time.time", return_value=2000000000):
            first_token = create_session(self.user["id"])
            second_token = create_session(self.user["id"])

        self.assertNotEqual(first_token, second_token)
        for token in (first_token, second_token):
            session = fetch_valid_session(hash_session_token(token), 2000000000)
            self.assertEqual(session["user_id"], self.user["id"])

    def test_missing_user_cannot_create_a_session(self):
        with self.assertRaises(sqlite3.IntegrityError):
            create_session(999)

        connection = get_db_connection()
        try:
            count = connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(count, 0)

    def test_valid_credential_resolves_to_its_owner(self):
        other_user = insert_user("bob", "test-only-hash-placeholder")
        with patch("services.session_service.time.time", return_value=2000000000):
            first_token = create_session(self.user["id"])
            second_token = create_session(other_user["id"])

        with patch("services.session_service.time.time", return_value=2000003599):
            self.assertEqual(get_session_user_id(first_token), self.user["id"])
            self.assertEqual(get_session_user_id(second_token), other_user["id"])

    def test_unknown_credential_returns_none(self):
        with patch("services.session_service.time.time", return_value=2000000000):
            create_session(self.user["id"])
            self.assertIsNone(get_session_user_id("unknown-test-token"))

    def test_credential_at_or_after_expiration_returns_none(self):
        with patch("services.session_service.time.time", return_value=2000000000):
            token = create_session(self.user["id"])

        for current_time in (2000003600, 2000003601):
            with self.subTest(current_time=current_time):
                with patch("services.session_service.time.time", return_value=current_time):
                    self.assertIsNone(get_session_user_id(token))

    def test_revoked_credential_returns_none(self):
        with patch("services.session_service.time.time", return_value=2000000000):
            token = create_session(self.user["id"])
            delete_session(hash_session_token(token))

            self.assertIsNone(get_session_user_id(token))
