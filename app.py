from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import pytz

# ==============================================================================
# CONFIGURACIÓN INICIAL DE FLASK Y BASE DE DATOS
# ==============================================================================
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = os.urandom(24)

# Parámetros de conexión a MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'TFG'

mysql = MySQL(app)

# Helper: Evita la notación científica en números pequeños (ej. 0.000002)
def fmt_q(val):
    """
    Formatea las cantidades numéricas para limitar a 6 decimales 
    y evitar la notación científica que puede confundir en la vista.
    """
    s = f"{float(val):.6f}"
    if '.' in s: 
        s = s.rstrip('0').rstrip('.')
    return s

# ==============================================================================
# RUTAS DE AUTENTICACIÓN (LOGIN, REGISTRO, LOGOUT)
# ==============================================================================

@app.route('/')
def index():
    """Ruta raíz: redirige al dashboard si hay sesión activa, o al login."""
    if 'usuario_id' in session: 
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    """Valida las credenciales del usuario contra la base de datos."""
    email = request.form.get('email_form')
    password = request.form.get('pass_form')
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, nombreUsuario, password FROM usuarios WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()
    
    # Comprobación de hash seguro de contraseñas
    if user and check_password_hash(user[2], password):
        session['usuario_id'] = user[0]
        session['nombreUsuario'] = user[1]
        return redirect(url_for('dashboard'))
        
    flash("Datos incorrectos.", "error")
    return redirect(url_for('index'))

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    """Gestiona el alta de un nuevo usuario."""
    if request.method == 'POST':
        nombre = request.form.get('usuario_form')
        email = request.form.get('email_form')
        password = request.form.get('pass_form')
        try:
            cur = mysql.connection.cursor()
            hashed_pw = generate_password_hash(password)
            cur.execute("INSERT INTO usuarios (nombreUsuario, email, password) VALUES (%s, %s, %s)", 
                        (nombre, email, hashed_pw))
            session['usuario_id'] = cur.lastrowid
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('dashboard'))
        except Exception as e: 
            print(f"Error registrando usuario: {e}")
            return redirect(url_for('registro'))
            
    return render_template('registro.html')

@app.route('/logout')
def logout():
    """Cierra la sesión actual limpiando las variables de sesión."""
    session.clear()
    return redirect(url_for('index'))

# ==============================================================================
# RUTAS DE DASHBOARD Y CUENTAS (BANCARIAS / FIAT)
# ==============================================================================

@app.route('/dashboard')
def dashboard():
    """
    Ruta principal que aglutina y prepara todos los datos para la vista general:
    Ingresos, gastos mensuales, cuentas fiat, y la distribución del presupuesto.
    """
    if 'usuario_id' not in session: return redirect(url_for('index'))
    cur = mysql.connection.cursor()
    
    # Datos de configuración y saldo del usuario
    cur.execute("SELECT nombreUsuario, pct_fijo, pct_ocio, pct_ahorro, saldo_broker, depositos_netos FROM usuarios WHERE id = %s", (session['usuario_id'],))
    u_data = cur.fetchone()
    depositos_netos = max(0.0, float(u_data[5] or 0.0))

    # Cuentas bancarias del usuario
    cur.execute("SELECT id, nombre, saldo FROM cuentas WHERE usuario_id = %s", (session['usuario_id'],))
    cuentas_db = cur.fetchall()
    cuentas = [{'id': c[0], 'nombre': c[1], 'saldo': float(c[2])} for c in cuentas_db]
    nombres_cuentas = [c['nombre'] for c in cuentas]
    saldos_cuentas = [c['saldo'] for c in cuentas]
    
    # Paleta dinámica para la Rosca de Capital
    paleta = ['#3498DB', '#9B59B6', '#E67E22', '#1ABC9C', '#F1C40F', '#E74C3C']
    colores_cuentas = [paleta[i % len(paleta)] for i in range(len(cuentas))]

    # Cálculo del Presupuesto (Gastos vs Ingresos en curso del mes actual)
    ahora = datetime.now()
    cur.execute("SELECT tipo, categoria, SUM(cantidad) FROM movimientos WHERE usuario_id = %s AND MONTH(fecha) = %s AND YEAR(fecha) = %s GROUP BY tipo, categoria", (session['usuario_id'], ahora.month, ahora.year))
    movs = cur.fetchall()
    
    total_ingresos = sum(float(m[2]) for m in movs if m[0]=='ingreso')
    gastado = {'fijo': 0.0, 'ocio': 0.0, 'ahorro_inversion': 0.0}
    for m in movs:
        if m[0] == 'gasto' and m[1] in gastado: 
            gastado[m[1]] += float(m[2])

    # Elementos de Inversión para los botones de la Dashboard
    cur.execute("SELECT id, nombreCartera FROM carteras WHERE usuario_id = %s", (session['usuario_id'],))
    mis_carteras = [{'id': c[0], 'nombre': c[1]} for c in cur.fetchall()]
    cur.execute("SELECT DISTINCT a.ticker FROM cartera_activos ca JOIN activos a ON ca.activo_id = a.id WHERE ca.usuario_id = %s AND ca.cartera_id IS NULL", (session['usuario_id'],))
    mis_sueltas = [{'ticker': p[0]} for p in cur.fetchall()]
    cur.close()

    return render_template('dashboard.html', 
        nombre=u_data[0], 
        pct_fijo=u_data[1], pct_ocio=u_data[2], pct_ahorro=u_data[3], 
        presupuesto_fijo=(total_ingresos * u_data[1] / 100), 
        presupuesto_ocio=(total_ingresos * u_data[2] / 100), 
        presupuesto_ahorro=(total_ingresos * u_data[3] / 100), 
        gastado_fijo=gastado['fijo'], gastado_ocio=gastado['ocio'], gastado_ahorro=gastado['ahorro_inversion'], 
        cuentas=cuentas, nombres_cuentas=nombres_cuentas, saldos_cuentas=saldos_cuentas, colores_cuentas=colores_cuentas, 
        mis_carteras=mis_carteras, mis_sueltas=mis_sueltas, saldo_broker=u_data[4], depositos_netos=depositos_netos)

@app.route('/crear_cuenta', methods=['POST'])
def crear_cuenta():
    """Crea una nueva cuenta bancaria/efectivo asociada al usuario."""
    data = request.json
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO cuentas (usuario_id, nombre, tipo, saldo) VALUES (%s, %s, %s, %s)", 
                (session['usuario_id'], data['nombre'], data['tipo'], data['saldo']))
    mysql.connection.commit()
    return jsonify({"mensaje": "OK"})

# ==============================================================================
# RUTAS DE MOVIMIENTOS (INGRESOS Y GASTOS MUNDANOS)
# ==============================================================================

@app.route('/mis_movimientos')
def mis_movimientos():
    """Recupera y renderiza el historial de transacciones mensuales."""
    if 'usuario_id' not in session: return redirect(url_for('index'))
    ahora = datetime.now()
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, tipo, concepto, categoria, cantidad, fecha FROM movimientos WHERE usuario_id = %s AND MONTH(fecha) = %s AND YEAR(fecha) = %s ORDER BY fecha DESC, id DESC", (session['usuario_id'], ahora.month, ahora.year))
    movimientos = cur.fetchall()
    cur.close()
    
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    return render_template('movimientos.html', movimientos=movimientos, mes_nombre=meses[ahora.month - 1], anio=ahora.year)

@app.route('/movimiento', methods=['POST'])
def crear_movimiento():
    """Procesa un ingreso o gasto y ajusta el saldo de la cuenta bancaria elegida."""
    data = request.json
    cur = mysql.connection.cursor()
    
    # Verificación de liquidez para gastos
    if data['tipo'] == 'gasto':
        cur.execute("SELECT saldo FROM cuentas WHERE id = %s", (data['cuenta_id'],))
        if float(cur.fetchone()[0]) < float(data['cantidad']): 
            return jsonify({"error": "Fondos insuficientes en la cuenta."}), 400
            
    cur.execute("INSERT INTO movimientos (usuario_id, cuenta_id, tipo, concepto, categoria, cantidad, fecha) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                (session['usuario_id'], data['cuenta_id'], data['tipo'], data['concepto'], data['categoria'], data['cantidad'], data['fecha']))
                
    # Actualización automática de saldo bancario
    if data['tipo'] == 'ingreso': 
        cur.execute("UPDATE cuentas SET saldo = saldo + %s WHERE id = %s", (data['cantidad'], data['cuenta_id']))
    else: 
        cur.execute("UPDATE cuentas SET saldo = saldo - %s WHERE id = %s", (data['cantidad'], data['cuenta_id']))
        
    mysql.connection.commit()
    return jsonify({"mensaje": "OK"})

@app.route('/editar_movimiento/<int:id>', methods=['PUT'])
def editar_movimiento(id):
    """Permite corregir datos de una transacción existente."""
    data = request.json
    cur = mysql.connection.cursor()
    cur.execute("UPDATE movimientos SET concepto = %s, categoria = %s, cantidad = %s, fecha = %s WHERE id = %s AND usuario_id = %s", 
                (data['concepto'], data['categoria'], data['cantidad'], data['fecha'], id, session['usuario_id']))
    mysql.connection.commit()
    return jsonify({"mensaje": "OK"})

@app.route('/eliminar_movimiento/<int:id>', methods=['DELETE'])
def eliminar_movimiento(id):
    """Elimina una transacción del historial."""
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM movimientos WHERE id = %s AND usuario_id = %s", (id, session['usuario_id']))
    mysql.connection.commit()
    return jsonify({"mensaje": "OK"})

# ==============================================================================
# GESTIÓN DE CARTERAS (Lógica de Inversión Fina)
# ==============================================================================

@app.route('/mis_carteras')
def mis_carteras():
    """
    Ruta central del Módulo de Inversión. Recupera el portfolio completo:
    carteras estructuradas, posiciones individuales (sueltas), y precios medios.
    """
    if 'usuario_id' not in session: return redirect(url_for('index'))
    cur = mysql.connection.cursor()
    
    cur.execute("SELECT saldo_broker FROM usuarios WHERE id = %s", (session['usuario_id'],))
    saldo_broker = cur.fetchone()[0] or 0.0
    
    cur.execute("SELECT id, nombre, saldo FROM cuentas WHERE usuario_id = %s", (session['usuario_id'],))
    cuentas_banco = cur.fetchall()
    
    cur.execute("SELECT id, nombreCartera, liquidez FROM carteras WHERE usuario_id = %s", (session['usuario_id'],))
    carteras = cur.fetchall()
    
    # Extraemos todos los activos invertidos
    cur.execute("SELECT ca.cartera_id, a.ticker, a.nombre, ca.cantidad, ca.precio_compra, ca.peso_objetivo FROM cartera_activos ca JOIN activos a ON ca.activo_id = a.id WHERE ca.usuario_id = %s", (session['usuario_id'],))
    pos_db = cur.fetchall()
    cur.close()

    pos_carteras, agrupadas_sueltas = {}, {}
    
    for p in pos_db:
        c_id, ticker, nombre, cant, p_compra, peso = p
        cant, p_compra = float(cant), float(p_compra)
        val_inv = cant * p_compra
        
        # Agrupación de posiciones sueltas por Ticker
        if c_id is None:
            if ticker not in agrupadas_sueltas: 
                agrupadas_sueltas[ticker] = {'ticker': ticker, 'nombre': nombre, 'cantidad': 0.0, 'invertido': 0.0}
            agrupadas_sueltas[ticker]['cantidad'] += cant
            agrupadas_sueltas[ticker]['invertido'] += val_inv
        else:
            if c_id not in pos_carteras: 
                pos_carteras[c_id] = []
            pos_carteras[c_id].append({'ticker': ticker, 'nombre': nombre, 'cantidad': cant, 'precio_medio': p_compra, 'invertido': val_inv, 'peso_objetivo': float(peso or 0)})

    # Post-procesamiento matemático para la vista
    sueltas = []
    for t, data in agrupadas_sueltas.items():
        data['precio_medio'] = (data['invertido'] / data['cantidad']) if data['cantidad'] > 0 else 0
        data['cantidad_str'] = fmt_q(data['cantidad'])
        sueltas.append(data)

    for c_id in pos_carteras:
        total_inv_c = sum(p['invertido'] for p in pos_carteras[c_id])
        for p in pos_carteras[c_id]: 
            p['porcentaje'] = (p['invertido'] / total_inv_c * 100) if total_inv_c > 0 else 0
            p['cantidad_str'] = fmt_q(p['cantidad'])

    return render_template('carteras.html', carteras=carteras, posiciones=pos_carteras, sueltas=sueltas, cuentas_banco=cuentas_banco, saldo_broker=saldo_broker)

@app.route('/crear_cartera', methods=['POST'])
def crear_cartera():
    """Instancia un nuevo bloque (cesta) de inversión vacía."""
    data = request.json
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO carteras (usuario_id, nombreCartera) VALUES (%s, %s)", (session['usuario_id'], data['nombre']))
    mysql.connection.commit()
    cur.close()
    return jsonify({"mensaje": "OK"})

@app.route('/agregar_posicion', methods=['POST'])
def agregar_posicion():
    """
    Agrega un activo (Ticker) a una cartera estructurada o a la zona suelta.
    Valida en tiempo real que el Ticker existe en Yahoo Finance.
    """
    data = request.json
    c_id = None if data['cartera_id'] == "suelta" else data['cartera_id']
    ticker = data['ticker'].upper()
    peso = float(data.get('peso_objetivo', 0))
    
    cur = mysql.connection.cursor()
    
    # 1. Validación Externa del Ticker
    try:
        stock = yf.Ticker(ticker)
        if not stock.fast_info.get('lastPrice'): return jsonify({"error": "Ticker inválido."}), 404
    except: return jsonify({"error": "Error con Yahoo Finance."}), 500
    
    # 2. Control de Peso Lógico (Máximo 100%)
    if c_id:
        cur.execute("SELECT SUM(peso_objetivo) FROM cartera_activos WHERE cartera_id = %s", (c_id,))
        suma_actual = float(cur.fetchone()[0] or 0.0)
        if suma_actual + peso > 100: 
            return jsonify({"error": "Superas el 100%."}), 400

    # 3. Creación del Activo en Base de Datos si es nuevo
    cur.execute("SELECT id FROM activos WHERE ticker = %s", (ticker,))
    activo = cur.fetchone()
    if not activo:
        cur.execute("INSERT INTO activos (nombre, ticker, tipo) VALUES (%s, %s, 'accion')", (stock.info.get('shortName', ticker), ticker))
        activo_id = cur.lastrowid
    else: 
        activo_id = activo[0]

    # 4. Flujo A: Compra de Posición Individual Inmediata
    if c_id is None:
        cant, p_compra = float(data['cantidad']), float(data['precio_compra'])
        total = cant * p_compra
        cur.execute("SELECT saldo_broker FROM usuarios WHERE id = %s", (session['usuario_id'],))
        if float(cur.fetchone()[0] or 0) < total: 
            return jsonify({"error": "Sin reserva principal."}), 400
            
        cur.execute("UPDATE usuarios SET saldo_broker = saldo_broker - %s WHERE id = %s", (total, session['usuario_id']))
        cur.execute("SELECT id, cantidad, precio_compra FROM cartera_activos WHERE usuario_id=%s AND cartera_id IS NULL AND activo_id=%s", (session['usuario_id'], activo_id))
        existente = cur.fetchone()
        
        # Ponderación del precio medio de compra (Algoritmo DCA)
        if existente:
            l_id, old_qty, old_precio = existente
            new_qty = float(old_qty) + cant
            new_precio = ((float(old_qty) * float(old_precio)) + total) / new_qty
            cur.execute("UPDATE cartera_activos SET cantidad=%s, precio_compra=%s WHERE id=%s", (new_qty, new_precio, l_id))
        else:
            cur.execute("INSERT INTO cartera_activos (usuario_id, activo_id, cantidad, precio_compra) VALUES (%s, %s, %s, %s)", (session['usuario_id'], activo_id, cant, p_compra))
            
    # 5. Flujo B: Inserción en Cartera (Compra diferida, gestionada por traspaso)
    else:
        cur.execute("SELECT id FROM cartera_activos WHERE usuario_id=%s AND cartera_id=%s AND activo_id=%s", (session['usuario_id'], c_id, activo_id))
        existente_cartera = cur.fetchone()
        if existente_cartera: 
            cur.execute("UPDATE cartera_activos SET peso_objetivo = peso_objetivo + %s WHERE id=%s", (peso, existente_cartera[0]))
        else: 
            cur.execute("INSERT INTO cartera_activos (usuario_id, cartera_id, activo_id, cantidad, precio_compra, peso_objetivo) VALUES (%s, %s, %s, 0, 0, %s)", (session['usuario_id'], c_id, activo_id, peso))
    
    mysql.connection.commit()
    return jsonify({"mensaje": "OK"})

@app.route('/traspaso_cartera', methods=['POST'])
def traspaso_cartera():
    """
    Motor central de la Gestión de Liquidez en Carteras.
    Distribuye y retira dinero dinámicamente según pesos (Auto-Invest y Rebalanceo).
    """
    data = request.json
    c_id = data['cartera_id']
    monto = float(data['cantidad'])
    direccion = data['direccion']
    cur = mysql.connection.cursor()
    
    # FLUJO A: Invertir en la Cartera
    if direccion == 'hacia_cartera':
        cur.execute("SELECT saldo_broker FROM usuarios WHERE id = %s", (session['usuario_id'],))
        if float(cur.fetchone()[0] or 0) < monto: 
            return jsonify({"error": "Reserva Principal insuficiente."}), 400
            
        cur.execute("UPDATE usuarios SET saldo_broker = saldo_broker - %s WHERE id = %s", (monto, session['usuario_id']))
        cur.execute("SELECT activo_id, peso_objetivo FROM cartera_activos WHERE cartera_id = %s AND peso_objetivo > 0", (c_id,))
        items = cur.fetchall()
        tasa_eur = yf.Ticker("EURUSD=X").fast_info.get('lastPrice', 1.08)
        
        for a_id, peso in items:
            dinero_activo = monto * (float(peso) / 100)
            cur.execute("SELECT ticker FROM activos WHERE id = %s", (a_id,))
            stock = yf.Ticker(cur.fetchone()[0])
            p_actual = stock.fast_info.get('lastPrice')
            moneda = stock.fast_info.get('currency', 'USD')
            
            if p_actual:
                p_eur = p_actual / tasa_eur if moneda != 'EUR' else p_actual
                nuevas_uds = dinero_activo / p_eur
                cur.execute("SELECT cantidad, precio_compra FROM cartera_activos WHERE cartera_id = %s AND activo_id = %s", (c_id, a_id))
                old_qty, old_price = cur.fetchone()
                new_qty = float(old_qty) + nuevas_uds
                new_avg_price = ((float(old_qty)*float(old_price)) + dinero_activo) / new_qty if new_qty > 0 else 0
                cur.execute("UPDATE cartera_activos SET cantidad = %s, precio_compra = %s WHERE cartera_id = %s AND activo_id = %s", (new_qty, new_avg_price, c_id, a_id))
                
        suma_pesos = sum(float(i[1]) for i in items)
        if suma_pesos < 100: 
            cur.execute("UPDATE carteras SET liquidez = liquidez + %s WHERE id = %s", (monto * (1 - (suma_pesos/100)), c_id))

    # FLUJO B: Retirar inversión y pasarla a liquidez de la cartera
    elif direccion == 'desde_inversion':
        cur.execute("SELECT activo_id, cantidad, peso_objetivo FROM cartera_activos WHERE cartera_id = %s AND cantidad > 0", (c_id,))
        activos = cur.fetchall()
        tasa_eur = yf.Ticker("EURUSD=X").fast_info.get('lastPrice', 1.08)
        valor_total_invertido = 0
        precios = {}
        pesos_invertidos = {}
        suma_pesos_invertidos = 0
        
        for a_id, qty, peso in activos:
            cur.execute("SELECT ticker FROM activos WHERE id = %s", (a_id,))
            stock = yf.Ticker(cur.fetchone()[0])
            p_eur = stock.fast_info.get('lastPrice') / (tasa_eur if stock.fast_info.get('currency', 'USD') != 'EUR' else 1)
            precios[a_id] = p_eur
            valor_total_invertido += float(qty) * p_eur
            pesos_invertidos[a_id] = float(peso)
            suma_pesos_invertidos += float(peso)
            
        if valor_total_invertido < monto: 
            return jsonify({"error": "No hay capital invertido suficiente."}), 400
            
        # Venta proporcional adaptada a los pesos reales
        for a_id, qty, peso in activos:
            peso_relativo = pesos_invertidos[a_id] / suma_pesos_invertidos if suma_pesos_invertidos > 0 else ((float(qty) * precios[a_id]) / valor_total_invertido)
            monto_vender = monto * peso_relativo
            uds_vender = min(monto_vender / precios[a_id], float(qty))
            cur.execute("UPDATE cartera_activos SET cantidad = cantidad - %s WHERE cartera_id = %s AND activo_id = %s", (uds_vender, c_id, a_id))
            
        cur.execute("UPDATE carteras SET liquidez = liquidez + %s WHERE id = %s", (monto, c_id))

    # FLUJO C: Sacar liquidez de la cartera a la Reserva Principal
    else:
        cur.execute("SELECT liquidez FROM carteras WHERE id = %s", (c_id,))
        if float(cur.fetchone()[0]) < monto: 
            return jsonify({"error": "Liquidez insuficiente."}), 400
        cur.execute("UPDATE carteras SET liquidez = liquidez - %s WHERE id = %s", (monto, c_id))
        cur.execute("UPDATE usuarios SET saldo_broker = saldo_broker + %s WHERE id = %s", (monto, session['usuario_id']))

    mysql.connection.commit()
    return jsonify({"mensaje": "OK"})

@app.route('/traspaso_broker', methods=['POST'])
def traspaso_broker():
    """Puente entre el mundo FIAT (Bancos) y el BROKER (Reserva Principal). Afecta a Depósitos Netos."""
    data = request.json
    cur = mysql.connection.cursor()
    monto = float(data['cantidad'])
    
    if data['direccion'] == 'hacia_broker':
        cur.execute("SELECT saldo FROM cuentas WHERE id = %s", (data['cuenta_id'],))
        if float(cur.fetchone()[0]) < monto: 
            return jsonify({"error": "Faltan fondos bancarios."}), 400
        cur.execute("UPDATE cuentas SET saldo = saldo - %s WHERE id = %s", (monto, data['cuenta_id']))
        # Incrementa depósitos netos
        cur.execute("UPDATE usuarios SET saldo_broker = saldo_broker + %s, depositos_netos = depositos_netos + %s WHERE id = %s", (monto, monto, session['usuario_id']))
    else:
        cur.execute("SELECT saldo_broker FROM usuarios WHERE id = %s", (session['usuario_id'],))
        if float(cur.fetchone()[0]) < monto: 
            return jsonify({"error": "Faltan fondos en Reserva."}), 400
        cur.execute("UPDATE usuarios SET saldo_broker = saldo_broker - %s, depositos_netos = depositos_netos - %s WHERE id = %s", (monto, monto, session['usuario_id']))
        cur.execute("UPDATE cuentas SET saldo = saldo + %s WHERE id = %s", (monto, data['cuenta_id']))
        
    mysql.connection.commit()
    return jsonify({"mensaje": "OK"})

@app.route('/vender_posicion', methods=['POST'])
def vender_posicion():
    """Ejecuta una orden de venta a mercado y libera capital al saldo de origen."""
    data = request.json
    ticker = data['ticker']
    qty_vender = float(data['cantidad'])
    c_id = None if data['cartera_id'] == 'suelta' else data['cartera_id']
    cur = mysql.connection.cursor()

    if c_id: 
        cur.execute("SELECT SUM(cantidad) FROM cartera_activos WHERE cartera_id=%s AND activo_id=(SELECT id FROM activos WHERE ticker=%s)", (c_id, ticker))
    else: 
        cur.execute("SELECT SUM(cantidad) FROM cartera_activos WHERE cartera_id IS NULL AND activo_id=(SELECT id FROM activos WHERE ticker=%s)", (ticker,))
        
    if float(cur.fetchone()[0] or 0) < qty_vender: 
        return jsonify({"error": "No tienes tantas unidades."}), 400

    try:
        stock = yf.Ticker(ticker)
        p_actual = stock.fast_info.get('lastPrice')
        moneda = stock.fast_info.get('currency', 'USD')
        tasa_eur = yf.Ticker("EURUSD=X").fast_info.get('lastPrice', 1.08)
        p_venta = p_actual / tasa_eur if moneda != 'EUR' else p_actual
    except: 
        return jsonify({"error": "Error Yahoo Finance."}), 500

    valor_venta = qty_vender * p_venta
    if c_id: 
        cur.execute("UPDATE carteras SET liquidez = liquidez + %s WHERE id = %s", (valor_venta, c_id))
    else: 
        cur.execute("UPDATE usuarios SET saldo_broker = saldo_broker + %s WHERE id = %s", (valor_venta, session['usuario_id']))
    
    if c_id: 
        cur.execute("SELECT id, cantidad FROM cartera_activos WHERE usuario_id=%s AND cartera_id=%s AND activo_id=(SELECT id FROM activos WHERE ticker=%s) ORDER BY id ASC", (session['usuario_id'], c_id, ticker))
    else: 
        cur.execute("SELECT id, cantidad FROM cartera_activos WHERE usuario_id=%s AND cartera_id IS NULL AND activo_id=(SELECT id FROM activos WHERE ticker=%s) ORDER BY id ASC", (session['usuario_id'], ticker))
    
    # Estrategia de liberación por lotes (FIFO simple adaptado)
    lotes = cur.fetchall()
    restante = qty_vender
    for lid, lqty in lotes:
        if restante <= 0: break
        if float(lqty) <= restante: 
            cur.execute("DELETE FROM cartera_activos WHERE id = %s", (lid,))
            restante -= float(lqty)
        else: 
            cur.execute("UPDATE cartera_activos SET cantidad = cantidad - %s WHERE id = %s", (restante, lid))
            restante = 0
            
    mysql.connection.commit()
    return jsonify({"mensaje": "OK"})

@app.route('/reajustar_cartera', methods=['POST'])
def reajustar_cartera():
    """Recalcula y compra/vende automáticamente para que la cartera cuadre con los Pesos %."""
    data = request.json
    c_id = data['cartera_id']
    cur = mysql.connection.cursor()
    cur.execute("SELECT liquidez FROM carteras WHERE id=%s", (c_id,))
    liquidez = float(cur.fetchone()[0])
    cur.execute("SELECT activo_id, cantidad, peso_objetivo FROM cartera_activos WHERE cartera_id=%s", (c_id,))
    activos = cur.fetchall()
    
    total_value = liquidez
    precios_actuales = {}
    tasa_eur = yf.Ticker("EURUSD=X").fast_info.get('lastPrice', 1.08)
    
    # 1. Foto fija del valor total de la cartera (Liquidez + Valor de Mercado)
    for a_id, qty, peso in activos:
        cur.execute("SELECT ticker FROM activos WHERE id=%s", (a_id,))
        stock = yf.Ticker(cur.fetchone()[0])
        p_eur = stock.fast_info.get('lastPrice') / (tasa_eur if stock.fast_info.get('currency', 'USD') != 'EUR' else 1)
        precios_actuales[a_id] = p_eur
        total_value += float(qty) * p_eur
        
    # 2. Ajuste al peso objetivo puro
    suma_pesos = 0
    for a_id, qty, peso in activos:
        suma_pesos += float(peso)
        new_qty = ((total_value * float(peso) / 100) / precios_actuales[a_id])
        cur.execute("UPDATE cartera_activos SET cantidad=%s, precio_compra=%s WHERE cartera_id=%s AND activo_id=%s", (new_qty, precios_actuales[a_id], c_id, a_id))
        
    cur.execute("UPDATE carteras SET liquidez=%s WHERE id=%s", (max(0, total_value * (1 - suma_pesos/100)), c_id))
    mysql.connection.commit()
    return jsonify({"mensaje": "OK"})

@app.route('/actualizar_peso', methods=['PUT'])
def actualizar_peso():
    data = request.json
    cur = mysql.connection.cursor()
    cur.execute("SELECT SUM(peso_objetivo) FROM cartera_activos WHERE cartera_id = %s AND activo_id != (SELECT id FROM activos WHERE ticker = %s)", (data['cartera_id'], data['ticker']))
    if float(cur.fetchone()[0] or 0.0) + float(data['peso']) > 100: return jsonify({"error": "Suma superior al 100%"}), 400
    cur.execute("UPDATE cartera_activos SET peso_objetivo = %s WHERE usuario_id = %s AND cartera_id = %s AND activo_id = (SELECT id FROM activos WHERE ticker = %s)", (float(data['peso']), session['usuario_id'], data['cartera_id'], data['ticker']))
    mysql.connection.commit()
    return jsonify({"mensaje": "OK"})

@app.route('/eliminar_cartera/<int:id>', methods=['DELETE'])
def eliminar_cartera(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM carteras WHERE id = %s AND usuario_id = %s", (id, session['usuario_id']))
    mysql.connection.commit()
    return jsonify({"mensaje": "OK"})

# ==============================================================================
# APIS EXTERNAS Y MOTOR GRÁFICO DEL DASHBOARD (EL CEREBRO DE LAS GRÁFICAS)
# ==============================================================================

@app.route('/api/precios_live', methods=['POST'])
def precios_live():
    """Endpoint de micro-pooling para refrescar precios en tiempo real sin recargar página."""
    data = request.get_json(silent=True) or {}
    tickers = data.get('tickers', [])
    precios = {}
    try:
        tasa = yf.Ticker("EURUSD=X").fast_info.get('lastPrice', 1.08)
        for t in set(tickers):
            stock = yf.Ticker(t)
            p = stock.fast_info.get('lastPrice')
            moneda = stock.fast_info.get('currency', 'USD')
            if p: precios[t] = round(p / tasa if moneda != 'EUR' else p, 4)
    except: pass
    return jsonify(precios)

@app.route('/api/historico')
def get_historico():
    """
    Algoritmo central de graficado patrimonial. 
    Cruza el registro de la Base de Datos con el histórico de Yahoo Finance para
    reconstruir el valor de la cartera/activo en el tiempo respetando los aportes reales (Baseline).
    """
    if 'usuario_id' not in session: return jsonify({})
    
    tipo = request.args.get('tipo', 'total')
    id_val = request.args.get('id', '')
    periodo = request.args.get('periodo', '1d')
    
    cur = mysql.connection.cursor()
    madrid_tz = pytz.timezone('Europe/Madrid')
    ahora_madrid = datetime.now(madrid_tz)

    # 1. CÁLCULO ESTRICTO DE VENTANA DE TIEMPO (Cuadratura de Marco Temporal)
    start_date = None
    if periodo == '1d': 
        start_date = ahora_madrid - timedelta(hours=24); interval = '5m'; yf_period = '5d'
    elif periodo == '1w': 
        start_date = ahora_madrid - timedelta(days=7); interval = '30m'; yf_period = '1mo'
    elif periodo == '1mo': 
        start_date = ahora_madrid - timedelta(days=30); interval = '1d'; yf_period = '3mo'
    elif periodo == '3mo': 
        start_date = ahora_madrid - timedelta(days=90); interval = '1d'; yf_period = '6mo'
    elif periodo == 'ytd': 
        start_date = datetime(ahora_madrid.year, 1, 1, tzinfo=madrid_tz); interval = '1d'; yf_period = '1y'
    elif periodo == '1y': 
        start_date = ahora_madrid - timedelta(days=365); interval = '1d'; yf_period = '2y'
    elif periodo == 'max': 
        cur.execute("SELECT MIN(fecha_compra) FROM cartera_activos WHERE usuario_id = %s", (session['usuario_id'],))
        min_date_db = cur.fetchone()[0]
        start_year = min_date_db.year if min_date_db else ahora_madrid.year
        start_date = datetime(start_year, 1, 1, tzinfo=madrid_tz); interval = '1d'; yf_period = 'max'
    else:
        start_date = ahora_madrid - timedelta(hours=24); interval = '5m'; yf_period = '5d'

    # 2. EXTRACCIÓN DE DATOS DE LA BASE DE DATOS SEGÚN FILTRO LATERAL
    liquidez_add = 0.0
    depositos_contextuales = 0.0
    
    if tipo == 'total':
        cur.execute("SELECT SUM(liquidez) FROM carteras WHERE usuario_id = %s", (session['usuario_id'],))
        l_res = cur.fetchone()[0]
        if l_res: liquidez_add = float(l_res)
        cur.execute("SELECT depositos_netos FROM usuarios WHERE id = %s", (session['usuario_id'],))
        depositos_contextuales = float(cur.fetchone()[0] or 0)
        query = "SELECT a.ticker, SUM(ca.cantidad), MIN(ca.fecha_compra), SUM(ca.cantidad * ca.precio_compra) FROM cartera_activos ca JOIN activos a ON ca.activo_id = a.id WHERE ca.usuario_id = %s AND ca.cantidad > 0 GROUP BY a.ticker"
        cur.execute(query, (session['usuario_id'],))
        
    elif tipo == 'cartera':
        cur.execute("SELECT liquidez FROM carteras WHERE usuario_id = %s AND id = %s", (session['usuario_id'], id_val))
        l_res = cur.fetchone()[0]
        if l_res: liquidez_add = float(l_res)
        query = "SELECT a.ticker, SUM(ca.cantidad), MIN(ca.fecha_compra), SUM(ca.cantidad * ca.precio_compra) FROM cartera_activos ca JOIN activos a ON ca.activo_id = a.id WHERE ca.usuario_id = %s AND ca.cartera_id = %s AND ca.cantidad > 0 GROUP BY a.ticker"
        cur.execute(query, (session['usuario_id'], id_val))
        
    else:
        query = "SELECT a.ticker, SUM(ca.cantidad), MIN(ca.fecha_compra), SUM(ca.cantidad * ca.precio_compra) FROM cartera_activos ca JOIN activos a ON ca.activo_id = a.id WHERE ca.usuario_id = %s AND ca.cartera_id IS NULL AND a.ticker = %s AND ca.cantidad > 0 GROUP BY a.ticker"
        cur.execute(query, (session['usuario_id'], id_val))

    activos = cur.fetchall()
    
    # Depósitos contextuales representan el "Baseline" o dinero invertido duro
    if tipo == 'cartera': depositos_contextuales = sum(float(row[3] or 0) for row in activos) + liquidez_add
    elif tipo == 'posicion': depositos_contextuales = sum(float(row[3] or 0) for row in activos)
        
    depositos_contextuales = max(0.0, depositos_contextuales)
    cur.close()

    try:
        tasa = yf.Ticker("EURUSD=X").fast_info.get('lastPrice', 1.08)
        dfs = []
        global_min_date_naive = None
        
        # 3. CONVERSIÓN DE FECHAS CLAVE
        for _, _, f_compra, _ in activos:
            if f_compra:
                if isinstance(f_compra, str): f_compra = pd.to_datetime(f_compra)
                if f_compra.tzinfo is None: f_compra = madrid_tz.localize(f_compra)
                f_compra_naive = f_compra.replace(tzinfo=None)
                if global_min_date_naive is None or f_compra_naive < global_min_date_naive:
                    global_min_date_naive = f_compra_naive

        # Seleccionar Formato para las Tooltips de Chart.js
        if periodo in ['1y', 'max', 'ytd']: fmt = '%d %b %Y'
        elif interval in ['5m', '30m', '1h']: fmt = '%d %b %H:%M'
        else: fmt = '%d %b'

        start_naive = start_date.replace(tzinfo=None)

        # 4. EXTRACCIÓN Y LIMPIEZA DE YAHOO FINANCE POR ACTIVO
        for ticker, qty, fecha_compra, invertido in activos:
            if start_date and periodo not in ['1y', 'max', 'ytd', '3mo', '1mo']:
                hist = yf.Ticker(ticker).history(start=start_date.strftime('%Y-%m-%d'), interval=interval)
            else:
                hist = yf.Ticker(ticker).history(period=yf_period, interval=interval)
            
            if not hist.empty:
                # Paso 4.1: Normalizar Horas a España
                if hist.index.tz: 
                    hist.index = hist.index.tz_convert(madrid_tz).tz_localize(None)
                else:
                    hist.index = hist.index.tz_localize(None)
                
                # Paso 4.2: Recorte Matemático del Rango de Tiempo Solicitado
                if interval == '1d':
                    start_compare = pd.Timestamp(start_naive.date())
                    hist = hist[hist.index >= start_compare]
                else:
                    hist = hist[hist.index >= start_naive]
                
                # Paso 4.3: "LÍNEA PLANA". Aplana a cero los días donde la acción no pertenecía al portfolio
                if fecha_compra:
                    if isinstance(fecha_compra, str): fecha_compra = pd.to_datetime(fecha_compra)
                    f_cmp_naive = fecha_compra.replace(tzinfo=None)
                    
                    if interval == '1d':
                        f_date_cmp = f_cmp_naive.date()
                        hist_dates = hist.index.date if hasattr(hist.index, 'date') else hist.index
                        hist.loc[hist_dates < f_date_cmp, 'Close'] = 0.0
                    else:
                        hist.loc[hist.index < f_cmp_naive, 'Close'] = 0.0
                
                # Conversión de divisa general a EUR
                val = hist[['Close']] * float(qty)
                moneda = yf.Ticker(ticker).fast_info.get('currency', 'USD')
                if moneda != 'EUR': val = val / tasa
                val.columns = [ticker]
                dfs.append(val)

        # SI LA CARTERA ES NUEVA Y AÚN NO HA INVERTIDO DATOS AL MERCADO
        if not dfs:
            if liquidez_add > 0:
                return jsonify({
                    "labels":[start_date.strftime(fmt), ahora_madrid.strftime(fmt)], 
                    "values":[liquidez_add, liquidez_add], 
                    "current_value": liquidez_add, 
                    "change_eur": 0, "change_pct": 0, "depositos": depositos_contextuales
                })
            return jsonify({"labels":[], "values":[], "current_value": 0, "change_eur": 0, "change_pct": 0, "depositos": depositos_contextuales})

        # 5. AGRUPACIÓN Y SANITIZACIÓN FINAL (Asegurando la eliminación de NaNs)
        df_final = pd.concat(dfs, axis=1).ffill().sum(axis=1)
        
        # Relleno predictivo para gráficas largas (Los Fines de Semana de la bolsa)
        if interval == '1d' and not df_final.empty:
            full_range = pd.date_range(start=start_date.date(), end=ahora_madrid.date(), freq='D')
            df_final = df_final.reindex(full_range).ffill().fillna(0)
        
        # Inyección del saldo líquido de la cartera en el tiempo correcto
        if liquidez_add > 0:
            if global_min_date_naive:
                mask = [d >= global_min_date_naive.date() for d in df_final.index.date]
                df_final.loc[mask] += liquidez_add
            else:
                df_final += liquidez_add
                
        labels = [d.strftime(fmt) for d in df_final.index]
        values = [round(v, 2) for v in df_final.values]
        
        # Obtención del valor en vivo del último milisegundo posible
        current_live_value = liquidez_add
        for ticker, qty, _, _ in activos:
            p_live = yf.Ticker(ticker).fast_info.get('lastPrice', 0)
            mon = yf.Ticker(ticker).fast_info.get('currency', 'USD')
            p_eur = p_live / tasa if mon != 'EUR' else p_live
            current_live_value += float(qty) * p_eur
            
        # Inyección de las Anclas Temporales: Evita que el gráfico quede flotando
        ahora_str = ahora_madrid.strftime(fmt)
        start_str = start_date.strftime(fmt)

        if interval in ['5m', '30m']:
            if labels and labels[0] != start_str:
                labels.insert(0, start_str)
                values.insert(0, values[0])
            if labels and labels[-1] != ahora_str:
                labels.append(ahora_str)
                values.append(round(current_live_value, 2))
            else:
                values[-1] = round(current_live_value, 2)
        else:
            if labels and labels[-1] != ahora_str:
                labels.append(ahora_str)
                values.append(round(current_live_value, 2))
            else:
                values[-1] = round(current_live_value, 2)
        
        # 6. CÁLCULO MAGISTRAL DE RENDIMIENTO (P&L) vs CAPITAL BASE
        first_nonzero_idx = next((i for i, v in enumerate(values) if v > 0), -1)
        if first_nonzero_idx > 0:
            baseline = depositos_contextuales
        else:
            baseline = values[0] if values else 0
            
        change_eur = current_live_value - baseline
        change_pct = (change_eur / baseline * 100) if baseline > 0 else 0
        
        return jsonify({
            "labels": labels, "values": values, "current_value": current_live_value, 
            "change_eur": change_eur, "change_pct": change_pct, "depositos": depositos_contextuales
        })
    except Exception as e: 
        print(f"Error Crítico API Histórico: {e}")
        return jsonify({"labels":[], "values":[], "current_value": 0, "change_eur": 0, "change_pct": 0, "depositos": depositos_contextuales})

if __name__ == '__main__':
    app.run(debug=True)