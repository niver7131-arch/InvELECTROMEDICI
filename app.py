from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from functools import wraps
from datetime import datetime
import os

app = Flask(__name__)
# ⚠️ CAMBIO 1: Usar variable de entorno para la clave secreta
app.secret_key = os.environ.get('SECRET_KEY', 'cns_la_paz_secret_key_2024')

# ✅ CAMBIO 2: Configuración de BD desde variables de entorno (Render las provee)
def get_db():
    """Obtener conexión a la base de datos usando variables de entorno"""
    try:
        # Render proporciona DATABASE_URL automáticamente
        database_url = os.environ.get('DATABASE_URL')
        
        if database_url:
            # Usar la URL completa que da Render
            conn = psycopg2.connect(database_url, sslmode='require')
        else:
            # Fallback para desarrollo local
            conn = psycopg2.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                port=os.environ.get('DB_PORT', '5432'),
                database=os.environ.get('DB_NAME', 'inventario_cns'),
                user=os.environ.get('DB_USER', 'postgres'),
                password=os.environ.get('DB_PASSWORD', '123')
            )
        return conn
    except Exception as e:
        print(f"❌ Error conectando a BD: {e}")
        raise

def login_required(f):
    """Decorador para requerir login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicie sesión primero', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ✅ CAMBIO 3: Función simplificada para inicializar tablas (sin crear BD)
def init_database():
    """Crear tablas si no existen (usando BD existente)"""
    conn = None
    cursor = None
    try:
        print("🔧 Conectando a la base de datos...")
        conn = get_db()
        cursor = conn.cursor()
        print("✅ Conexión establecida, creando tablas si no existen...")
        
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
        print("✅ Tabla 'usuarios' verificada/creada")
        
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
        print("✅ Tabla 'equipos' verificada/creada")
        
        # Insertar usuario admin si no existe
        cursor.execute("SELECT * FROM usuarios WHERE username='admin'")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO usuarios (username, password, nombre_completo, rol)
                VALUES ('admin', 'admin123', 'Administrador CNS', 'admin')
            """)
            print("✅ Usuario admin creado")
        else:
            print("ℹ️ Usuario admin ya existe")
        
        # Insertar datos de ejemplo si no hay equipos
        cursor.execute("SELECT COUNT(*) FROM equipos")
        count = cursor.fetchone()[0]
        print(f"ℹ️ Equipos existentes: {count}")
        
        if count == 0:
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
        print("✅ Base de datos inicializada correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error inicializando tablas: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ============ INICIALIZAR BASE DE DATOS AL ARRANCAR LA APP ============
# 🔴 IMPORTANTE: Esto se ejecuta ANTES de que Gunicorn arranque
print("=" * 60)
print("🚀 SISTEMA DE INVENTARIO CNS - ELECTROMEDICINA")
print("🏥 Regional La Paz - Bolivia")
print("=" * 60)

# Verificar variables de entorno
print("📋 Verificando configuración:")
print(f"  - DATABASE_URL: {'✅ Configurada' if os.environ.get('DATABASE_URL') else '❌ No configurada'}")
print(f"  - SECRET_KEY: {'✅ Configurada' if os.environ.get('SECRET_KEY') else '⚠️ Usando valor por defecto'}")
print(f"  - PORT: {os.environ.get('PORT', '5000')}")

# Inicializar base de datos
print("\n📦 Inicializando tablas en la base de datos...")
init_database()

print("\n" + "=" * 60)
print("✨ SISTEMA LISTO PARA USAR")
print("=" * 60)
print("👤 Usuario: admin")
print("🔑 Contraseña: admin123")
print("=" * 60)

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
        
        try:
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
        except Exception as e:
            print(f"❌ Error en login: {e}")
            flash('Error al conectar con la base de datos', 'danger')
    
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
    try:
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
    except Exception as e:
        print(f"❌ Error obteniendo equipos: {e}")
        return jsonify({'error': str(e)}), 500

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
    try:
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
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {e}")
        return jsonify({'error': str(e)}), 500

# ============ CONFIGURACIÓN PARA DESARROLLO LOCAL ============
# Este bloque solo se ejecuta si ejecutas python app.py directamente
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)