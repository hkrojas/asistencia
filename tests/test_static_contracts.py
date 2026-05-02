import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def project_sources():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        parts = set(relative.parts)
        if parts & {".git", "node_modules", "dist", "__pycache__"}:
            continue
        if relative.parts[0] in {"docs", "tests"}:
            continue
        if relative.name == "AGENTS.md":
            continue
        if path.suffix.lower() in {".py", ".sql", ".js", ".jsx", ".md"}:
            yield relative, path.read_text(encoding="utf-8", errors="ignore")


class StaticContractTests(unittest.TestCase):
    def test_admin_routes_compile(self):
        source = read("backend/routes/admin.py")
        compile(source, "backend/routes/admin.py", "exec")

    def test_export_csv_reads_period_id_from_query_string(self):
        source = read("backend/routes/admin.py")
        self.assertIn("request.args.get('period_id')", source)

    def test_attendance_state_returns_register_compatible_actions(self):
        source = read("backend/routes/attendance.py")
        self.assertIn("'check_out' if last['punch_type'] == 'in' else 'check_in'", source)

    def test_schema_devices_match_api_contract(self):
        schema = read("backend/schema.sql")
        match = re.search(r"CREATE TABLE devices \((.*?)\);", schema, re.S)
        self.assertIsNotNone(match, "devices table is missing")

        devices_block = match.group(1)
        self.assertIn("token_hash", devices_block)
        self.assertIn("building_id", devices_block)
        self.assertNotIn("device_token", devices_block)
        self.assertNotRegex(devices_block, r"employee_id\s+UUID\s+NOT NULL")

    def test_schema_creates_pairing_codes_table_used_by_api(self):
        schema = read("backend/schema.sql")
        self.assertIn("CREATE TABLE device_pairing_codes", schema)

    def test_schema_creates_payroll_periods_before_daily_timesheets(self):
        schema = read("backend/schema.sql")
        self.assertLess(
            schema.index("CREATE TABLE payroll_periods"),
            schema.index("CREATE TABLE daily_timesheets"),
        )

    def test_schema_keeps_seed_device_compatible_with_hashed_tokens(self):
        schema = read("backend/schema.sql")
        self.assertIn("INSERT INTO devices (id, token_hash, employee_id, building_id, alias)", schema)

    def test_backend_routes_use_schedule_assignments_contract(self):
        admin = read("backend/routes/admin.py")
        schedules = read("backend/routes/schedules.py")
        self.assertNotIn("FROM schedules", admin)
        self.assertNotIn("JOIN schedules", admin)
        self.assertNotIn("FROM schedules", schedules)
        self.assertIn("FROM schedule_assignments", schedules)

    def test_expo_secure_store_is_declared(self):
        package = json.loads(read("package.json"))
        self.assertIn("expo-secure-store", package.get("dependencies", {}))

    def test_backend_runtime_dependencies_are_declared(self):
        requirements = read("backend/requirements.txt")
        self.assertIn("PyJWT", requirements)

    def test_env_example_does_not_include_realistic_password(self):
        env_example = read("backend/.env.example")
        self.assertNotIn("Barcelona01064", env_example)

    def test_backend_admin_cors_allows_vite_dev_origin(self):
        sys.path.insert(0, str(ROOT / "backend"))
        try:
            from app import create_app

            app = create_app()
            client = app.test_client()
            response = client.open(
                "/v1/admin/login",
                method="OPTIONS",
                headers={
                    "Origin": "http://127.0.0.1:5174",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                },
            )

            self.assertEqual(
                response.headers.get("Access-Control-Allow-Origin"),
                "http://127.0.0.1:5174",
            )
        finally:
            sys.path.remove(str(ROOT / "backend"))

    def test_frontend_api_base_url_is_configurable_for_local_hosts(self):
        api = read("frontend-web/src/services/api.js")
        self.assertIn("import.meta.env.VITE_API_BASE_URL", api)
        self.assertIn("window.location.hostname", api)
        self.assertNotIn("baseURL: 'http://localhost:5000/v1'", api)

    def test_schema_does_not_seed_known_admin_user(self):
        schema = read("backend/schema.sql")
        self.assertNotIn("INSERT INTO system_users", schema)
        self.assertNotIn("'admin'", schema)
        self.assertNotIn("admin123", schema)

        seed = read("backend/dev_seed_admin.py")
        self.assertIn("DEV_ADMIN_USERNAME", seed)
        self.assertIn("DEV_ADMIN_PASSWORD", seed)
        self.assertIn("INSERT INTO system_users", seed)

    def test_shared_kiosk_attendance_resolves_employee_per_request(self):
        source = read("backend/routes/attendance.py")
        self.assertIn("def _resolve_employee_id", source)
        self.assertIn("request.args.get('employee_id')", source)
        self.assertIn("data.get('employee_id')", source)
        self.assertIn("'requires_employee': True", source)

    def test_failed_biometrics_do_not_insert_raw_punch(self):
        source = read("backend/routes/attendance.py")
        rejection_index = source.index("if not match:")
        insert_index = source.index("INSERT INTO raw_punches")
        self.assertLess(rejection_index, insert_index)
        self.assertNotIn("'record_id': str(row['id'])", source)

    def test_mobile_attendance_sends_selected_employee_for_kiosks(self):
        api = read("src/services/api.js")
        screen = read("src/screens/AttendanceScreen.js")
        self.assertIn("fetchKioskEmployees", api)
        self.assertIn("employee_id: employeeId", api)
        self.assertIn("selectedEmployeeId", screen)
        self.assertIn("fetchCurrentState(token, selectedEmployeeId)", screen)

    def test_wfm_manager_normalizes_anomaly_flags_before_rendering(self):
        source = read("frontend-web/src/pages/WfmManager.jsx")
        self.assertIn("const normalizeAnomalyFlags", source)
        self.assertNotIn("JSON.parse(issue.anomaly_flags)", source)

    def test_compensate_exception_action_matches_schema_contract(self):
        source = read("frontend-web/src/components/ExceptionsManager.jsx")
        self.assertNotIn("handleResolve(ex.id, 'compensate')", source)
        self.assertIn("handleResolve(ex.id, 'leave_early')", source)

    def test_recent_attendance_uses_device_building_when_available(self):
        source = read("backend/routes/admin.py")
        self.assertIn("LEFT JOIN devices d ON d.id = rp.device_id", source)
        self.assertIn("COALESCE(rp.building_id, d.building_id, e.primary_building_id)", source)

    def test_no_commercial_invoicing_terms_outside_docs_and_guard_tests(self):
        forbidden_terms = [
            "invoice",
            "sales_invoice",
            "tax_invoice",
            "billing",
            "factura",
            "comprobante",
            "boleta de venta",
            "igv",
            "credit_note",
            "debit_note",
            "invoice_series",
            "sunat_ticket",
            "cdr",
        ]
        violations = []
        for relative, content in project_sources():
            lower = content.lower()
            for term in forbidden_terms:
                if term in lower:
                    violations.append(f"{relative}: {term}")

        self.assertEqual([], violations)

    def test_no_commercial_invoice_routes_or_schema_tables_exist(self):
        sources = "\n".join(content.lower() for _, content in project_sources())
        forbidden_fragments = [
            "/invoices",
            "/billing",
            "/facturas",
            "/comprobantes",
            "/sunat",
            "create table invoices",
            "create table sales_invoices",
            "create table tax_invoices",
            "create table invoice_series",
        ]

        for fragment in forbidden_fragments:
            self.assertNotIn(fragment, sources)

    def test_no_invoicing_scope_document_exists(self):
        doc = read("docs/alcance_no_facturacion.md")
        self.assertIn("Este proyecto no emite facturas electronicas de venta.", doc)
        self.assertIn("El sistema si genera boletas de pago de remuneraciones.", doc)
        self.assertIn("El sistema si genera lotes de pago de sueldos.", doc)
        self.assertIn("El sistema si genera reportes de costo laboral por edificio.", doc)


if __name__ == "__main__":
    unittest.main()
