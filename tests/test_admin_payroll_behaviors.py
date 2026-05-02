import sys
import unittest
from contextlib import contextmanager
from datetime import date, time
import os
from pathlib import Path
from unittest.mock import patch

import jwt
from flask import Flask


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from routes import admin as admin_module  # noqa: E402
from services import timesheet_engine  # noqa: E402


TEST_JWT_SECRET = "test-secret-key-with-at-least-32-bytes"


class FakeCursor:
    def __init__(self):
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        return {"id": "manual-punch-id"}


@contextmanager
def fake_tx(cursor=None):
    yield object(), cursor or FakeCursor()


def admin_token():
    secret = os.getenv("JWT_SECRET_KEY", TEST_JWT_SECRET)
    return jwt.encode({"user_id": "admin-id", "username": "admin"}, secret, algorithm="HS256")


class AdminPayrollBehaviorTests(unittest.TestCase):
    def setUp(self):
        os.environ["JWT_SECRET_KEY"] = TEST_JWT_SECRET
        app = Flask(__name__)
        app.register_blueprint(admin_module.admin_bp, url_prefix="/v1")
        self.client = app.test_client()
        self.headers = {"Authorization": f"Bearer {admin_token()}"}

    def test_processing_selected_period_uses_period_dates(self):
        period = {
            "id": "period-1",
            "starts_on": date(2026, 4, 1),
            "ends_on": date(2026, 4, 3),
            "state": "open",
        }
        employees = [{"id": "employee-1"}, {"id": "employee-2"}]

        with patch.object(admin_module, "query_one", return_value=period) as query_one, \
             patch.object(admin_module, "query_all", return_value=employees), \
             patch.object(admin_module, "process_timesheet", return_value=True) as process_timesheet:
            response = self.client.post(
                "/v1/admin/timesheets/process",
                headers=self.headers,
                json={"period_id": "period-1"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["days_processed"], 3)
        query_one.assert_called()
        self.assertEqual(process_timesheet.call_count, 6)
        self.assertEqual(
            [call.args[1] for call in process_timesheet.call_args_list[:3]],
            [date(2026, 4, 1), date(2026, 4, 1), date(2026, 4, 2)],
        )

    def test_leave_day_processes_without_unbound_overtime_minutes(self):
        cursor = FakeCursor()
        query_results = [
            {"id": "period-1", "state": "open"},
            {
                "id": "schedule-1",
                "start_time": time(8, 0),
                "end_time": time(17, 0),
                "is_overnight": False,
                "tolerance_minutes": 15,
            },
            {"id": "rate-1"},
            {"leave_type": "Vacaciones", "is_paid": True},
        ]

        with patch.object(timesheet_engine, "query_one", side_effect=query_results), \
             patch.object(timesheet_engine, "query_all", return_value=[]), \
             patch.object(timesheet_engine, "tx", return_value=fake_tx(cursor)):
            result = timesheet_engine.process_timesheet("employee-1", date(2026, 4, 1))

        self.assertTrue(result)
        insert_params = cursor.executed[-1][1]
        self.assertEqual(insert_params[8], 0)
        self.assertEqual(insert_params[9], 0)
        self.assertEqual(insert_params[11], "resolved")

    def test_wfm_manual_resolution_records_audit_exception(self):
        cursor = FakeCursor()
        timesheet = {"employee_id": "employee-1", "logical_date": date(2026, 4, 1)}

        with patch.object(admin_module, "query_one", return_value=timesheet), \
             patch.object(admin_module, "tx", return_value=fake_tx(cursor)), \
             patch.object(admin_module, "process_timesheet", return_value=True):
            response = self.client.post(
                "/v1/admin/wfm/resolve/00000000-0000-0000-0000-000000000001",
                headers=self.headers,
                json={"action": "manual_out", "time": "17:00", "reason": "Olvido marcar salida"},
            )

        self.assertEqual(response.status_code, 200)
        all_sql = "\n".join(sql for sql, _ in cursor.executed)
        self.assertIn("INSERT INTO raw_punches", all_sql)
        self.assertIn("INSERT INTO time_exceptions", all_sql)
        self.assertIn("Olvido marcar salida", str(cursor.executed))

    def test_dashboard_exception_resolution_reprocesses_timesheet(self):
        cursor = FakeCursor()
        log_data = {"employee_id": "employee-1", "punch_time": date(2026, 4, 1)}

        with patch.object(admin_module, "query_one", return_value=log_data), \
             patch.object(admin_module, "tx", return_value=fake_tx(cursor)), \
             patch.object(admin_module, "process_timesheet", return_value=True) as process_timesheet:
            response = self.client.post(
                "/v1/admin/exceptions/resolve",
                headers=self.headers,
                json={"logId": "log-1", "resolutionType": "overtime", "adminId": "admin-id"},
            )

        self.assertEqual(response.status_code, 200)
        process_timesheet.assert_called_once_with("employee-1", date(2026, 4, 1))

    def test_close_period_rejects_unresolved_wfm_issues(self):
        cursor = FakeCursor()
        query_results = [
            {"id": "period-1", "state": "open"},
            {"unresolved_count": 2},
        ]

        with patch.object(admin_module, "query_one", side_effect=query_results), \
             patch.object(admin_module, "tx", return_value=fake_tx(cursor)):
            response = self.client.post(
                "/v1/admin/payroll-periods/00000000-0000-0000-0000-000000000001/close",
                headers=self.headers,
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["unresolved_count"], 2)
        self.assertEqual(cursor.executed, [])

    def test_admin_stats_returns_calculated_punctuality(self):
        with patch.object(admin_module, "query_one", return_value={
            "active_employees": 2,
            "present_today": 1,
            "total_buildings": 1,
            "avg_punctuality": 67,
        }):
            response = self.client.get("/v1/admin/stats", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["avg_punctuality"], 67)


if __name__ == "__main__":
    unittest.main()
