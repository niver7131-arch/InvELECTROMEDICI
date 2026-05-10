from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from functools import wraps
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'cns_la_paz_secret_key_2024'

# Configuración de base de datos
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'inventario_cns',
    'user': 'postgres',
    'password': '123'
}

def get_db():
    """Obtener conexión a la base de datos"""
    return psycopg2.connect(**DB_CONFIG)

def login_required(f):
    """Decorador para requerir login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicie sesión primero', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ============ CREAR CARPETA DATABASE Y ARCHIVO SQL ============
def crear_carpeta_database():
    """Crear carpeta database y archivo init.sql automáticamente"""
    if not os.path.exists('database'):
        os.makedirs('database')
        print("📁 Carpeta 'database' creada")
        
        # Crear archivo init.sql
        sql_content = """-- ==========================================
-- SISTEMA DE INVENTARIO CNS - ELECTROMEDICINA
-- Base de datos para Regional La Paz
-- Fecha de creación: {}
-- ==========================================

-- Crear base de datos
-- CREATE DATABASE inventario_cns;

-- \\c inventario_cns;

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
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        with open('database/init.sql', 'w', encoding='utf-8') as f:
            f.write(sql_content)
        print("📄 Archivo 'database/init.sql' creado")
        print("💡 Puedes ejecutar este SQL en pgAdmin si necesitas recrear la BD")

# ============ INICIALIZAR BASE DE DATOS ============
def init_database():
    """Crear base de datos y tablas si no existen"""
    try:
        # Conectar a PostgreSQL sin base específica
        conn_admin = psycopg2.connect(
            host='localhost',
            port='5432',
            user='postgres',
            password='123'
        )
        conn_admin.autocommit = True
        cursor_admin = conn_admin.cursor()
        
        # Crear base de datos si no existe
        cursor_admin.execute("SELECT 1 FROM pg_database WHERE datname='inventario_cns'")
        if not cursor_admin.fetchone():
            cursor_admin.execute("CREATE DATABASE inventario_cns")
            print("✅ Base de datos 'inventario_cns' creada")
        else:
            print("ℹ️ Base de datos 'inventario_cns' ya existe")
        
        cursor_admin.close()
        conn_admin.close()
        
        # Conectar a la base de datos específica
        conn = get_db()
        cursor = conn.cursor()
        
        # Crear tabla de usuarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id_usuario SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                nombre_completo VARCHAR(100),
                rol VARCHAR(20) DEFAULT 'usuario',
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Tabla 'usuarios' lista")
        
        # Crear tabla de equipos
        cursor.execute("""
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
            )
        """)
        print("✅ Tabla 'equipos' lista")
        
        # Insertar usuario admin si no existe
        cursor.execute("SELECT * FROM usuarios WHERE username='admin'")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO usuarios (username, password, nombre_completo, rol)
                VALUES ('admin', 'admin123', 'Administrador CNS', 'admin')
            """)
            print("✅ Usuario 'admin' creado")
        
        # Insertar datos de ejemplo si no hay equipos
        cursor.execute("SELECT COUNT(*) FROM equipos")
        if cursor.fetchone()[0] == 0:
            equipos_ejemplo = [
                ('CNS-001', 'Monitor de Signos Vitales', 'Monitor', 'GE Healthcare', 
                 'B650', 'SN001', 'operativo', 'Hospital La Paz'),
                ('CNS-002', 'Electrocardiógrafo', 'Diagnóstico', 'Philips', 
                 'PageWriter TC30', 'SN002', 'mantenimiento', 'Centro Salud Sur'),
                ('CNS-003', 'Ventilador Mecánico', 'Soporte Vital', 'Draeger', 
                 'Savina 300', 'SN003', 'operativo', 'UTI Hospital La Paz'),
                ('CNS-004', 'Desfibrilador', 'Emergencia', 'Zoll', 
                 'R Series', 'SN004', 'operativo', 'Emergencias Hospital'),
                ('CNS-005', 'Bomba de Infusión', 'Administración', 'Braun', 
                 'Perfusor Space', 'SN005', 'operativo', 'Pabellón Central'),
                ('CNS-006', 'Ultrasonido', 'Diagnóstico', 'Mindray', 
                 'DC-70', 'SN006', 'operativo', 'Radiología'),
            ]
            
            for eq in equipos_ejemplo:
                cursor.execute("""
                    INSERT INTO equipos (codigo_inventario, nombre_equipo, tipo_equipo, 
                                       marca, modelo, numero_serie, estado, ubicacion)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, eq)
            print(f"✅ {len(equipos_ejemplo)} equipos de ejemplo creados")
        
        # Crear índices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_equipos_codigo ON equipos(codigo_inventario)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_equipos_estado ON equipos(estado)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_equipos_ubicacion ON equipos(ubicacion)")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("🎉 Base de datos inicializada correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
        print("\n⚠️ SOLUCIÓN RÁPIDA:")
        print("1. Asegúrate que PostgreSQL esté instalado")
        print("2. Verifica que PostgreSQL esté corriendo:")
        print("   - Windows: net start postgresql-15")
        print("   - Linux: sudo systemctl start postgresql")
        print("3. Asegúrate que la contraseña de PostgreSQL es '123'")
        print("   Si no es así, cambia la contraseña o edita DB_CONFIG en app.py")
        return False

# ============ RUTAS PRINCIPALES ============

@app.route('/')
def index():
    """Redirigir a login o dashboard"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT * FROM usuarios WHERE username = %s AND password = %s",
            (username, password)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            session['user_id'] = user['id_usuario']
            session['username'] = user['username']
            session['nombre'] = user['nombre_completo']
            flash(f'¡Bienvenido {session["nombre"] or session["username"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Cerrar sesión"""
    session.clear()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal con inventario"""
    return render_template('index.html', username=session.get('username'))

# ============ API PARA EQUIPOS ============

@app.route('/api/equipos')
@login_required
def get_equipos():
    """Obtener todos los equipos (JSON)"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT id_equipo, codigo_inventario, nombre_equipo, tipo_equipo, 
               marca, modelo, numero_serie, estado, ubicacion, 
               ultimo_mantenimiento, observaciones
        FROM equipos ORDER BY id_equipo DESC
    """)
    equipos = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Formatear fechas
    for equipo in equipos:
        if equipo['ultimo_mantenimiento']:
            equipo['ultimo_mantenimiento'] = equipo['ultimo_mantenimiento'].strftime('%Y-%m-%d')
    
    return jsonify(equipos)

@app.route('/api/equipos', methods=['POST'])
@login_required
def add_equipo():
    """Agregar nuevo equipo"""
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO equipos (codigo_inventario, nombre_equipo, tipo_equipo, marca, 
                               modelo, numero_serie, estado, ubicacion, ultimo_mantenimiento, observaciones)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['codigo_inventario'], data['nombre_equipo'], data.get('tipo_equipo', ''),
            data.get('marca', ''), data.get('modelo', ''), data.get('numero_serie', ''),
            data.get('estado', 'operativo'), data.get('ubicacion', ''),
            data.get('ultimo_mantenimiento') or None, data.get('observaciones', '')
        ))
        conn.commit()
        return jsonify({'success': True, 'message': 'Equipo agregado correctamente'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/equipos/<int:id>', methods=['PUT'])
@login_required
def update_equipo(id):
    """Actualizar equipo existente"""
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE equipos SET 
                codigo_inventario = %s, nombre_equipo = %s, tipo_equipo = %s,
                marca = %s, modelo = %s, numero_serie = %s, estado = %s,
                ubicacion = %s, ultimo_mantenimiento = %s, observaciones = %s
            WHERE id_equipo = %s
        """, (
            data['codigo_inventario'], data['nombre_equipo'], data.get('tipo_equipo', ''),
            data.get('marca', ''), data.get('modelo', ''), data.get('numero_serie', ''),
            data.get('estado', 'operativo'), data.get('ubicacion', ''),
            data.get('ultimo_mantenimiento') or None, data.get('observaciones', ''),
            id
        ))
        conn.commit()
        return jsonify({'success': True, 'message': 'Equipo actualizado correctamente'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/equipos/<int:id>', methods=['DELETE'])
@login_required
def delete_equipo(id):
    """Eliminar equipo"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM equipos WHERE id_equipo = %s", (id,))
        conn.commit()
        return jsonify({'success': True, 'message': 'Equipo eliminado'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/estadisticas')
@login_required
def get_estadisticas():
    """Obtener estadísticas del inventario"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM equipos")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM equipos WHERE estado = 'operativo'")
    operativos = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM equipos WHERE estado = 'mantenimiento'")
    mantenimiento = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM equipos WHERE estado = 'dañado'")
    danados = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM equipos WHERE estado = 'reparación'")
    reparacion = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'total': total,
        'operativos': operativos,
        'mantenimiento': mantenimiento,
        'danados': danados,
        'reparacion': reparacion
    })

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 SISTEMA DE INVENTARIO CNS - ELECTROMEDICINA")
    print("🏥 Regional La Paz - Bolivia")
    print("=" * 60)
    
    # Crear carpeta database automáticamente
    crear_carpeta_database()
    
    print("\n📦 Inicializando base de datos...")
    if init_database():
        print("\n" + "=" * 60)
        print("✨ SISTEMA LISTO PARA USAR")
        print("=" * 60)
        print("🔗 Abre en tu navegador: http://localhost:5000")
        print("👤 Usuario: admin")
        print("🔑 Contraseña: admin123")
        print("=" * 60)
        print("\n💾 Respaldo de BD guardado en: database/init.sql")
        print("📁 Carpeta 'database' creada automáticamente")
        print("\n✅ Presiona CTRL+C para detener el servidor\n")
        
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("\n❌ No se pudo iniciar el sistema. Verifica PostgreSQL.")