"""Contract checks without network calls or access to real credentials."""
import json
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from anywhere.api import app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_ui_and_static_match(self):
        page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Anywhere Stack", page.text)
        self.assertEqual(self.client.get("/static/index.html").text, page.text)
        self.assertEqual(self.client.get("/static/missing.txt").status_code, 404)

    def test_health_and_docs(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": ""}):
            self.assertFalse(self.client.get("/health").json()["anthropic_configured"])
        self.assertEqual(self.client.get("/api/healthz").status_code, 200)
        self.assertEqual(self.client.get("/docs").status_code, 200)
        paths = self.client.get("/openapi.json").json()["paths"]
        self.assertIn("/api/intent", paths)
        self.assertIn("/api/sync", paths)

    def test_validation(self):
        self.assertEqual(self.client.post("/api/intent", json={}).status_code, 422)
        self.assertEqual(self.client.post("/api/intent", json={"text": " "}).status_code, 400)
        self.assertEqual(self.client.post("/api/sync", json={}).status_code, 422)

    def test_missing_key(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": ""}):
            response = self.client.post("/api/intent", json={"text": "Plan my work"})
        self.assertEqual(response.status_code, 503)

    def test_success_contract(self):
        routing = {"project_id": "test", "project_name": "Test", "is_new": False,
                   "action_type": "plan", "confidence": 0.9}
        brain = {"goal": "Test", "state": "Planned", "decision": "Proceed",
                 "actions": ["Review"], "memory": ""}
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-only"}), \
             patch("anywhere.api.route", return_value=json.dumps(routing)) as router, \
             patch("anywhere.api.reason", return_value=json.dumps({"response": "Planned", "brain": brain})) as reason:
            response = self.client.post("/api/intent", json={
                "text": "Plan Test", "projects": [{"id": "test", "name": "Test", "goal": "Test"}]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["brain"], brain)
        self.assertEqual(response.json()["routing_confidence"], 0.9)
        self.assertEqual(response.json()["models_used"]["provider"], "Anthropic")
        router.assert_called_once()
        reason.assert_called_once()

    def test_provider_failure_is_not_success(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-only"}), \
             patch("anywhere.api.route", side_effect=RuntimeError("private provider detail")):
            response = self.client.post("/api/intent", json={"text": "Plan work"})
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("private provider detail", response.text)
        self.assertNotIn("brain", response.json())

    def test_malformed_routing(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-only"}), \
             patch("anywhere.api.route", return_value="not JSON"):
            response = self.client.post("/api/intent", json={"text": "Plan work"})
        self.assertEqual(response.status_code, 502)

    def test_reasoning_failure_and_malformed_result(self):
        routing = '{"project_id":"test","project_name":"Test"}'
        for result in (RuntimeError("provider failed"), "not JSON"):
            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-only"}), \
                 patch("anywhere.api.route", return_value=routing), \
                 patch("anywhere.api.reason", **(
                     {"side_effect": result} if isinstance(result, Exception) else {"return_value": result})):
                response = self.client.post("/api/intent", json={"text": "Plan work"})
            self.assertEqual(response.status_code, 502)

    def test_sync_envelope_and_item_errors(self):
        self.assertEqual(self.client.post("/api/sync", json={"queue": []}).json(),
                         {"synced": 0, "results": []})
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": ""}):
            response = self.client.post("/api/sync", json={
                "queue": [{"id": "one", "text": "Plan"}, {"id": "two", "text": ""}]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["synced"], 2)  # legacy count: attempted items
        self.assertEqual([r["status"] for r in response.json()["results"]], ["error", "error"])

    def test_sync_success_keeps_queue_item_id(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-only"}), \
             patch("anywhere.api.route", return_value='{"project_id":"test","project_name":"Test"}'), \
             patch("anywhere.api.reason", return_value='{"response":"Done","brain":{"state":"Planned"}}'):
            response = self.client.post("/api/sync", json={
                "queue": [{"id": "offline-one", "text": "Plan Test", "project_id": "test"}]})
        result = response.json()["results"][0]
        self.assertEqual(result["id"], "offline-one")
        self.assertEqual(result["status"], "processed")
        self.assertEqual(result["brain"]["state"], "Planned")


if __name__ == "__main__":
    unittest.main()
