-- Building operations, prepayroll, payroll remuneration documents, salary payments, and audit foundation.
-- Idempotent migration for databases created before schema V4.

CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_name VARCHAR(180) NOT NULL,
    ruc VARCHAR(11) NOT NULL UNIQUE,
    fiscal_address VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS employers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    legal_name VARCHAR(180) NOT NULL,
    ruc VARCHAR(11) NOT NULL UNIQUE,
    employer_type VARCHAR(30) NOT NULL DEFAULT 'administrator',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE buildings ADD COLUMN IF NOT EXISTS employer_id UUID REFERENCES employers(id) ON DELETE SET NULL;
ALTER TABLE buildings ADD COLUMN IF NOT EXISTS code VARCHAR(30);
ALTER TABLE buildings ADD COLUMN IF NOT EXISTS district VARCHAR(100);
ALTER TABLE buildings ADD COLUMN IF NOT EXISTS managed_client_name VARCHAR(150);
ALTER TABLE buildings ADD COLUMN IF NOT EXISTS cost_center VARCHAR(50);
ALTER TABLE buildings ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'active';

ALTER TABLE raw_punches ADD COLUMN IF NOT EXISTS building_id UUID REFERENCES buildings(id) ON DELETE SET NULL;
ALTER TABLE system_users ADD COLUMN IF NOT EXISTS role VARCHAR(40) NOT NULL DEFAULT 'Superadmin';

CREATE TABLE IF NOT EXISTS building_admin_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES system_users(id) ON DELETE CASCADE,
    building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    valid_from DATE NOT NULL DEFAULT CURRENT_DATE,
    valid_to DATE,
    can_view_wages BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, building_id, valid_from)
);

CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor_user_id UUID REFERENCES system_users(id) ON DELETE SET NULL,
    module VARCHAR(60) NOT NULL,
    action VARCHAR(80) NOT NULL,
    entity_type VARCHAR(80) NOT NULL,
    entity_id UUID,
    old_data JSONB,
    new_data JSONB,
    reason TEXT,
    ip_address VARCHAR(80),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS employee_profiles (
    employee_id UUID PRIMARY KEY REFERENCES employees(id) ON DELETE CASCADE,
    document_type VARCHAR(20),
    document_number VARCHAR(30),
    birth_date DATE,
    phone VARCHAR(40),
    email VARCHAR(120),
    address VARCHAR(255),
    pension_system VARCHAR(20),
    pension_provider VARCHAR(80),
    health_regime VARCHAR(80),
    bank_name VARCHAR(80),
    bank_account_number VARCHAR(80),
    bank_cci VARCHAR(30),
    bank_validation_status VARCHAR(20) DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS employment_contracts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    employer_id UUID REFERENCES employers(id) ON DELETE SET NULL,
    contract_type VARCHAR(60) NOT NULL,
    starts_on DATE NOT NULL,
    ends_on DATE,
    base_salary NUMERIC(12,2),
    currency VARCHAR(3) NOT NULL DEFAULT 'PEN',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    termination_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS employee_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    manager_user_id UUID REFERENCES system_users(id) ON DELETE SET NULL,
    cost_center VARCHAR(50),
    assignment_type VARCHAR(30) NOT NULL DEFAULT 'base',
    valid_from DATE NOT NULL DEFAULT CURRENT_DATE,
    valid_to DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS shift_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    starts_at TIME NOT NULL,
    ends_at TIME NOT NULL,
    is_overnight BOOLEAN NOT NULL DEFAULT FALSE,
    role_name VARCHAR(80),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS shift_instances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID REFERENCES shift_templates(id) ON DELETE SET NULL,
    building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    employee_id UUID REFERENCES employees(id) ON DELETE SET NULL,
    shift_date DATE NOT NULL,
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'scheduled',
    replacement_for UUID REFERENCES employees(id) ON DELETE SET NULL,
    created_by UUID REFERENCES system_users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS operational_movements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    origin_building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    destination_building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,
    movement_type VARCHAR(40) NOT NULL,
    reason TEXT NOT NULL,
    requested_by UUID REFERENCES system_users(id) ON DELETE SET NULL,
    approved_by UUID REFERENCES system_users(id) ON DELETE SET NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'requested',
    generates_overtime BOOLEAN NOT NULL DEFAULT FALSE,
    generates_mobility BOOLEAN NOT NULL DEFAULT FALSE,
    cost_allocation_rule VARCHAR(40) NOT NULL DEFAULT 'destination_building',
    is_cross_employer BOOLEAN NOT NULL DEFAULT FALSE,
    legal_validation_required BOOLEAN NOT NULL DEFAULT FALSE,
    legal_note TEXT,
    evidence_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS operational_incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    incident_date DATE NOT NULL,
    starts_at TIMESTAMPTZ,
    ends_at TIMESTAMPTZ,
    incident_type VARCHAR(50) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'registered',
    is_paid BOOLEAN,
    recovers_hours BOOLEAN NOT NULL DEFAULT FALSE,
    affects_prepayroll BOOLEAN NOT NULL DEFAULT TRUE,
    affects_payroll BOOLEAN NOT NULL DEFAULT TRUE,
    reason TEXT NOT NULL,
    evidence_url TEXT,
    registered_by UUID REFERENCES system_users(id) ON DELETE SET NULL,
    approved_by UUID REFERENCES system_users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS daily_building_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    report_date DATE NOT NULL,
    administrator_user_id UUID REFERENCES system_users(id) ON DELETE SET NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'draft',
    summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    observations TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (building_id, report_date)
);

CREATE TABLE IF NOT EXISTS building_prepayrolls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    payroll_period_id UUID NOT NULL REFERENCES payroll_periods(id) ON DELETE CASCADE,
    administrator_user_id UUID REFERENCES system_users(id) ON DELETE SET NULL,
    state VARCHAR(40) NOT NULL DEFAULT 'draft',
    blocker_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    submitted_at TIMESTAMPTZ,
    approved_at TIMESTAMPTZ,
    consolidated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (building_id, payroll_period_id)
);

CREATE TABLE IF NOT EXISTS building_prepayroll_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    building_prepayroll_id UUID NOT NULL REFERENCES building_prepayrolls(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    source_building_id UUID REFERENCES buildings(id) ON DELETE SET NULL,
    regular_minutes INTEGER NOT NULL DEFAULT 0,
    overtime_minutes INTEGER NOT NULL DEFAULT 0,
    deficit_minutes INTEGER NOT NULL DEFAULT 0,
    absences_count INTEGER NOT NULL DEFAULT 0,
    late_count INTEGER NOT NULL DEFAULT 0,
    permissions_count INTEGER NOT NULL DEFAULT 0,
    coverage_in_minutes INTEGER NOT NULL DEFAULT 0,
    coverage_out_minutes INTEGER NOT NULL DEFAULT 0,
    estimated_gross NUMERIC(12,2) NOT NULL DEFAULT 0,
    estimated_net NUMERIC(12,2) NOT NULL DEFAULT 0,
    status VARCHAR(30) NOT NULL DEFAULT 'draft',
    notes TEXT
);

CREATE TABLE IF NOT EXISTS building_prepayroll_observations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    building_prepayroll_id UUID NOT NULL REFERENCES building_prepayrolls(id) ON DELETE CASCADE,
    reason_code VARCHAR(60) NOT NULL,
    comment TEXT NOT NULL,
    state VARCHAR(30) NOT NULL DEFAULT 'open',
    observed_by UUID REFERENCES system_users(id) ON DELETE SET NULL,
    answered_by UUID REFERENCES system_users(id) ON DELETE SET NULL,
    answer TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    answered_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS payroll_concepts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(30) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    item_type VARCHAR(30) NOT NULL,
    is_remunerative BOOLEAN NOT NULL DEFAULT TRUE,
    affects_afp_onp BOOLEAN NOT NULL DEFAULT FALSE,
    affects_essalud BOOLEAN NOT NULL DEFAULT FALSE,
    affects_fifth_tax BOOLEAN NOT NULL DEFAULT FALSE,
    affects_cts BOOLEAN NOT NULL DEFAULT FALSE,
    affects_gratification BOOLEAN NOT NULL DEFAULT FALSE,
    affects_vacation BOOLEAN NOT NULL DEFAULT FALSE,
    affects_liquidation BOOLEAN NOT NULL DEFAULT FALSE,
    formula_key VARCHAR(80) NOT NULL,
    legal_source TEXT,
    valid_from DATE NOT NULL DEFAULT CURRENT_DATE,
    valid_to DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS payroll_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payroll_period_id UUID NOT NULL REFERENCES payroll_periods(id) ON DELETE CASCADE,
    state VARCHAR(40) NOT NULL DEFAULT 'draft',
    total_gross NUMERIC(14,2) NOT NULL DEFAULT 0,
    total_discounts NUMERIC(14,2) NOT NULL DEFAULT 0,
    total_worker_contributions NUMERIC(14,2) NOT NULL DEFAULT 0,
    total_employer_contributions NUMERIC(14,2) NOT NULL DEFAULT 0,
    total_net NUMERIC(14,2) NOT NULL DEFAULT 0,
    closed_at TIMESTAMPTZ,
    closed_by UUID REFERENCES system_users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS payroll_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payroll_run_id UUID NOT NULL REFERENCES payroll_runs(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    building_id UUID REFERENCES buildings(id) ON DELETE SET NULL,
    concept_id UUID REFERENCES payroll_concepts(id) ON DELETE SET NULL,
    item_type VARCHAR(30) NOT NULL,
    quantity NUMERIC(12,4) NOT NULL DEFAULT 1,
    amount NUMERIC(12,2) NOT NULL,
    formula_key VARCHAR(80),
    calculation_base JSONB NOT NULL DEFAULT '{}'::jsonb,
    explanation TEXT
);

CREATE TABLE IF NOT EXISTS payroll_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payroll_run_id UUID NOT NULL REFERENCES payroll_runs(id) ON DELETE CASCADE,
    snapshot_data JSONB NOT NULL,
    closure_hash VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS building_cost_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payroll_period_id UUID NOT NULL REFERENCES payroll_periods(id) ON DELETE CASCADE,
    building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    payroll_run_id UUID REFERENCES payroll_runs(id) ON DELETE SET NULL,
    cost_center VARCHAR(50),
    total_labor_cost NUMERIC(14,2) NOT NULL DEFAULT 0,
    total_regular_hours NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_overtime_hours NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_mobility NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_coverages_received NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_coverages_sent NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_prorations NUMERIC(14,2) NOT NULL DEFAULT 0,
    observations TEXT,
    state VARCHAR(20) NOT NULL DEFAULT 'draft'
        CHECK (state IN ('draft', 'generated', 'exported')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES system_users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS payroll_payslips (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payroll_run_id UUID NOT NULL REFERENCES payroll_runs(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    version INTEGER NOT NULL DEFAULT 1,
    state VARCHAR(30) NOT NULL DEFAULT 'generated',
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sent_at TIMESTAMPTZ,
    UNIQUE (payroll_run_id, employee_id, version)
);

CREATE TABLE IF NOT EXISTS salary_payment_batches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payroll_run_id UUID NOT NULL REFERENCES payroll_runs(id) ON DELETE CASCADE,
    state VARCHAR(30) NOT NULL DEFAULT 'pending',
    total_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
    prepared_by UUID REFERENCES system_users(id) ON DELETE SET NULL,
    proof_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    paid_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS salary_payment_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    salary_payment_batch_id UUID NOT NULL REFERENCES salary_payment_batches(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    bank_name VARCHAR(80),
    bank_account_number VARCHAR(80),
    amount NUMERIC(12,2) NOT NULL,
    state VARCHAR(30) NOT NULL DEFAULT 'pending',
    paid_at TIMESTAMPTZ
);
