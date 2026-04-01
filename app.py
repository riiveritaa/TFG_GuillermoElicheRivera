from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Configuración conexión MySQL

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'TFG'

mysql = MySQL(app)

#Regsitro

@app.route('/registro', methods=['POST'])
def registro():

    data = request.json

    nombre = data['nombre']
    email = data['email']
    password = data['password']

# Generar hash

    password_hash = generate_password_hash(password)

    cur = mysql.connection.cursor()

    cur.execute(
        "INSERT INTO usuarios (nombreUsuario, email, password) VALUES (%s, %s, %s)",
        (nombre, email, password_hash)
    )

    mysql.connection.commit()
    cur.close()

    return jsonify({"mensaje": "Usuario registrado correctamente"})

#Login

@app.route('/login', methods=['POST'])
def login():

    data = request.json
    email = data['email']
    password = data['password']

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
    usuario = cur.fetchone()
    cur.close()

    print(usuario)
    if usuario and check_password_hash(usuario[3], password):
        return jsonify({"mensaje": "Login correcto"})
    else:
        return jsonify({"mensaje": "Credenciales incorrectas"}), 401

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