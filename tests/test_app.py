import unittest
from copy import deepcopy

from fastapi.testclient import TestClient

from src.app import activities, app


class UnregisterTests(unittest.TestCase):
    def setUp(self):
        self.original_activities = deepcopy(activities)
        self.client = TestClient(app)
        self.addCleanup(self.restore_activities)
        self.addCleanup(self.client.close)

    def restore_activities(self):
        activities.clear()
        activities.update(self.original_activities)

    def test_unregister_removes_only_selected_participant(self):
        response = self.client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "message": "Unregistered michael@mergington.edu from Chess Club"
        })
        expected = deepcopy(self.original_activities)
        expected["Chess Club"]["participants"].remove("michael@mergington.edu")
        self.assertEqual(self.client.get("/activities").json(), expected)

        signup = self.client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "michael@mergington.edu"},
        )
        self.assertEqual(signup.status_code, 200)

    def test_unregister_unknown_activity(self):
        response = self.client.delete(
            "/activities/Unknown/unregister", params={"email": "michael@mergington.edu"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Activity not found"})
        self.assertEqual(activities, self.original_activities)

    def test_unregister_missing_participant(self):
        response = self.client.delete(
            "/activities/Chess%20Club/unregister", params={"email": "unknown@example.com"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {
            "detail": "Student is not signed up for this activity"
        })
        self.assertEqual(activities, self.original_activities)

    def test_unregister_requires_email(self):
        response = self.client.delete("/activities/Chess%20Club/unregister")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(activities, self.original_activities)
