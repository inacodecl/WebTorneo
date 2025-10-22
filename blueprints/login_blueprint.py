# blueprints/login_blueprint.py
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, current_app, flash
import requests

login_bp = Blueprint('login', __name__)

@login_bp.route('/')
def formulario_login():
    return render_template('auth/login.html')

# Ruta para hacer login
@login_bp.route('/login', methods=['POST'])
def login():
    correo = request.form.get("nombre_equipo")
    pwd = request.form.get("pwd_equipo")
    next_url = request.args.get("next")  # opcional

    # --- Logins rápidos de admin y juez (sin API) ---
    if correo == "admin@admin.com" and pwd == "admin123":
        session.clear()
        session['rol'] = 'admin'
        session['correo'] = correo
        return redirect(next_url or url_for('dashboard_admin_bp.dashboard_admin'))

    if correo == "juez@juez.com" and pwd == "juez123":
        session.clear()
        session['rol'] = 'juez'
        session['correo'] = correo
        return redirect(next_url or url_for('juez.dashboard'))

    # --- Login normal contra la API (equipo) ---
    datos_login = {
        "nombre_equipo": correo,
        "pwd": pwd  # la API espera "pwd"
    }

    url_base_api = current_app.config.get("URL_BASE_API", "http://localhost:4000/api")

    try:
        response = requests.post(f'{url_base_api}/equipos/login', json=datos_login, timeout=10)
    except requests.RequestException as e:
        flash(f"No se pudo contactar a la API: {e}", "danger")
        return render_template('auth/login.html')

    # intenta parsear JSON con manejo de errores
    try:
        data = response.json()
    except ValueError:
        flash("Respuesta no válida de la API de login.", "danger")
        return render_template('auth/login.html')

    if response.status_code == 200 and 'equipo' in data:
        equipo = data['equipo']
        session.clear()
        session['rol'] = 'equipo'                 # 👈 importante para proteger vistas
        session['equipo_id'] = equipo.get('id_equipo')
        session['nombre_equipo'] = equipo.get('nombre_equipo')
        return redirect(next_url or url_for('dashboard_equipo_bp.dashboard_equipo'))

    # Error de login
    error = data.get('error') or data.get('message') or "Nombre de equipo o contraseña incorrectos"
    flash(error, "danger")
    return render_template('auth/login.html')

@login_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login.formulario_login'))

# Ruta de prueba (opcional)
@login_bp.route('/prueba')
def prueba():
    return render_template('dashboard_equipos/temporal_equipos.html')
