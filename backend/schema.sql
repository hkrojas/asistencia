-- ============================================================
-- Asistencia App — PostgreSQL Schema
-- ============================================================

-- Extensión para UUIDs (se habilita una sola vez por base de datos)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ──────────────────────────────────────────────────────────────
-- 1. employees — Catálogo de empleados
-- ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS employees (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name       VARCHAR(150) NOT NULL,
    status          VARCHAR(20)  NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'inactive', 'suspended')),
    face_id_aws     VARCHAR(255),          -- ID de rostro en AWS Rekognition (futuro)
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ──────────────────────────────────────────────────────────────
-- 2. devices — Dispositivos vinculados a empleados
-- ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS devices (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_token    VARCHAR(255) NOT NULL UNIQUE,
    employee_id     UUID         NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    alias           VARCHAR(100),          -- Nombre descriptivo del equipo
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_devices_token ON devices (device_token);

-- ──────────────────────────────────────────────────────────────
-- 3. schedules — Horarios semanales asignados
-- ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS schedules (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id     UUID         NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    day_of_week     SMALLINT     NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
                                           -- 0 = Lunes … 6 = Domingo
    start_time      TIME         NOT NULL,
    end_time        TIME         NOT NULL,
    UNIQUE (employee_id, day_of_week)
);

-- ──────────────────────────────────────────────────────────────
-- 4. attendance_logs — Registros de asistencia
-- ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS attendance_logs (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id       UUID         NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    device_id         UUID         NOT NULL REFERENCES devices(id)   ON DELETE SET NULL,
    action_type       VARCHAR(10)  NOT NULL CHECK (action_type IN ('check_in', 'check_out')),
    timestamp         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    photo_s3_key      VARCHAR(512),        -- Ruta de la foto en S3 (futuro)
    confidence_score  NUMERIC(5,2),        -- Porcentaje de confianza de Rekognition (futuro)
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_attendance_employee  ON attendance_logs (employee_id);
CREATE INDEX IF NOT EXISTS idx_attendance_timestamp ON attendance_logs (timestamp);

-- ──────────────────────────────────────────────────────────────
-- Datos semilla para desarrollo
-- ──────────────────────────────────────────────────────────────
INSERT INTO employees (id, full_name, status)
VALUES ('a1b2c3d4-0000-0000-0000-000000000001', 'Juan Pérez', 'active')
ON CONFLICT (id) DO NOTHING;

INSERT INTO devices (id, device_token, employee_id, alias)
VALUES (
    'b1b2c3d4-0000-0000-0000-000000000001',
    'token-simulado-juan-perez',
    'a1b2c3d4-0000-0000-0000-000000000001',
    'Tablet Entrada Principal'
)
ON CONFLICT (device_token) DO NOTHING;

-- Horario de lunes a viernes 08:00–17:00
INSERT INTO schedules (employee_id, day_of_week, start_time, end_time)
VALUES
    ('a1b2c3d4-0000-0000-0000-000000000001', 0, '08:00', '17:00'),
    ('a1b2c3d4-0000-0000-0000-000000000001', 1, '08:00', '17:00'),
    ('a1b2c3d4-0000-0000-0000-000000000001', 2, '08:00', '17:00'),
    ('a1b2c3d4-0000-0000-0000-000000000001', 3, '08:00', '17:00'),
    ('a1b2c3d4-0000-0000-0000-000000000001', 4, '08:00', '17:00')
ON CONFLICT (employee_id, day_of_week) DO NOTHING;
