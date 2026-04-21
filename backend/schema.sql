-- ============================================================
-- Asistencia App — PostgreSQL Schema (V2 - WFM Expansion)
-- ============================================================

-- Extensión para UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Limpieza preventiva
DROP TABLE IF EXISTS time_exceptions CASCADE;
DROP TABLE IF EXISTS attendance_logs CASCADE;
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
-- 2. roles — Niveles de acceso/permisos
-- ──────────────────────────────────────────────────────────────
CREATE TABLE roles (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(50) NOT NULL UNIQUE -- 'worker', 'building_admin', 'hr_admin'
);

-- ──────────────────────────────────────────────────────────────
-- 3. employees — Catálogo de empleados
-- ──────────────────────────────────────────────────────────────
CREATE TABLE employees (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name           VARCHAR(150) NOT NULL,
    status              VARCHAR(20)  NOT NULL DEFAULT 'active'
                            CHECK (status IN ('active', 'inactive', 'suspended')),
    role_id             UUID         NOT NULL REFERENCES roles(id),
    primary_building_id UUID         REFERENCES buildings(id) ON DELETE SET NULL,
    face_id_aws         VARCHAR(255),
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ──────────────────────────────────────────────────────────────
-- 4. devices — Dispositivos vinculados a empleados
-- ──────────────────────────────────────────────────────────────
CREATE TABLE devices (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_token    VARCHAR(255) NOT NULL UNIQUE,
    employee_id     UUID         NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    alias           VARCHAR(100),
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_devices_token ON devices (device_token);

-- ──────────────────────────────────────────────────────────────
-- 5. schedules — Horarios semanales asignados
-- ──────────────────────────────────────────────────────────────
CREATE TABLE schedules (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id     UUID         NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    building_id     UUID         REFERENCES buildings(id) ON DELETE SET NULL,
    day_of_week     SMALLINT     NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    start_time      TIME         NOT NULL,
    end_time        TIME         NOT NULL,
    UNIQUE (employee_id, day_of_week)
);

-- ──────────────────────────────────────────────────────────────
-- 6. attendance_logs — Registros de asistencia
-- ──────────────────────────────────────────────────────────────
CREATE TABLE attendance_logs (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id       UUID         NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    device_id         UUID         NOT NULL REFERENCES devices(id)   ON DELETE SET NULL,
    building_id       UUID         REFERENCES buildings(id) ON DELETE SET NULL,
    action_type       VARCHAR(10)  NOT NULL CHECK (action_type IN ('check_in', 'check_out')),
    timestamp         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    is_manual_override BOOLEAN     NOT NULL DEFAULT FALSE,
    photo_s3_key      VARCHAR(512),
    confidence_score  NUMERIC(5,2),
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_attendance_employee  ON attendance_logs (employee_id);
CREATE INDEX idx_attendance_timestamp ON attendance_logs (timestamp);

-- ──────────────────────────────────────────────────────────────
-- 7. time_exceptions — Excepciones (permisos, horas extra, etc.)
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
('00000000-0000-0000-0000-000000000001', 'worker'),
('00000000-0000-0000-0000-000000000002', 'building_admin'),
('00000000-0000-0000-0000-000000000003', 'hr_admin');

-- Buildings
INSERT INTO buildings (id, name, address) VALUES
('e0e0e0e0-0000-0000-0000-000000000001', 'Oficina Central', 'Av. De los Héroes 123'),
('e0e0e0e0-0000-0000-0000-000000000002', 'Almacén Norte', 'Parque Industrial Sur');

-- Employees
-- Juan Pérez (Worker)
INSERT INTO employees (id, full_name, status, role_id, primary_building_id)
VALUES ('a1b2c3d4-0000-0000-0000-000000000001', 'Juan Pérez', 'active', 
        '00000000-0000-0000-0000-000000000001', 'e0e0e0e0-0000-0000-0000-000000000001');

-- Admin RRHH
INSERT INTO employees (id, full_name, status, role_id, primary_building_id)
VALUES ('a1b2c3d4-0000-0000-0000-000000000002', 'Admin RRHH', 'active', 
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
INSERT INTO schedules (employee_id, building_id, day_of_week, start_time, end_time)
VALUES
    ('a1b2c3d4-0000-0000-0000-000000000001', 'e0e0e0e0-0000-0000-0000-000000000001', 0, '08:00', '17:00'),
    ('a1b2c3d4-0000-0000-0000-000000000001', 'e0e0e0e0-0000-0000-0000-000000000001', 1, '08:00', '17:00'),
    ('a1b2c3d4-0000-0000-0000-000000000001', 'e0e0e0e0-0000-0000-0000-000000000001', 2, '08:00', '17:00'),
    ('a1b2c3d4-0000-0000-0000-000000000001', 'e0e0e0e0-0000-0000-0000-000000000001', 3, '08:00', '17:00'),
    ('a1b2c3d4-0000-0000-0000-000000000001', 'e0e0e0e0-0000-0000-0000-000000000001', 4, '08:00', '17:00');

-- Time Exception
INSERT INTO time_exceptions (employee_id, date, exception_type, minutes_adjusted, approved_by, reason)
VALUES ('a1b2c3d4-0000-0000-0000-000000000001', CURRENT_DATE, 'medical', 0, 
        'a1b2c3d4-0000-0000-0000-000000000002', 'Cita odontológica');
