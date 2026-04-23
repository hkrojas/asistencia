-- ============================================================
-- Asistencia App — PostgreSQL Schema (V3 - WFM Core Domain)
-- ============================================================

-- Extensión para UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Limpieza preventiva
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS daily_timesheets CASCADE;
DROP TABLE IF EXISTS time_exceptions CASCADE;
DROP TABLE IF EXISTS raw_punches CASCADE;
DROP TABLE IF EXISTS attendance_logs CASCADE; -- Deprecated
DROP TABLE IF EXISTS schedules CASCADE;
DROP TABLE IF EXISTS devices CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS roles CASCADE;
DROP TABLE IF EXISTS buildings CASCADE;

-- ──────────────────────────────────────────────────────────────
-- 1. buildings — Sedes o establecimientos
-- ──────────────────────────────────────────────────────────────
CREATE TABLE buildings (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(100) NOT NULL,
    address         VARCHAR(255),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
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
    device_token    VARCHAR(255) NOT NULL UNIQUE,
    employee_id     UUID         NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    alias           VARCHAR(100),
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ──────────────────────────────────────────────────────────────
-- 5. schedules — Horarios Planificados
-- ──────────────────────────────────────────────────────────────
CREATE TABLE schedules (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id         UUID         NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    building_id         UUID         REFERENCES buildings(id) ON DELETE SET NULL,
    day_of_week         SMALLINT     NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    start_time          TIME         NOT NULL,
    end_time            TIME         NOT NULL,
    is_overnight        BOOLEAN      NOT NULL DEFAULT FALSE,
    tolerance_minutes   INTEGER      NOT NULL DEFAULT 15,
    UNIQUE (employee_id, day_of_week)
);

-- ──────────────────────────────────────────────────────────────
-- 6. raw_punches — Eventos de Marcación (Inmutable)
-- ──────────────────────────────────────────────────────────────
CREATE TABLE raw_punches (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id         UUID         REFERENCES devices(id) ON DELETE SET NULL,
    employee_id       UUID         NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    punch_time        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    punch_type        VARCHAR(10)  NOT NULL CHECK (punch_type IN ('in', 'out')),
    confidence_score  NUMERIC(5,2),
    offline_sync      BOOLEAN      NOT NULL DEFAULT FALSE,
    client_uuid       UUID         UNIQUE, -- Idempotencia desde el cliente
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_punches_employee ON raw_punches (employee_id);
CREATE INDEX idx_punches_time     ON raw_punches (punch_time);

-- ──────────────────────────────────────────────────────────────
-- 7. daily_timesheets — Jornadas Interpretadas
-- ──────────────────────────────────────────────────────────────
CREATE TYPE timesheet_status AS ENUM ('incomplete', 'perfect', 'exception', 'resolved');

CREATE TABLE daily_timesheets (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id       UUID         NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    logical_date      DATE         NOT NULL,
    schedule_id       UUID         REFERENCES schedules(id) ON DELETE SET NULL,
    first_punch_in    TIMESTAMPTZ,
    last_punch_out    TIMESTAMPTZ,
    regular_minutes   INTEGER      DEFAULT 0,
    overtime_minutes  INTEGER      DEFAULT 0,
    deficit_minutes   INTEGER      DEFAULT 0,
    status            timesheet_status NOT NULL DEFAULT 'incomplete',
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
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
-- 9. time_exceptions — Resoluciones WFM
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

-- ──────────────────────────────────────────────────────────────
-- Datos semilla para desarrollo
-- ──────────────────────────────────────────────────────────────

-- Roles
INSERT INTO roles (id, name) VALUES 
('00000000-0000-0000-0000-000000000001', 'Worker'),
('00000000-0000-0000-0000-000000000002', 'BuildingAdmin'),
('00000000-0000-0000-0000-000000000003', 'HRAdmin');

-- Buildings
INSERT INTO buildings (id, name, address) VALUES
('e0e0e0e0-0000-0000-0000-000000000001', 'Oficina Central', 'Av. De los Héroes 123'),
('e0e0e0e0-0000-0000-0000-000000000002', 'Almacén Norte', 'Parque Industrial Sur');

-- Employees
INSERT INTO employees (id, full_name, job_title, status, role_id, primary_building_id)
VALUES ('a1b2c3d4-0000-0000-0000-000000000001', 'Juan Pérez', 'Conserje', 'active', 
        '00000000-0000-0000-0000-000000000001', 'e0e0e0e0-0000-0000-0000-000000000001');

INSERT INTO employees (id, full_name, job_title, status, role_id, primary_building_id)
VALUES ('a1b2c3d4-0000-0000-0000-000000000002', 'Admin RRHH', 'Gerente de Compensaciones', 'active', 
        '00000000-0000-0000-0000-000000000003', 'e0e0e0e0-0000-0000-0000-000000000001');

-- Devices
INSERT INTO devices (id, device_token, employee_id, alias)
VALUES (
    'b1b2c3d4-0000-0000-0000-000000000001',
    'token-simulado-juan-perez',
    'a1b2c3d4-0000-0000-0000-000000000001',
    'Tablet de Juan'
);

-- Schedules
INSERT INTO schedules (id, employee_id, building_id, day_of_week, start_time, end_time)
VALUES
    ('c0e0e0e0-0000-0000-0000-000000000001', 'a1b2c3d4-0000-0000-0000-000000000001', 'e0e0e0e0-0000-0000-0000-000000000001', 0, '08:00', '17:00'),
    ('c0e0e0e0-0000-0000-0000-000000000002', 'a1b2c3d4-0000-0000-0000-000000000001', 'e0e0e0e0-0000-0000-0000-000000000001', 1, '08:00', '17:00'),
    ('c0e0e0e0-0000-0000-0000-000000000003', 'a1b2c3d4-0000-0000-0000-000000000001', 'e0e0e0e0-0000-0000-0000-000000000001', 2, '08:00', '17:00'),
    ('c0e0e0e0-0000-0000-0000-000000000004', 'a1b2c3d4-0000-0000-0000-000000000001', 'e0e0e0e0-0000-0000-0000-000000000001', 3, '08:00', '17:00'),
    ('c0e0e0e0-0000-0000-0000-000000000005', 'a1b2c3d4-0000-0000-0000-000000000001', 'e0e0e0e0-0000-0000-0000-000000000001', 4, '08:00', '17:00');

-- ──────────────────────────────────────────────────────────────
-- 10. payroll_periods — Ciclos de Nómina y Bloqueo
-- ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS payroll_periods (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(100) NOT NULL,
    starts_on   DATE NOT NULL,
    ends_on     DATE NOT NULL,
    state       VARCHAR(20) DEFAULT 'open' CHECK (state IN ('open', 'closed')),
    closed_at   TIMESTAMPTZ,
    closed_by   UUID REFERENCES system_users(id),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Actualización de tablas existentes para soportar bloqueo
ALTER TABLE daily_timesheets ADD COLUMN IF NOT EXISTS payroll_period_id UUID REFERENCES payroll_periods(id);
ALTER TABLE daily_timesheets ADD COLUMN IF NOT EXISTS is_locked BOOLEAN DEFAULT FALSE;
ALTER TABLE raw_punches ADD COLUMN IF NOT EXISTS ingest_status VARCHAR(20) DEFAULT 'accepted' CHECK (ingest_status IN ('accepted', 'late_pending_review', 'rejected'));

-- Phase 26: Autenticación y Usuarios de Sistema
CREATE TABLE IF NOT EXISTS system_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Seed: admin / Hernandez2026
INSERT INTO system_users (username, password_hash)
VALUES ('admin', 'scrypt:32768:8:1$nPnHMCE4QJlQRPuD$5f3f2e7e70ac807947665f41d89e52223e1fb6cf8b650ac66be4a3d48b9d552993b1cf9917a03f29824eb09bb1c3301d7e22e3f3dab110296fa6e442d780ed6f')
ON CONFLICT (username) DO NOTHING;

-- Seed: Periodos iniciales
INSERT INTO payroll_periods (name, starts_on, ends_on, state)
VALUES 
('Abril 2026 - Q1', '2026-04-01', '2026-04-15', 'closed'),
('Abril 2026 - Q2', '2026-04-16', '2026-04-30', 'open')
ON CONFLICT DO NOTHING;
