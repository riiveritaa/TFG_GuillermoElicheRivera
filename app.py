from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = os.urandom(24)

# Configuración conexión MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'TFG'

mysql = MySQL(app)

@app.route('/')
def index():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/registro', methods=['GET'])
def pagina_registro():
    return render_template('registro.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email_form')
    password = request.form.get('pass_form')

    if not email or not password:
        return jsonify({"mensaje": "Por favor, completa todos los campos"}), 400

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, nombreUsuario, email, password FROM usuarios WHERE email = %s", (email,))
    usuario = cur.fetchone()
    cur.close()

    if usuario and check_password_hash(usuario[3], password):
        session['usuario_id'] = usuario[0]
        # No pasamos el nombre aquí, lo leeremos en la ruta dashboard
        return redirect(url_for('dashboard'))
    else:
        return jsonify({"mensaje": "Email o contraseña incorrectos"}), 401

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/registro', methods=['POST'])
def registro():
    nombre = request.form.get('usuario_form')
    email = request.form.get('email_form')
    password = request.form.get('pass_form')

    if not nombre or not email or not password:
        return jsonify({"mensaje": "Faltan campos obligatorios"}), 400

    password_hash = generate_password_hash(password)

    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO usuarios (nombreUsuario, email, password) VALUES (%s, %s, %s)",
            (nombre, email, password_hash)
        )
        mysql.connection.commit()
        cur.close()
        return jsonify({"mensaje": "Usuario registrado correctamente"})

    except Exception as e:
        return jsonify({"mensaje": "Error al registrar usuario", "error": str(e)}), 500 
    
@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
    
    # 1. Obtenemos los datos ACTUALIZADOS del usuario, incluyendo porcentajes
    cur = mysql.connection.cursor()
    cur.execute("SELECT nombreUsuario, pct_fijo, pct_ocio, pct_ahorro FROM usuarios WHERE id = %s", (session['usuario_id'],))
    datos_usuario = cur.fetchone()
    cur.close()

    # 2. Se los enviamos al HTML
    return render_template('dashboard.html', 
    nombre=datos_usuario[0],
    pct_fijo=datos_usuario[1],
    pct_ocio=datos_usuario[2],
    pct_ahorro=datos_usuario[3])

@app.route('/configurar_porcentajes', methods=['POST'])
def configurar_porcentajes():
    if 'usuario_id' not in session:
        return jsonify({"mensaje": "No autorizado"}), 401

    data = request.json
    fijo = data.get('pct_fijo')
    ocio = data.get('pct_ocio')
    ahorro = data.get('pct_ahorro')

    # Validación en el backend por si acaso intentan hackear el JS
    if (fijo + ocio + ahorro) != 100:
        return jsonify({"mensaje": "Los porcentajes deben sumar exactamente 100%"}), 400

    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "UPDATE usuarios SET pct_fijo = %s, pct_ocio = %s, pct_ahorro = %s WHERE id = %s",
            (fijo, ocio, ahorro, session['usuario_id'])
        )
        mysql.connection.commit()
        cur.close()
        return jsonify({"mensaje": "Porcentajes actualizados correctamente"})
    except Exception as e:
        return jsonify({"mensaje": "Error al actualizar porcentajes", "error": str(e)}), 500

@app.route('/movimiento', methods=['POST'])
def crear_movimiento():
    if 'usuario_id' not in session:
        return jsonify({"mensaje": "No autorizado"}), 401

    data = request.json
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO movimientos (usuario_id, tipo, concepto, categoria, cantidad, fecha) VALUES (%s, %s, %s, %s, %s, %s)",
            (session['usuario_id'], data['tipo'], data['concepto'], data['categoria'], data['cantidad'], data['fecha'])
        )
        mysql.connection.commit()
        cur.close()
        return jsonify({"mensaje": "Movimiento creado correctamente"})
    except Exception as e:
        return jsonify({"mensaje": "Error al crear movimiento", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)