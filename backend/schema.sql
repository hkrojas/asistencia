-- ============================================================
-- Asistencia App — PostgreSQL Schema (V3 - WFM Core Domain)
-- ============================================================

-- Extensión para UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Limpieza preventiva
DROP TABLE IF EXISTS salary_payment_items CASCADE;
DROP TABLE IF EXISTS salary_payment_batches CASCADE;
DROP TABLE IF EXISTS payroll_payslips CASCADE;
DROP TABLE IF EXISTS building_cost_reports CASCADE;
DROP TABLE IF EXISTS payroll_snapshots CASCADE;
DROP TABLE IF EXISTS payroll_items CASCADE;
DROP TABLE IF EXISTS payroll_runs CASCADE;
DROP TABLE IF EXISTS payroll_concepts CASCADE;
DROP TABLE IF EXISTS building_prepayroll_observations CASCADE;
DROP TABLE IF EXISTS building_prepayroll_items CASCADE;
DROP TABLE IF EXISTS building_prepayrolls CASCADE;
DROP TABLE IF EXISTS daily_building_reports CASCADE;
DROP TABLE IF EXISTS operational_incidents CASCADE;
DROP TABLE IF EXISTS operational_movements CASCADE;
DROP TABLE IF EXISTS shift_instances CASCADE;
DROP TABLE IF EXISTS shift_templates CASCADE;
DROP TABLE IF EXISTS employee_assignments CASCADE;
DROP TABLE IF EXISTS employment_contracts CASCADE;
DROP TABLE IF EXISTS employee_profiles CASCADE;
DROP TABLE IF EXISTS building_admin_assignments CASCADE;
DROP TABLE IF EXISTS audit_events CASCADE;
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS daily_timesheets CASCADE;
DROP TABLE IF EXISTS time_exceptions CASCADE;
DROP TABLE IF EXISTS raw_punches CASCADE;
DROP TABLE IF EXISTS attendance_logs CASCADE; -- Deprecated
DROP TABLE IF EXISTS leaves CASCADE;
DROP TABLE IF EXISTS compensation_rates CASCADE;
DROP TABLE IF EXISTS schedule_assignments CASCADE;
DROP TABLE IF EXISTS device_pairing_codes CASCADE;
DROP TABLE IF EXISTS payroll_periods CASCADE;
DROP TABLE IF EXISTS schedules CASCADE;
DROP TABLE IF EXISTS system_users CASCADE;
DROP TABLE IF EXISTS devices CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS roles CASCADE;
DROP TABLE IF EXISTS buildings CASCADE;
DROP TABLE IF EXISTS employers CASCADE;
DROP TABLE IF EXISTS companies CASCADE;
DROP TYPE IF EXISTS timesheet_status CASCADE;

-- ──────────────────────────────────────────────────────────────
-- 1. buildings — Sedes o establecimientos
-- ──────────────────────────────────────────────────────────────
CREATE TABLE companies (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_name   VARCHAR(180) NOT NULL,
    ruc             VARCHAR(11)  NOT NULL UNIQUE,
    fiscal_address  VARCHAR(255),
    status          VARCHAR(20)  NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'inactive')),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE employers (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id      UUID         REFERENCES companies(id) ON DELETE CASCADE,
    legal_name      VARCHAR(180) NOT NULL,
    ruc             VARCHAR(11)  NOT NULL UNIQUE,
    employer_type   VARCHAR(30)  NOT NULL DEFAULT 'administrator'
                        CHECK (employer_type IN ('administrator', 'building_client', 'third_party')),
    status          VARCHAR(20)  NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'inactive')),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE buildings (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employer_id     UUID         REFERENCES employers(id) ON DELETE SET NULL,
    code            VARCHAR(30)  UNIQUE,
    name            VARCHAR(100) NOT NULL,
    address         VARCHAR(255),
    district        VARCHAR(100),
    managed_client_name VARCHAR(150),
    cost_center     VARCHAR(50),
    status          VARCHAR(20)  NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'suspended', 'terminated')),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE device_pairing_codes (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code_hash   VARCHAR(255) NOT NULL,
    building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    expires_at  TIMESTAMPTZ NOT NULL,
    is_used     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ──────────────────────────────────────────────────────────────
-- 2. roles — Niveles de acceso (Sistema)
-- ──────────────────────────────────────────────────────────────
CREATE TABLE roles (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(50) NOT NULL UNIQUE -- 'Admin', 'HR', 'Kiosk'
);

-- ──────────────────────────────────────────────────────────────
-- 3. employees — Catálogo de empleados
-- ──────────────────────────────────────────────────────────────
CREATE TABLE employees (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name           VARCHAR(150) NOT NULL,
    job_title           VARCHAR(100), -- Cargo operativo
    status              VARCHAR(20)  NOT NULL DEFAULT 'active'
                            CHECK (status IN ('active', 'inactive', 'suspended')),
    role_id             UUID         NOT NULL REFERENCES roles(id),
    primary_building_id UUID         REFERENCES buildings(id) ON DELETE SET NULL,
    face_id_aws         VARCHAR(255),
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ──────────────────────────────────────────────────────────────
-- 4. devices — Dispositivos / Quioscos
-- ──────────────────────────────────────────────────────────────
CREATE TABLE devices (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token_hash      VARCHAR(255) NOT NULL UNIQUE,
    employee_id     UUID         REFERENCES employees(id) ON DELETE CASCADE,
    building_id     UUID         REFERENCES buildings(id) ON DELETE CASCADE,
    alias           VARCHAR(100),
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ──────────────────────────────────────────────────────────────
-- 5. schedule_assignments — Horarios Planificados (SCD Tipo 2)
-- ──────────────────────────────────────────────────────────────
CREATE TABLE schedule_assignments (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id         UUID         NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    building_id         UUID         REFERENCES buildings(id) ON DELETE SET NULL,
    day_of_week         SMALLINT     NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    start_time          TIME         NOT NULL,
    end_time            TIME         NOT NULL,
    is_overnight        BOOLEAN      NOT NULL DEFAULT FALSE,
    tolerance_minutes   INTEGER      NOT NULL DEFAULT 15,
    valid_from          DATE         NOT NULL DEFAULT CURRENT_DATE,
    valid_to            DATE,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ──────────────────────────────────────────────────────────────
-- 5.1 compensation_rates — Tarifas y Sueldos (SCD Tipo 2)
-- ──────────────────────────────────────────────────────────────
CREATE TABLE compensation_rates (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id         UUID         NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    hourly_wage         NUMERIC(12,2) NOT NULL,
    overtime_multiplier NUMERIC(4,2)  NOT NULL DEFAULT 1.5,
    valid_from          DATE         NOT NULL DEFAULT CURRENT_DATE,
    valid_to            DATE,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ──────────────────────────────────────────────────────────────
-- 5.2 leaves — Permisos y Ausencias
-- ──────────────────────────────────────────────────────────────
CREATE TABLE leaves (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id         UUID         NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    logical_date        DATE         NOT NULL,
    leave_type          VARCHAR(50)  NOT NULL, -- 'Vacaciones', 'Salud', 'Personal'
    is_paid             BOOLEAN      DEFAULT TRUE,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (employee_id, logical_date)
);

CREATE TABLE payroll_periods (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(100) NOT NULL,
    starts_on   DATE NOT NULL,
    ends_on     DATE NOT NULL,
    state       VARCHAR(20) DEFAULT 'open' CHECK (state IN ('open', 'closed')),
    closed_at   TIMESTAMPTZ,
    closed_by   UUID,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────────────────────────────
-- 6. raw_punches — Eventos de Marcación (Inmutable)
-- ──────────────────────────────────────────────────────────────
CREATE TABLE raw_punches (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id         UUID         REFERENCES devices(id) ON DELETE SET NULL,
    building_id       UUID         REFERENCES buildings(id) ON DELETE SET NULL,
    employee_id       UUID         NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    punch_time        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    punch_type        VARCHAR(10)  NOT NULL CHECK (punch_type IN ('in', 'out')),
    confidence_score  NUMERIC(5,2),
    offline_sync      BOOLEAN      NOT NULL DEFAULT FALSE,
    client_uuid       UUID         UNIQUE,
    ingest_status     VARCHAR(20)  DEFAULT 'accepted' CHECK (ingest_status IN ('accepted', 'late_pending_review', 'rejected')),
    biometric_status  VARCHAR(20)  DEFAULT 'unavailable' CHECK (biometric_status IN ('passed', 'failed', 'unavailable', 'bypassed')),
    biometric_provider VARCHAR(50),
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_punches_employee ON raw_punches (employee_id);
CREATE INDEX idx_punches_time     ON raw_punches (punch_time);

-- ──────────────────────────────────────────────────────────────
-- 7. daily_timesheets — Jornadas Interpretadas
-- ──────────────────────────────────────────────────────────────
CREATE TYPE timesheet_status AS ENUM ('incomplete', 'perfect', 'exception', 'resolved');

CREATE TABLE daily_timesheets (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id             UUID         NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    logical_date            DATE         NOT NULL,
    schedule_assignment_id  UUID         REFERENCES schedule_assignments(id) ON DELETE SET NULL,
    compensation_rate_id    UUID         REFERENCES compensation_rates(id) ON DELETE SET NULL,
    payroll_period_id       UUID         REFERENCES payroll_periods(id) ON DELETE SET NULL,
    first_punch_in          TIMESTAMPTZ,
    last_punch_out          TIMESTAMPTZ,
    regular_minutes         INTEGER      DEFAULT 0,
    overtime_minutes        INTEGER      DEFAULT 0,
    deficit_minutes         INTEGER      DEFAULT 0,
    worked_minutes_total    INTEGER      DEFAULT 0,
    status                  timesheet_status NOT NULL DEFAULT 'incomplete',
    anomaly_flags           JSONB        DEFAULT '[]'::jsonb,
    is_locked               BOOLEAN      DEFAULT FALSE,
    created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (employee_id, logical_date)
);

-- ──────────────────────────────────────────────────────────────
-- 8. audit_logs — Registro de cambios (Gobernanza)
-- ──────────────────────────────────────────────────────────────
CREATE TABLE audit_logs (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name        VARCHAR(50)  NOT NULL,
    record_id         UUID         NOT NULL,
    action            VARCHAR(10)  NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_data          JSONB,
    new_data          JSONB,
    changed_by_id     UUID         REFERENCES employees(id) ON DELETE SET NULL,
    reason            TEXT,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ──────────────────────────────────────────────────────────────
-- 10. system_users — Autenticación del Panel
-- ──────────────────────────────────────────────────────────────
CREATE TABLE system_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(40) NOT NULL DEFAULT 'Superadmin'
        CHECK (role IN ('Superadmin', 'CompanyAdmin', 'HR', 'Finance', 'BuildingAdmin', 'Supervisor', 'Worker', 'Auditor')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE building_admin_assignments (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES system_users(id) ON DELETE CASCADE,
    building_id     UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    valid_from      DATE NOT NULL DEFAULT CURRENT_DATE,
    valid_to        DATE,
    can_view_wages  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, building_id, valid_from)
);

CREATE TABLE audit_events (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor_user_id   UUID REFERENCES system_users(id) ON DELETE SET NULL,
    module          VARCHAR(60) NOT NULL,
    action          VARCHAR(80) NOT NULL,
    entity_type     VARCHAR(80) NOT NULL,
    entity_id       UUID,
    old_data        JSONB,
    new_data        JSONB,
    reason          TEXT,
    ip_address      VARCHAR(80),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ──────────────────────────────────────────────────────────────
-- 11. time_exceptions — Resoluciones WFM
-- ──────────────────────────────────────────────────────────────
CREATE TABLE time_exceptions (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id       UUID         NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    date              DATE         NOT NULL,
    exception_type    VARCHAR(20)  NOT NULL 
                        CHECK (exception_type IN ('leave_early', 'overtime', 'medical', 'manual_punch')),
    minutes_adjusted  INTEGER      DEFAULT 0,
    approved_by       UUID         REFERENCES employees(id) ON DELETE SET NULL,
    reason            TEXT,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE employee_profiles (
    employee_id            UUID PRIMARY KEY REFERENCES employees(id) ON DELETE CASCADE,
    document_type          VARCHAR(20),
    document_number        VARCHAR(30),
    birth_date             DATE,
    phone                  VARCHAR(40),
    email                  VARCHAR(120),
    address                VARCHAR(255),
    pension_system         VARCHAR(20) CHECK (pension_system IN ('AFP', 'ONP')),
    pension_provider       VARCHAR(80),
    health_regime          VARCHAR(80),
    bank_name              VARCHAR(80),
    bank_account_number    VARCHAR(80),
    bank_cci               VARCHAR(30),
    bank_validation_status VARCHAR(20) DEFAULT 'pending'
);

CREATE TABLE employment_contracts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id     UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    employer_id     UUID REFERENCES employers(id) ON DELETE SET NULL,
    contract_type   VARCHAR(60) NOT NULL,
    starts_on       DATE NOT NULL,
    ends_on         DATE,
    base_salary     NUMERIC(12,2),
    currency        VARCHAR(3) NOT NULL DEFAULT 'PEN',
    status          VARCHAR(20) NOT NULL DEFAULT 'active'
                        CHECK (status IN ('draft', 'active', 'ended', 'void')),
    termination_reason TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE employee_assignments (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id     UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    building_id     UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    manager_user_id UUID REFERENCES system_users(id) ON DELETE SET NULL,
    cost_center     VARCHAR(50),
    assignment_type VARCHAR(30) NOT NULL DEFAULT 'base'
                        CHECK (assignment_type IN ('base', 'temporary', 'coverage')),
    valid_from      DATE NOT NULL DEFAULT CURRENT_DATE,
    valid_to        DATE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE shift_templates (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    building_id     UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,
    starts_at       TIME NOT NULL,
    ends_at         TIME NOT NULL,
    is_overnight    BOOLEAN NOT NULL DEFAULT FALSE,
    role_name       VARCHAR(80),
    status          VARCHAR(20) NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'inactive')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE shift_instances (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id     UUID REFERENCES shift_templates(id) ON DELETE SET NULL,
    building_id     UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    employee_id     UUID REFERENCES employees(id) ON DELETE SET NULL,
    shift_date      DATE NOT NULL,
    starts_at       TIMESTAMPTZ NOT NULL,
    ends_at         TIMESTAMPTZ NOT NULL,
    status          VARCHAR(30) NOT NULL DEFAULT 'scheduled'
                        CHECK (status IN ('scheduled', 'covered', 'completed', 'missed', 'cancelled')),
    replacement_for UUID REFERENCES employees(id) ON DELETE SET NULL,
    created_by      UUID REFERENCES system_users(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE operational_movements (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id                 UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    origin_building_id          UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    destination_building_id     UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    starts_at                   TIMESTAMPTZ NOT NULL,
    ends_at                     TIMESTAMPTZ NOT NULL,
    movement_type               VARCHAR(40) NOT NULL,
    reason                      TEXT NOT NULL,
    requested_by                UUID REFERENCES system_users(id) ON DELETE SET NULL,
    approved_by                 UUID REFERENCES system_users(id) ON DELETE SET NULL,
    status                      VARCHAR(40) NOT NULL DEFAULT 'requested'
                                    CHECK (status IN ('requested', 'approved', 'rejected', 'executed', 'observed', 'pending_legal_validation', 'cancelled')),
    generates_overtime          BOOLEAN NOT NULL DEFAULT FALSE,
    generates_mobility          BOOLEAN NOT NULL DEFAULT FALSE,
    cost_allocation_rule        VARCHAR(40) NOT NULL DEFAULT 'destination_building'
                                    CHECK (cost_allocation_rule IN ('base_building', 'destination_building', 'worked_hours', 'worked_days', 'manual_approval', 'client_contract')),
    is_cross_employer           BOOLEAN NOT NULL DEFAULT FALSE,
    legal_validation_required   BOOLEAN NOT NULL DEFAULT FALSE,
    legal_note                  TEXT,
    evidence_url                TEXT,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE operational_incidents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id     UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    building_id     UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    incident_date   DATE NOT NULL,
    starts_at       TIMESTAMPTZ,
    ends_at         TIMESTAMPTZ,
    incident_type   VARCHAR(50) NOT NULL,
    status          VARCHAR(30) NOT NULL DEFAULT 'registered'
                        CHECK (status IN ('registered', 'pending_approval', 'approved', 'rejected', 'observed', 'annulled', 'included_in_prepayroll', 'included_in_closed_payroll')),
    is_paid         BOOLEAN,
    recovers_hours  BOOLEAN NOT NULL DEFAULT FALSE,
    affects_prepayroll BOOLEAN NOT NULL DEFAULT TRUE,
    affects_payroll BOOLEAN NOT NULL DEFAULT TRUE,
    reason          TEXT NOT NULL,
    evidence_url    TEXT,
    registered_by   UUID REFERENCES system_users(id) ON DELETE SET NULL,
    approved_by     UUID REFERENCES system_users(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE daily_building_reports (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    building_id     UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    report_date     DATE NOT NULL,
    administrator_user_id UUID REFERENCES system_users(id) ON DELETE SET NULL,
    status          VARCHAR(30) NOT NULL DEFAULT 'draft'
                        CHECK (status IN ('draft', 'submitted', 'observed', 'closed')),
    summary         JSONB NOT NULL DEFAULT '{}'::jsonb,
    observations    TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (building_id, report_date)
);

CREATE TABLE building_prepayrolls (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    building_id     UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    payroll_period_id UUID NOT NULL REFERENCES payroll_periods(id) ON DELETE CASCADE,
    administrator_user_id UUID REFERENCES system_users(id) ON DELETE SET NULL,
    state           VARCHAR(40) NOT NULL DEFAULT 'draft'
                        CHECK (state IN ('draft', 'admin_review', 'sent_to_hr', 'observed_by_hr', 'corrected_by_admin', 'approved_by_hr', 'consolidated', 'closed')),
    blocker_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    submitted_at    TIMESTAMPTZ,
    approved_at     TIMESTAMPTZ,
    consolidated_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (building_id, payroll_period_id)
);

CREATE TABLE building_prepayroll_items (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    building_prepayroll_id UUID NOT NULL REFERENCES building_prepayrolls(id) ON DELETE CASCADE,
    employee_id     UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    source_building_id UUID REFERENCES buildings(id) ON DELETE SET NULL,
    regular_minutes INTEGER NOT NULL DEFAULT 0,
    overtime_minutes INTEGER NOT NULL DEFAULT 0,
    deficit_minutes INTEGER NOT NULL DEFAULT 0,
    absences_count  INTEGER NOT NULL DEFAULT 0,
    late_count      INTEGER NOT NULL DEFAULT 0,
    permissions_count INTEGER NOT NULL DEFAULT 0,
    coverage_in_minutes INTEGER NOT NULL DEFAULT 0,
    coverage_out_minutes INTEGER NOT NULL DEFAULT 0,
    estimated_gross NUMERIC(12,2) NOT NULL DEFAULT 0,
    estimated_net   NUMERIC(12,2) NOT NULL DEFAULT 0,
    status          VARCHAR(30) NOT NULL DEFAULT 'draft',
    notes           TEXT
);

CREATE TABLE building_prepayroll_observations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    building_prepayroll_id UUID NOT NULL REFERENCES building_prepayrolls(id) ON DELETE CASCADE,
    reason_code     VARCHAR(60) NOT NULL,
    comment         TEXT NOT NULL,
    state           VARCHAR(30) NOT NULL DEFAULT 'open'
                        CHECK (state IN ('open', 'answered', 'closed')),
    observed_by     UUID REFERENCES system_users(id) ON DELETE SET NULL,
    answered_by     UUID REFERENCES system_users(id) ON DELETE SET NULL,
    answer          TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    answered_at     TIMESTAMPTZ
);

CREATE TABLE payroll_concepts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code            VARCHAR(30) NOT NULL UNIQUE,
    name            VARCHAR(120) NOT NULL,
    item_type       VARCHAR(30) NOT NULL
                        CHECK (item_type IN ('income', 'discount', 'worker_contribution', 'employer_contribution')),
    is_remunerative BOOLEAN NOT NULL DEFAULT TRUE,
    affects_afp_onp BOOLEAN NOT NULL DEFAULT FALSE,
    affects_essalud BOOLEAN NOT NULL DEFAULT FALSE,
    affects_fifth_tax BOOLEAN NOT NULL DEFAULT FALSE,
    affects_cts     BOOLEAN NOT NULL DEFAULT FALSE,
    affects_gratification BOOLEAN NOT NULL DEFAULT FALSE,
    affects_vacation BOOLEAN NOT NULL DEFAULT FALSE,
    affects_liquidation BOOLEAN NOT NULL DEFAULT FALSE,
    formula_key     VARCHAR(80) NOT NULL,
    legal_source    TEXT,
    valid_from      DATE NOT NULL DEFAULT CURRENT_DATE,
    valid_to        DATE,
    status          VARCHAR(20) NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE payroll_runs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payroll_period_id UUID NOT NULL REFERENCES payroll_periods(id) ON DELETE CASCADE,
    state           VARCHAR(40) NOT NULL DEFAULT 'draft'
                        CHECK (state IN ('draft', 'in_review', 'observed', 'hr_validated', 'finance_validated', 'closed', 'paid', 'reopened', 'void')),
    total_gross     NUMERIC(14,2) NOT NULL DEFAULT 0,
    total_discounts NUMERIC(14,2) NOT NULL DEFAULT 0,
    total_worker_contributions NUMERIC(14,2) NOT NULL DEFAULT 0,
    total_employer_contributions NUMERIC(14,2) NOT NULL DEFAULT 0,
    total_net       NUMERIC(14,2) NOT NULL DEFAULT 0,
    closed_at       TIMESTAMPTZ,
    closed_by       UUID REFERENCES system_users(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE payroll_items (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payroll_run_id  UUID NOT NULL REFERENCES payroll_runs(id) ON DELETE CASCADE,
    employee_id     UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    building_id     UUID REFERENCES buildings(id) ON DELETE SET NULL,
    concept_id      UUID REFERENCES payroll_concepts(id) ON DELETE SET NULL,
    item_type       VARCHAR(30) NOT NULL
                        CHECK (item_type IN ('income', 'discount', 'worker_contribution', 'employer_contribution')),
    quantity        NUMERIC(12,4) NOT NULL DEFAULT 1,
    amount          NUMERIC(12,2) NOT NULL,
    formula_key     VARCHAR(80),
    calculation_base JSONB NOT NULL DEFAULT '{}'::jsonb,
    explanation     TEXT
);

CREATE TABLE payroll_snapshots (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payroll_run_id  UUID NOT NULL REFERENCES payroll_runs(id) ON DELETE CASCADE,
    snapshot_data   JSONB NOT NULL,
    closure_hash    VARCHAR(128),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE building_cost_reports (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payroll_period_id UUID NOT NULL REFERENCES payroll_periods(id) ON DELETE CASCADE,
    building_id     UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    payroll_run_id  UUID REFERENCES payroll_runs(id) ON DELETE SET NULL,
    cost_center     VARCHAR(50),
    total_labor_cost NUMERIC(14,2) NOT NULL DEFAULT 0,
    total_regular_hours NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_overtime_hours NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_mobility  NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_coverages_received NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_coverages_sent NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_prorations NUMERIC(14,2) NOT NULL DEFAULT 0,
    observations    TEXT,
    state           VARCHAR(20) NOT NULL DEFAULT 'draft'
                        CHECK (state IN ('draft', 'generated', 'exported')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID REFERENCES system_users(id) ON DELETE SET NULL
);

CREATE TABLE payroll_payslips (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payroll_run_id  UUID NOT NULL REFERENCES payroll_runs(id) ON DELETE CASCADE,
    employee_id     UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    version         INTEGER NOT NULL DEFAULT 1,
    state           VARCHAR(30) NOT NULL DEFAULT 'generated'
                        CHECK (state IN ('generated', 'sent', 'replaced', 'void')),
    generated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sent_at         TIMESTAMPTZ,
    UNIQUE (payroll_run_id, employee_id, version)
);

CREATE TABLE salary_payment_batches (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payroll_run_id  UUID NOT NULL REFERENCES payroll_runs(id) ON DELETE CASCADE,
    state           VARCHAR(30) NOT NULL DEFAULT 'pending'
                        CHECK (state IN ('pending', 'prepared', 'sent_to_bank', 'observed', 'paid', 'partially_paid')),
    total_amount    NUMERIC(14,2) NOT NULL DEFAULT 0,
    prepared_by     UUID REFERENCES system_users(id) ON DELETE SET NULL,
    proof_url       TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    paid_at         TIMESTAMPTZ
);

CREATE TABLE salary_payment_items (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    salary_payment_batch_id UUID NOT NULL REFERENCES salary_payment_batches(id) ON DELETE CASCADE,
    employee_id     UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    bank_name       VARCHAR(80),
    bank_account_number VARCHAR(80),
    amount          NUMERIC(12,2) NOT NULL,
    state           VARCHAR(30) NOT NULL DEFAULT 'pending'
                        CHECK (state IN ('pending', 'observed', 'paid')),
    paid_at         TIMESTAMPTZ
);

-- ──────────────────────────────────────────────────────────────
-- Datos semilla para desarrollo
-- ──────────────────────────────────────────────────────────────

-- Roles
INSERT INTO roles (id, name) VALUES 
('00000000-0000-0000-0000-000000000001', 'Worker'),
('00000000-0000-0000-0000-000000000002', 'BuildingAdmin'),
('00000000-0000-0000-0000-000000000003', 'HRAdmin');

-- Empresa / Empleador base
INSERT INTO companies (id, business_name, ruc, fiscal_address)
VALUES ('c0c0c0c0-0000-0000-0000-000000000001', 'Administradora Demo SAC', '20111111111', 'Av. De los Heroes 123');

INSERT INTO employers (id, company_id, legal_name, ruc, employer_type)
VALUES (
    'd0d0d0d0-0000-0000-0000-000000000001',
    'c0c0c0c0-0000-0000-0000-000000000001',
    'Administradora Demo SAC',
    '20111111111',
    'administrator'
);

-- Buildings
INSERT INTO buildings (id, name, address) VALUES
('e0e0e0e0-0000-0000-0000-000000000001', 'Oficina Central', 'Av. De los Héroes 123'),
('e0e0e0e0-0000-0000-0000-000000000002', 'Almacén Norte', 'Parque Industrial Sur');

UPDATE buildings
   SET employer_id = 'd0d0d0d0-0000-0000-0000-000000000001',
       code = CASE
           WHEN id = 'e0e0e0e0-0000-0000-0000-000000000001' THEN 'EDI-CENTRAL'
           ELSE 'EDI-NORTE'
       END,
       district = 'Lima',
       managed_client_name = CASE
           WHEN id = 'e0e0e0e0-0000-0000-0000-000000000001' THEN 'Administradora Demo'
           ELSE 'Cliente Norte'
       END,
       cost_center = CASE
           WHEN id = 'e0e0e0e0-0000-0000-0000-000000000001' THEN 'CC-CENTRAL'
           ELSE 'CC-NORTE'
       END
 WHERE id IN (
       'e0e0e0e0-0000-0000-0000-000000000001',
       'e0e0e0e0-0000-0000-0000-000000000002'
 );

-- Employees
INSERT INTO employees (id, full_name, job_title, status, role_id, primary_building_id)
VALUES ('a1b2c3d4-0000-0000-0000-000000000001', 'Juan Pérez', 'Conserje', 'active', 
        '00000000-0000-0000-0000-000000000001', 'e0e0e0e0-0000-0000-0000-000000000001');

INSERT INTO employees (id, full_name, job_title, status, role_id, primary_building_id)
VALUES ('a1b2c3d4-0000-0000-0000-000000000002', 'Admin RRHH', 'Gerente de Compensaciones', 'active', 
        '00000000-0000-0000-0000-000000000003', 'e0e0e0e0-0000-0000-0000-000000000001');

-- Devices
INSERT INTO devices (id, token_hash, employee_id, building_id, alias)
VALUES (
    'b1b2c3d4-0000-0000-0000-000000000001',
    '8d5d7ce148c85f5433cf2d4f3d3d8ce0ba776bb28bf2be43d0debd0e5be21c8b',
    'a1b2c3d4-0000-0000-0000-000000000001',
    'e0e0e0e0-0000-0000-0000-000000000001',
    'Tablet de Juan'
);

-- Seed: Periodos iniciales
INSERT INTO payroll_periods (name, starts_on, ends_on, state)
VALUES 
('Abril 2026 - Q1', '2026-04-01', '2026-04-15', 'closed'),
('Abril 2026 - Q2', '2026-04-16', '2026-04-30', 'open')
ON CONFLICT DO NOTHING;
