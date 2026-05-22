from flask import Flask, request, jsonify, render_template, redirect, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = os.urandom(24)

# CONFIGURACIÓN DE LA BASE DE DATOS TFG_DAW
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'TFG_DAW'

mysql = MySQL(app)

# ==========================================
# RUTAS DE NAVEGACIÓN
# ==========================================

@app.route('/')
def index():
    if 'usuario_id' in session: 
        return redirect('/dashboard')
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'GET':
        return render_template('registro.html')
    
    nombre = request.form.get('usuario_form')
    email = request.form.get('email_form')
    password = request.form.get('pass_form')
    
    try:
        cur = mysql.connection.cursor()
        # Generación del Hash seguro antes de la inserción
        hashed_pw = generate_password_hash(password)
        cur.execute("INSERT INTO usuarios (nombreUsuario, email, password) VALUES (%s, %s, %s)", 
            (nombre, email, hashed_pw))
        session['usuario_id'] = cur.lastrowid
        session['nombreUsuario'] = nombre
        mysql.connection.commit()
        cur.close()
        return redirect('/dashboard')
    except Exception as e:
        return redirect('/registro')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email_form')
    password = request.form.get('pass_form')
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, nombreUsuario, password FROM usuarios WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()
    if user and check_password_hash(user[2], password):
        session['usuario_id'] = user[0]
        session['nombreUsuario'] = user[1]
        return redirect('/dashboard')
    return redirect('/')

@app.route('/dashboard')
def dashboard_vista():
    if 'usuario_id' not in session: 
        return redirect('/')
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ==========================================
# API DE DATOS (JSON PARA JAVASCRIPT)
# ==========================================

@app.route('/api/datos_dashboard', methods=['GET'])
def api_datos_dashboard():
    if 'usuario_id' not in session: 
        return jsonify({"error": "No autorizado"}), 401
        
    cur = mysql.connection.cursor()
    cur.execute("SELECT nombreUsuario, pct_fijo, pct_ocio, pct_ahorro FROM usuarios WHERE id = %s", (session['usuario_id'],))
    u_data = cur.fetchone()
    cur.execute("SELECT id, nombre, saldo FROM cuentas WHERE usuario_id = %s", (session['usuario_id'],))
    cuentas_db = cur.fetchall()
    cuentas = [{'id': c[0], 'nombre': c[1], 'saldo': float(c[2])} for c in cuentas_db]

    ahora = datetime.now()

    cur.execute("SELECT id, tipo, concepto, categoria, cantidad, fecha, cuenta_id FROM movimientos WHERE usuario_id = %s AND MONTH(fecha) = %s AND YEAR(fecha) = %s ORDER BY fecha DESC, id DESC", (session['usuario_id'], ahora.month, ahora.year))
    movimientos_db = cur.fetchall()
    cur.close()
    
    movimientos = []
    total_ingresos, gastado_fijo, gastado_ocio, gastado_ahorro = 0.0, 0.0, 0.0, 0.0
    for mov in movimientos_db:
        cant = float(mov[4])
        movimientos.append({
            'id': mov[0], 'tipo': mov[1], 'concepto': mov[2], 
            'categoria': mov[3], 'cantidad': cant, 'fecha': str(mov[5]), 'cuenta_id': mov[6]
        })
        if mov[1] == 'ingreso': total_ingresos += cant
        elif mov[1] == 'gasto':
            if mov[3] == 'fijo': gastado_fijo += cant
            elif mov[3] == 'ocio': gastado_ocio += cant
            elif mov[3] == 'ahorro_inversion': gastado_ahorro += cant

    pf = total_ingresos * (u_data[1] / 100)
    po = total_ingresos * (u_data[2] / 100)
    pa = total_ingresos * (u_data[3] / 100)
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    return jsonify({
        "usuario": {"nombre": u_data[0], "pct_fijo": u_data[1], "pct_ocio": u_data[2], "pct_ahorro": u_data[3]},
        "cuentas": cuentas,
        "movimientos": movimientos,
        "grafico_barras": {"presupuestado": [pf, po, pa], "gastado": [gastado_fijo, gastado_ocio, gastado_ahorro]},
        "mes_actual": meses[ahora.month - 1],
        "anio_actual": ahora.year
    })

@app.route('/api/crear_cuenta', methods=['POST'])
def crear_cuenta():
    data = request.json
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO cuentas (usuario_id, nombre, tipo, saldo) VALUES (%s, %s, %s, %s)", 
            (session['usuario_id'], data['nombre_cuenta'], data['tipo_cuenta'], data['saldo_inicial']))
    mysql.connection.commit()
    cur.close()
    return jsonify({"mensaje": "OK"})

@app.route('/api/crear_movimiento', methods=['POST'])
def crear_movimiento():
    data = request.json
    cur = mysql.connection.cursor()
    
    es_ahorro = (data['tipo_movimiento'] == 'gasto' and data['categoria'] == 'ahorro_inversion')
    
    if data['tipo_movimiento'] == 'gasto' and not es_ahorro:
        cur.execute("SELECT saldo FROM cuentas WHERE id = %s", (data['cuenta_id'],))
        saldo_actual = cur.fetchone()[0]
        if float(saldo_actual) < float(data['cantidad']): 
            return jsonify({"error": "Fondos insuficientes en la cuenta."}), 400
            
    cur.execute("INSERT INTO movimientos (usuario_id, cuenta_id, tipo, concepto, categoria, cantidad, fecha) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
            (session['usuario_id'], data['cuenta_id'], data['tipo_movimiento'], data['concepto'], data['categoria'], data['cantidad'], data['fecha']))
    
    if data['tipo_movimiento'] == 'ingreso' or es_ahorro: 
        cur.execute("UPDATE cuentas SET saldo = saldo + %s WHERE id = %s", (data['cantidad'], data['cuenta_id']))
    else: 
        cur.execute("UPDATE cuentas SET saldo = saldo - %s WHERE id = %s", (data['cantidad'], data['cuenta_id']))
        
    mysql.connection.commit()
    cur.close()
    return jsonify({"mensaje": "OK"})

@app.route('/api/eliminar_movimiento/<int:id>', methods=['DELETE'])
def eliminar_movimiento(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT tipo, cantidad, cuenta_id, categoria FROM movimientos WHERE id = %s AND usuario_id = %s", (id, session['usuario_id']))
    mov = cur.fetchone()
    
    if mov and mov[2] is not None:
        tipo, cantidad, cuenta_id, categoria = mov
        es_ahorro = (tipo == 'gasto' and categoria == 'ahorro_inversion')
        
        if tipo == 'ingreso' or es_ahorro: 
            cur.execute("UPDATE cuentas SET saldo = saldo - %s WHERE id = %s", (cantidad, cuenta_id))
        else: 
            cur.execute("UPDATE cuentas SET saldo = saldo + %s WHERE id = %s", (cantidad, cuenta_id))
            
    cur.execute("DELETE FROM movimientos WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({"mensaje": "OK"})

# ==========================================
# API EDITAR MOVIMIENTO
# ==========================================
@app.route('/api/editar_movimiento', methods=['POST'])
def editar_movimiento():
    if 'usuario_id' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    data = request.json
    mov_id = data.get('edit_movimiento_id')
    
    cur = mysql.connection.cursor()
    try:
        # 1. Recuperar info del movimiento antiguo
        cur.execute("SELECT tipo, cantidad, cuenta_id, categoria FROM movimientos WHERE id = %s AND usuario_id = %s", (mov_id, session['usuario_id']))
        old_mov = cur.fetchone()
        if not old_mov:
            return jsonify({"error": "Movimiento no encontrado"}), 404
            
        old_tipo, old_cantidad, old_cuenta_id, old_categoria = old_mov
        old_es_ahorro = (old_tipo == 'gasto' and old_categoria == 'ahorro_inversion')
        
        # 2. Deshacer el efecto del movimiento antiguo
        if old_tipo == 'ingreso' or old_es_ahorro:
            cur.execute("UPDATE cuentas SET saldo = saldo - %s WHERE id = %s", (old_cantidad, old_cuenta_id))
        else:
            cur.execute("UPDATE cuentas SET saldo = saldo + %s WHERE id = %s", (old_cantidad, old_cuenta_id))
            
        # 3. Leer los nuevos datos del formulario
        new_tipo = data['edit_tipo_movimiento']
        new_concepto = data['edit_concepto']
        new_categoria = data['edit_categoria']
        new_cantidad = float(data['edit_cantidad'])
        new_cuenta_id = data['edit_cuenta_id']
        new_fecha = data['edit_fecha']
        new_es_ahorro = (new_tipo == 'gasto' and new_categoria == 'ahorro_inversion')
        
        # 4. Comprobar si la cuenta nueva tiene fondos suficientes (solo si es gasto normal)
        if new_tipo == 'gasto' and not new_es_ahorro:
            cur.execute("SELECT saldo FROM cuentas WHERE id = %s", (new_cuenta_id,))
            saldo_actual = float(cur.fetchone()[0])
            if saldo_actual < new_cantidad:
                mysql.connection.rollback() # Deshace el paso 2
                return jsonify({"error": "Fondos insuficientes en la cuenta."}), 400
                
        # 5. Aplicar el efecto del nuevo movimiento
        if new_tipo == 'ingreso' or new_es_ahorro:
            cur.execute("UPDATE cuentas SET saldo = saldo + %s WHERE id = %s", (new_cantidad, new_cuenta_id))
        else:
            cur.execute("UPDATE cuentas SET saldo = saldo - %s WHERE id = %s", (new_cantidad, new_cuenta_id))
            
        # 6. Actualizar la base de datos
        cur.execute("""
            UPDATE movimientos 
            SET concepto = %s, categoria = %s, cantidad = %s, cuenta_id = %s, fecha = %s 
            WHERE id = %s AND usuario_id = %s
        """, (new_concepto, new_categoria, new_cantidad, new_cuenta_id, new_fecha, mov_id, session['usuario_id']))
        
        mysql.connection.commit()
        cur.close()
        return jsonify({"mensaje": "OK"})
    except Exception as e:
        mysql.connection.rollback()
        cur.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/ajustar_presupuesto', methods=['POST'])
def ajustar_presupuesto():
    if 'usuario_id' not in session:
        return jsonify({"error": "No autorizado"}), 401
    data = request.json
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE usuarios 
        SET pct_fijo = %s, pct_ocio = %s, pct_ahorro = %s 
        WHERE id = %s
    """, (data['pct_fijo'], data['pct_ocio'], data['pct_ahorro'], session['usuario_id']))
    mysql.connection.commit()
    cur.close()
    return jsonify({"mensaje": "OK"})

@app.route('/api/eliminar_cuenta', methods=['POST'])
def eliminar_cuenta():
    if 'usuario_id' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    data = request.json
    id_borrar = data.get('cuenta_id_borrar')
    id_destino = data.get('cuenta_id_destino')

    cur = mysql.connection.cursor()
    try:
        # Comprobación de propiedad y saldo
        cur.execute("SELECT saldo FROM cuentas WHERE id = %s AND usuario_id = %s", (id_borrar, session['usuario_id']))
        cuenta_info = cur.fetchone()
        if not cuenta_info:
            return jsonify({"error": "La cuenta no existe."}), 404
            
        saldo_a_traspasar = float(cuenta_info[0])

        # Traspaso obligatorio si hay fondos positivos
        if saldo_a_traspasar > 0:
            if not id_destino or str(id_borrar) == str(id_destino):
                return jsonify({"error": "Destino inválido."}), 400
            cur.execute("UPDATE cuentas SET saldo = saldo + %s WHERE id = %s", (saldo_a_traspasar, id_destino))
            
        # Borrado de la cuenta original
        cur.execute("DELETE FROM cuentas WHERE id = %s", (id_borrar,))
        
        # Confirmación de la transacción (Todo o Nada)
        mysql.connection.commit()
        cur.close()
        return jsonify({"mensaje": "OK"})

    except Exception as e:
        # Si algo falla (ej. caída de BD), se deshace el traspaso
        mysql.connection.rollback()
        cur.close()
        return jsonify({"error": "Error interno del servidor."}), 500
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)