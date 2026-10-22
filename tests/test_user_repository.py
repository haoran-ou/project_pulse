import os
import sqlite3
import tempfile
import unittest

from database import get_db_connection, initialize_database
from repositories.user_repository import fetch_user_by_username, insert_user


class TestUserRepository(unittest.TestCase):
    def setUp(self):
        original_directory = os.getcwd()
        temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temp_directory.cleanup)
        self.addCleanup(os.chdir, original_directory)
        os.chdir(temp_directory.name)
        initialize_database()

        connection = get_db_connection()
        try:
            # Storage fixtures only; these are not usable password hashes.
            connection.executemany(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                [
                    ("alice", "alice-test-placeholder"),
                    ("bob", "bob-test-placeholder"),
                ],
            )
            connection.commit()
        finally:
            connection.close()

    def test_fetches_only_the_requested_user(self):
        user = fetch_user_by_username("bob")

        self.assertIsInstance(user, dict)
        self.assertEqual(user["id"], 2)
        self.assertEqual(user["username"], "bob")
        self.assertEqual(user["password_hash"], "bob-test-placeholder")
        self.assertIsNotNone(user["created_at"])

    def test_unmatched_input_returns_none(self):
        for username in ("missing-user", "' OR 1=1 --"):
            with self.subTest(username=username):
                self.assertIsNone(fetch_user_by_username(username))

    def test_insert_persists_user_without_returning_hash(self):
        result = insert_user("carol", "carol-test-placeholder")

        self.assertEqual(result, {"id": 3, "username": "carol"})
        stored_user = fetch_user_by_username("carol")
        self.assertEqual(stored_user["id"], result["id"])
        self.assertEqual(stored_user["username"], "carol")
        self.assertEqual(stored_user["password_hash"], "carol-test-placeholder")
        self.assertIsNotNone(stored_user["created_at"])

    def test_duplicate_insert_preserves_existing_user(self):
        original_user = fetch_user_by_username("alice")

        with self.assertRaises(sqlite3.IntegrityError):
            insert_user("alice", "replacement-test-placeholder")

        self.assertEqual(fetch_user_by_username("alice"), original_user)
        result = insert_user("carol", "carol-test-placeholder")
        self.assertEqual(fetch_user_by_username("carol")["id"], result["id"])
