from flask import Flask, request, jsonify, render_template
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Configuración conexión MySQL

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'TFG'

mysql = MySQL(app)

# Ruta para la página de login
@app.route('/')
def index():
    return render_template('login.html')

# Ruta para la página de registro

@app.route('/registro', methods=['GET'])
def pagina_registro():
    return render_template('registro.html')

#Login

@app.route('/login', methods=['POST'])
def login():

# 1. Recogemos los datos que vienen del HTML
    email = request.form.get('email_form')
    password = request.form.get('pass_form')

#si vienen vacios evitamos que se rompa
    if not email or not password:
        return jsonify({"mensaje": "Por favor, completa todos los campos"}), 400

    cur = mysql.connection.cursor()

# 2. Buscamos el usuario en la base de datos por su email
    cur.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
    usuario = cur.fetchone()
    cur.close()

#3 verificamos si el usuario existe y si la contraseña es correcta
    if usuario and check_password_hash(usuario[3], password):
        return jsonify({"mensaje": "Login exitoso", "usuario_id": usuario[0]})
    else:
        return jsonify({"mensaje": "Email o contraseña incorrectos"}), 401

#Regsitro

@app.route('/registro', methods=['POST'])
def registro():

# 1. Recogemos los datos que vienen del HTML

    nombre = request.form.get('usuario_form')
    email = request.form.get('email_form')
    password = request.form.get('pass_form')

    if not nombre or not email or not password:
        return jsonify({"mensaje": "Faltan campos obligatorios"}), 400

    # Generar hash

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
    
#Crear movimiento 

@app.route('/movimiento', methods=['POST'])
def movimiento():

    data = request.json

    usuario_id = data['usuario_id']
    tipo = data['tipo']
    concepto = data['concepto']
    cantidad = data['cantidad']
    fecha = data['fecha']

    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO movimientos (usuario_id, tipo, concepto, cantidad, fecha) VALUES (%s, %s, %s, %s, %s)",
        (usuario_id, tipo, concepto, cantidad, fecha)
    )

    mysql.connection.commit()
    cur.close()

    return jsonify({"mensaje": "Movimiento creado"})

#Lista de movimientos

@app.route('/movimientos/<int:usuario_id>', methods=['GET'])
def obtener_movimientos(usuario_id):

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM movimientos WHERE usuario_id = %s", (usuario_id,))
    movimientos = cur.fetchall()
    cur.close()

    return jsonify(movimientos)

#Actualizar movimientos 

@app.route('/movimiento/<int:id>', methods=['PUT'])
def actualizar_movimiento(id):

    data = request.json
    concepto = data['concepto']
    cantidad = data['cantidad']

    cur = mysql.connection.cursor()
    cur.execute(
        "UPDATE movimientos SET concepto = %s, cantidad = %s WHERE id = %s",
        (concepto, cantidad, id)
    )
    mysql.connection.commit()
    cur.close()

    return jsonify({"mensaje": "Movimiento actualizado"})

#Borrar movimientos 

@app.route('/movimiento/<int:id>', methods=['DELETE'])
def eliminar_movimiento(id):

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM movimientos WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()

    return jsonify({"mensaje": "Movimiento eliminado"})

print(app.url_map)

if __name__ == '__main__':
    app.run(debug=True)