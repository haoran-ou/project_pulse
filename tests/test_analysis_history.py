import unittest
import os
import tempfile

from unittest.mock import patch
from database import initialize_database
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers.meetings import router


class TestAnalysisHistory(unittest.TestCase):
    
    def setUp(self):

        original_directory = os.getcwd()
        temp_directory = tempfile.TemporaryDirectory()

        self.addCleanup(temp_directory.cleanup)
        self.addCleanup(os.chdir, original_directory)

        os.chdir(temp_directory.name)
        initialize_database()

        app = FastAPI()
        app.include_router(router)

        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_analysis_routes_are_registered(self):

        response = self.client.get("/openapi.json")

        self.assertEqual(response.status_code, 200)

        paths = response.json()["paths"]
        analysis_path = "/meetings/{meeting_id}/analyses"

        self.assertIn(analysis_path, paths)
        self.assertIn("get", paths[analysis_path])
        self.assertIn("post", paths[analysis_path])

    def test_analysis_is_saved_and_retrievable(self):
        meeting_response = self.client.post(
            "/meetings",
            json={
                "project_name": "Test Project",
                "meeting_text": "Alice will add tests.",
            },
        )
        self.assertEqual(meeting_response.status_code, 201)
        meeting_id = meeting_response.json()["id"]

        expected_analysis = {
            "summary": "Alice will add tests.",
            "tasks": [
                {"task": "Add tests", "owner": "Alice", "status": "Pending"}
            ],
            "risks": [],
        }
        path = f"/meetings/{meeting_id}/analyses"

        with patch(
            "services.analysis_service.analyze_meeting",
            return_value=expected_analysis,
        ) as mock_analyze:
            analysis_response = self.client.post(path)
            mock_analyze.assert_called_once_with("Alice will add tests.")

        self.assertEqual(analysis_response.status_code, 201)
        saved_analysis = analysis_response.json()
        self.assertEqual(saved_analysis["meeting_id"], meeting_id)
        self.assertEqual(saved_analysis["summary"], expected_analysis["summary"])
        self.assertEqual(saved_analysis["tasks"], expected_analysis["tasks"])
        self.assertEqual(saved_analysis["risks"], expected_analysis["risks"])
        self.assertEqual(
            saved_analysis["meeting_text_snapshot"], "Alice will add tests."
        )

        history_response = self.client.get(path)
        self.assertEqual(history_response.status_code, 200)
        self.assertEqual(history_response.json(), [saved_analysis])