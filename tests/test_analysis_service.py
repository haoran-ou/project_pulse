import unittest
from models import MeetingAnalysis
from unittest.mock import Mock, patch
from services.analysis_service import azure_analyze_meeting,fake_analyze_meeting

#而是文件不会启动FastApi. unittest是python自带的测试工具


class TestAnalysisService(unittest.TestCase):
    def test_analysis_without_risk(self):
        result = fake_analyze_meeting("Discuss the project timeline")

        self.assertEqual(result["risks"], [])

    def test_analysis_with_risk(self):
        result = fake_analyze_meeting("There is a schedule RISK")

        self.assertEqual(
            result["risks"],
            ["A potential project risk was detected."],
        )



    def test_analysis_returns_expected_structure(self):
        result = fake_analyze_meeting("Discuss the project timeline")

        expected = {
            "summary": "Basic analysis of the meeting: Discuss the project timeline",
            "tasks": [
                {
                    "task": "Review the meeting notes",
                    "owner": "Unassigned",
                    "status": "Pending",
                }
            ],
            "risks": [],

        }

        self.assertEqual(result, expected)

    def test_azure_analysis_returns_dict(self):
        expected_analysis = MeetingAnalysis(
            summary="The team discussed the release.",
            tasks=[],
            risks=[],
        )
        fake_response = Mock()
        fake_response.output_parsed = expected_analysis
        fake_client = Mock()
        fake_client.responses.parse.return_value = fake_response
        with patch(
            "services.analysis_service.get_ai_client",
            return_value=fake_client,
        ):
            with patch.dict(
                "os.environ",
                {"AZURE_OPENAI_DEPLOYMENT":"test-depolyment"},
            ):
                result = azure_analyze_meeting("Discuss the release.")
            self.assertEqual(
                result,
                {
                    "summary": "The team discussed the release.",
                    "tasks": [],
                    "risks": [], 
                },
            )
        fake_client.responses.parse.assert_called_once()
        sent_arguments = fake_client.responses.parse.call_args.kwargs
    
        self.assertEqual(sent_arguments["input"], "Discuss the release.")
        self.assertEqual(sent_arguments["model"], "test-depolyment")

    def test_azure_analysis_raises_when_result_is_missing(self):
        fake_response = Mock()
        fake_response.output_parsed = None

        fake_client = Mock()
        fake_client.responses.parse.return_value = fake_response

        with patch(
            "services.analysis_service.get_ai_client",
            return_value = fake_client,
        ):
            with patch.dict(
                "os.environ",
                {"AZURE_OPENAI_DEPLOYMENT": "test-developyment"}, 
            ):
                with self.assertRaises(ValueError):
                    azure_analyze_meeting("Discuss the release.")

