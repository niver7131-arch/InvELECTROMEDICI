-- ==========================================
-- SISTEMA DE INVENTARIO CNS - ELECTROMEDICINA
-- Base de datos para Regional La Paz
-- Fecha de creación: 2026-05-10 17:15:11
-- ==========================================

-- Crear base de datos
-- CREATE DATABASE inventario_cns;

-- \c inventario_cns;

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    nombre_completo VARCHAR(100),
    rol VARCHAR(20) DEFAULT 'usuario',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de equipos de electromedicina
CREATE TABLE IF NOT EXISTS equipos (
    id_equipo SERIAL PRIMARY KEY,
    codigo_inventario VARCHAR(50) UNIQUE NOT NULL,
    nombre_equipo VARCHAR(100) NOT NULL,
    tipo_equipo VARCHAR(50),
    marca VARCHAR(50),
    modelo VARCHAR(50),
    numero_serie VARCHAR(50),
    estado VARCHAR(20) DEFAULT 'operativo',
    ubicacion VARCHAR(100),
    fecha_adquisicion DATE,
    ultimo_mantenimiento DATE,
    observaciones TEXT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Usuario administrador por defecto
INSERT INTO usuarios (username, password, nombre_completo, rol) 
VALUES ('admin', 'admin123', 'Administrador CNS', 'admin')
ON CONFLICT (username) DO NOTHING;

-- Equipos de ejemplo
INSERT INTO equipos (codigo_inventario, nombre_equipo, tipo_equipo, marca, modelo, numero_serie, estado, ubicacion) VALUES
('CNS-001', 'Monitor de Signos Vitales', 'Monitor', 'GE Healthcare', 'B650', 'SN001', 'operativo', 'Hospital La Paz'),
('CNS-002', 'Electrocardiógrafo', 'Diagnóstico', 'Philips', 'PageWriter TC30', 'SN002', 'mantenimiento', 'Centro Salud Sur'),
('CNS-003', 'Ventilador Mecánico', 'Soporte Vital', 'Draeger', 'Savina 300', 'SN003', 'operativo', 'UTI Hospital La Paz'),
('CNS-004', 'Desfibrilador', 'Emergencia', 'Zoll', 'R Series', 'SN004', 'operativo', 'Emergencias Hospital'),
('CNS-005', 'Bomba de Infusión', 'Administración', 'Braun', 'Perfusor Space', 'SN005', 'operativo', 'Pabellón Central'),
('CNS-006', 'Electrocardiógrafo Digital', 'Diagnóstico', 'Mindray', 'BeneHeart R12', 'SN006', 'reparación', 'Mantenimiento'),
('CNS-007', 'Monitor Neonatal', 'Monitor', 'Philips', 'IntelliVue X3', 'SN007', 'operativo', 'Neonatología'),
('CNS-008', 'Electrocauterio', 'Quirúrgico', 'Valleylab', 'Force FX', 'SN008', 'operativo', 'Quirófano 1')
ON CONFLICT (codigo_inventario) DO NOTHING;

-- Índices para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_equipos_codigo ON equipos(codigo_inventario);
CREATE INDEX IF NOT EXISTS idx_equipos_estado ON equipos(estado);
CREATE INDEX IF NOT EXISTS idx_equipos_ubicacion ON equipos(ubicacion);

-- Mostrar resumen
SELECT 'Base de datos inicializada correctamente' as Mensaje;
