import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from routes import attendance as attendance_module  # noqa: E402


class AttendanceBehaviorTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(attendance_module.attendance_bp, url_prefix="/v1")
        self.client = app.test_client()

    def test_kiosk_state_requires_employee_selection(self):
        device = {
            "device_id": "device-1",
            "employee_id": None,
            "building_id": "building-1",
        }

        with patch.object(attendance_module, "_get_device_from_token", return_value=device), \
             patch.object(attendance_module, "_resolve_employee_id", return_value=None):
            response = self.client.get(
                "/v1/attendance/state",
                headers={"X-Device-Token": "token"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["requires_employee"], True)
        self.assertEqual(response.get_json()["action"], "check_in")

    def test_biometric_failure_does_not_open_write_transaction(self):
        device = {
            "device_id": "device-1",
            "employee_id": None,
            "building_id": "building-1",
        }

        with patch.object(attendance_module, "_get_device_from_token", return_value=device), \
             patch.object(attendance_module, "_resolve_employee_id", return_value="employee-1"), \
             patch.object(attendance_module, "verify_face", return_value={"match": False, "status": "failed"}), \
             patch("utils.db.tx") as tx_mock:
            response = self.client.post(
                "/v1/attendance/register",
                headers={"X-Device-Token": "token"},
                json={
                    "action_type": "check_in",
                    "employee_id": "employee-1",
                    "photo": "base64-photo",
                    "client_uuid": "client-1",
                },
            )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["success"], False)
        tx_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
