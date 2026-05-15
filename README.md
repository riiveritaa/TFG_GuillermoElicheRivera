# TFG - Gestión Financiera Personal

## Descripción general

Este proyecto es una aplicación web de gestión financiera personal desarrollada con Flask y MySQL.
Permite registrar usuarios, iniciar sesión, gestionar cuentas y movimientos, y visualizar datos del presupuesto mensual.

## Arquitectura

### Backend
- `Codigo fuente/app.py`
- Flask como framework principal.
- `flask_mysqldb` para la conexión con MySQL.
- `werkzeug.security` para el hashing seguro de contraseñas.
- Sesiones de Flask para mantener la sesión del usuario.
- Rutas que renderizan plantillas y rutas API (`/api/*`) que devuelven datos JSON para el frontend.

### Frontend
- Plantillas Jinja2 en `Codigo fuente/templates/`:
  - `login.html`
  - `registro.html`
  - `dashboard.html`
- Archivos estáticos en `Codigo fuente/static/`:
  - CSS en `Codigo fuente/static/Css/`
  - JavaScript en `Codigo fuente/static/js/`

### Base de datos
- Esquema SQL en `Bbdd/TFG_DAW.sql`.
- Tablas principales esperadas (según el código):
  - `usuarios`
  - `cuentas`
  - `movimientos`
- La base de datos se usa para almacenar credenciales, cuentas de usuario y transacciones.

## Estado actual del proyecto

### Funcionalidades implementadas
- Registro de usuario.
- Login de usuario con verificación de contraseña.
- Dashboard protegido por sesión.
- APIs para:
  - obtener datos del dashboard
  - crear cuentas
  - crear movimientos
  - eliminar movimientos
  - editar movimientos
  - ajustar presupuesto
  - eliminar cuentas
- Cálculo de presupuestos por categoría (`fijo`, `ocio`, `ahorro_inversion`).
- Cálculo de saldo de cuentas y control de fondos insuficientes.

### Limitaciones y mejoras pendientes
- Configuración de base de datos fijada en el código.
- `app.run(debug=True)` habilita modo de desarrollo; no es seguro para producción.
- Falta validación completa de formularios y entrada de datos en frontend y backend.
- No hay gestión de migraciones para la base de datos.
- No hay pruebas automatizadas incluidas.
- No hay archivo `requirements.txt` ni entorno virtual documentado.

## Razonamiento de `.env`

Actualmente la configuración de la base de datos y la clave secreta están definidas directamente en `Codigo fuente/app.py`:

- `MYSQL_HOST`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DB`
- `secret_key`

Esto no es recomendable porque:
- expone credenciales sensibles en el repositorio si se comparte el código.
- dificulta el despliegue en diferentes entornos (local, desarrollo, producción).
- hace más difícil rotar contraseñas o cambiar datos sin editar el código.

### Uso recomendado de `.env`

Se recomienda mover la configuración sensible a un archivo `.env` que no se suba al control de versiones.
Por ejemplo:

```
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DB=TFG_DAW
SECRET_KEY=una_clave_segura_generada_aleatoriamente
FLASK_ENV=development
```

A continuación, cargar estas variables en Flask usando `python-dotenv` o `os.environ`.

### Beneficios de `.env`
- Separación de código y configuración.
- Mayor seguridad de las credenciales.
- Despliegue más simple en distintas máquinas o servidores.
- Mejora de buenas prácticas para proyectos web.

## Cómo ejecutar

1. Crear y activar un entorno virtual Python.
2. Instalar dependencias necesarias (Flask, flask_mysqldb, python-dotenv si se usa).
3. Importar la base de datos desde `Bbdd/TFG_DAW.sql` en MySQL.
4. Ejecutar:

```bash
cd "Codigo fuente"
python app.py
```

5. Abrir el navegador en `http://127.0.0.1:5000/`.

## Recomendaciones para la siguiente fase

- Crear un archivo `requirements.txt` con todas las dependencias.
- Añadir `.env` y usar `python-dotenv` para cargar variables de entorno.
- Cambiar `app.secret_key` para leer `SECRET_KEY` desde el entorno.
- Añadir pruebas unitarias y de integración.
