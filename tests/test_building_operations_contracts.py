import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class BuildingOperationsSchemaTests(unittest.TestCase):
    def test_schema_contains_building_operations_domain_tables(self):
        schema = read("backend/schema.sql")

        for table_name in [
            "companies",
            "employers",
            "building_admin_assignments",
            "employee_profiles",
            "employment_contracts",
            "employee_assignments",
            "shift_templates",
            "shift_instances",
            "operational_movements",
            "operational_incidents",
            "daily_building_reports",
            "building_prepayrolls",
            "building_prepayroll_items",
            "building_prepayroll_observations",
            "payroll_concepts",
            "payroll_runs",
            "payroll_items",
            "payroll_snapshots",
            "payroll_payslips",
            "salary_payment_batches",
            "salary_payment_items",
            "building_cost_reports",
            "audit_events",
        ]:
            self.assertIn(f"CREATE TABLE {table_name}", schema)

    def test_buildings_and_raw_punches_capture_effective_employer_and_building(self):
        schema = read("backend/schema.sql")
        buildings = schema[schema.index("CREATE TABLE buildings") : schema.index("CREATE TABLE device_pairing_codes")]
        raw_punches = schema[schema.index("CREATE TABLE raw_punches") : schema.index("CREATE INDEX idx_punches_employee")]

        self.assertIn("employer_id", buildings)
        self.assertIn("cost_center", buildings)
        self.assertIn("district", buildings)
        self.assertIn("managed_client_name", buildings)
        self.assertNotIn("client_name     VARCHAR", buildings)
        self.assertIn("building_id", raw_punches)

    def test_building_operations_migration_exists_for_existing_databases(self):
        migration = read("backend/migrations/001_building_operations.sql")
        self.assertIn("CREATE TABLE IF NOT EXISTS companies", migration)
        self.assertIn("ALTER TABLE buildings ADD COLUMN IF NOT EXISTS employer_id", migration)
        self.assertIn("CREATE TABLE IF NOT EXISTS building_prepayrolls", migration)
        self.assertIn("CREATE TABLE IF NOT EXISTS payroll_runs", migration)
        self.assertIn("CREATE TABLE IF NOT EXISTS building_cost_reports", migration)

    def test_remuneration_tables_use_unambiguous_names(self):
        schema = read("backend/schema.sql")
        migration = read("backend/migrations/001_building_operations.sql")
        combined = f"{schema}\n{migration}"

        for expected in [
            "CREATE TABLE payroll_payslips",
            "CREATE TABLE salary_payment_batches",
            "CREATE TABLE salary_payment_items",
            "CREATE TABLE building_cost_reports",
        ]:
            self.assertIn(expected, combined)

        for ambiguous in [
            "CREATE TABLE payslips",
            "CREATE TABLE payment_batches",
            "CREATE TABLE payment_items",
        ]:
            self.assertNotIn(ambiguous, combined)

    def test_building_cost_reports_do_not_store_commercial_fiscal_fields(self):
        schema = read("backend/schema.sql")
        block = schema[
            schema.index("CREATE TABLE building_cost_reports") : schema.index("CREATE TABLE payroll_payslips")
        ]

        for field in [
            "payroll_period_id",
            "building_id",
            "payroll_run_id",
            "cost_center",
            "total_labor_cost",
            "total_regular_hours",
            "total_overtime_hours",
            "total_mobility",
            "total_coverages_received",
            "total_coverages_sent",
            "total_prorations",
            "observations",
            "state",
            "created_at",
            "created_by",
        ]:
            self.assertIn(field, block)

        for forbidden in [
            "invoice",
            "sales_invoice",
            "tax_invoice",
            "billing",
            "factura",
            "comprobante",
            "igv",
            "credit_note",
            "debit_note",
            "invoice_series",
            "sunat_ticket",
            "cdr",
            "correlativo",
            "serie",
        ]:
            self.assertNotIn(forbidden, block.lower())


class BuildingOperationsServiceTests(unittest.TestCase):
    def test_cross_employer_coverage_requires_legal_validation(self):
        from services.operations import classify_coverage

        result = classify_coverage(
            {"id": "origin", "employer_ruc": "20111111111"},
            {"id": "destination", "employer_ruc": "20222222222"},
        )

        self.assertTrue(result["is_cross_employer"])
        self.assertTrue(result["legal_validation_required"])
        self.assertTrue(result["approval_blocked"])
        self.assertEqual(result["status"], "pending_legal_validation")
        self.assertIn("SUPUESTO PENDIENTE DE VALIDACION LEGAL", result["legal_note"])

    def test_same_employer_coverage_starts_requested_without_legal_block(self):
        from services.operations import classify_coverage

        result = classify_coverage(
            {"id": "origin", "employer_ruc": "20111111111"},
            {"id": "destination", "employer_ruc": "20111111111"},
        )

        self.assertFalse(result["is_cross_employer"])
        self.assertFalse(result["legal_validation_required"])
        self.assertFalse(result["approval_blocked"])
        self.assertEqual(result["status"], "requested")

    def test_prepayroll_send_is_blocked_by_critical_operational_issues(self):
        from services.operations import validate_prepayroll_submission

        result = validate_prepayroll_submission(
            pending_coverages=1,
            unclassified_absences=2,
            unapproved_overtime=3,
            unrevised_critical_shifts=4,
        )

        self.assertFalse(result["can_send"])
        self.assertEqual(result["blocker_count"], 10)
        self.assertIn("coberturas pendientes", " ".join(result["errors"]))
        self.assertIn("faltas sin clasificar", " ".join(result["errors"]))
        self.assertIn("horas extra sin aprobacion", " ".join(result["errors"]))


class PayrollServiceTests(unittest.TestCase):
    def test_payroll_totals_separate_income_discounts_contributions_and_net(self):
        from services.payroll_engine import summarize_payroll_items

        totals = summarize_payroll_items(
            [
                {"item_type": "income", "amount": 1500},
                {"item_type": "worker_contribution", "amount": 195},
                {"item_type": "discount", "amount": 100},
                {"item_type": "employer_contribution", "amount": 135},
            ]
        )

        self.assertEqual(totals["gross_income"], 1500)
        self.assertEqual(totals["worker_contributions"], 195)
        self.assertEqual(totals["discounts"], 100)
        self.assertEqual(totals["employer_contributions"], 135)
        self.assertEqual(totals["net_pay"], 1205)
        self.assertEqual(totals["company_cost"], 1635)


class PermissionServiceTests(unittest.TestCase):
    def test_building_admin_scope_is_limited_to_assigned_buildings(self):
        from services.permissions import can_access_building

        self.assertTrue(can_access_building("BuildingAdmin", ["building-1"], "building-1"))
        self.assertFalse(can_access_building("BuildingAdmin", ["building-1"], "building-2"))
        self.assertTrue(can_access_building("HR", [], "building-2"))
        self.assertTrue(can_access_building("Superadmin", [], "building-2"))

    def test_wage_visibility_requires_explicit_permission_for_building_admin(self):
        from services.permissions import can_view_wages

        self.assertFalse(can_view_wages("BuildingAdmin", assignment={"can_view_wages": False}))
        self.assertTrue(can_view_wages("BuildingAdmin", assignment={"can_view_wages": True}))
        self.assertTrue(can_view_wages("HR", assignment=None))
        self.assertTrue(can_view_wages("Finance", assignment=None))
        self.assertFalse(can_view_wages("Auditor", assignment=None))


class BuildingOperationsFrontendContractTests(unittest.TestCase):
    def test_frontend_exposes_building_operations_routes(self):
        app = read("frontend-web/src/App.jsx")
        sidebar = read("frontend-web/src/components/Sidebar.jsx")
        api = read("frontend-web/src/services/api.js")

        for route in [
            'path="operations"',
            'path="prepayroll"',
            'path="payroll"',
            'path="payments"',
            'path="admin"',
        ]:
            self.assertIn(route, app)

        for label in ["Operación", "Preplanilla", "Planilla", "Pagos de sueldos", "Administración"]:
            self.assertIn(label, sidebar)

        for export_name in [
            "getOperationsDashboard",
            "createCoverage",
            "createOperationalIncident",
            "generateBuildingPrepayroll",
            "sendBuildingPrepayroll",
            "observeBuildingPrepayroll",
            "approveBuildingPrepayroll",
            "getPayrollConsolidation",
            "createPayrollRun",
            "closePayrollRun",
            "createSalaryPaymentBatch",
            "generatePayrollPayslips",
        ]:
            self.assertIn(f"export const {export_name}", api)

    def test_frontend_labels_payments_as_salary_and_remuneration_documents(self):
        payments = read("frontend-web/src/pages/Payments.jsx")
        api = read("frontend-web/src/services/api.js")

        self.assertIn("Boletas de pago", payments)
        self.assertIn("Boletas de pago de remuneraciones", payments)
        self.assertIn("Pagos de sueldos", payments)
        self.assertIn("Lote de pago de sueldos", payments)
        self.assertNotIn("Boletas y Pagos", payments)
        self.assertIn("/admin/payroll-payslips/generate", api)
        self.assertIn("/admin/salary-payment-batches", api)
        self.assertNotIn("/admin/payslips/generate", api)
        self.assertNotIn("/admin/payment-batches", api)


class BuildingOperationsBackendContractTests(unittest.TestCase):
    def test_operations_blueprint_is_registered(self):
        app = read("backend/app.py")
        self.assertIn("from routes.operations import operations_bp", app)
        self.assertIn("app.register_blueprint(operations_bp, url_prefix='/v1')", app)

    def test_payroll_payslips_and_salary_payment_batches_require_closed_runs(self):
        source = read("backend/routes/operations.py")

        self.assertIn('@operations_bp.route("/admin/payroll-payslips/generate"', source)
        self.assertIn("def generate_payroll_payslips", source)
        self.assertIn("INSERT INTO payroll_payslips", source)
        self.assertIn('run["state"] != "closed"', source)
        self.assertIn("Solo se generan boletas de pago", source)

        self.assertIn('@operations_bp.route("/admin/salary-payment-batches"', source)
        self.assertIn("def create_salary_payment_batch", source)
        self.assertIn("INSERT INTO salary_payment_batches", source)
        self.assertIn("Solo se preparan pagos de sueldos", source)
        self.assertNotIn('@operations_bp.route("/admin/payslips/generate"', source)
        self.assertNotIn('@operations_bp.route("/admin/payment-batches"', source)
