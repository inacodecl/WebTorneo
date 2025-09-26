from flask import render_template, request, jsonify, Blueprint, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename
import requests
import os
import uuid

inscripcion_bp = Blueprint('inscripcion', __name__)

# === Config de subidas (segura y absoluta) ===
def _upload_dir():
    base = os.path.join(current_app.root_path, 'static', 'avatars')
    os.makedirs(base, exist_ok=True)
    return base

EXTENSIONES_PERMITIDAS = {'png', 'jpg', 'jpeg', 'jfif', 'webp'}

def _ext_ok(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in EXTENSIONES_PERMITIDAS

@inscripcion_bp.route('/')
def index():
    return render_template('auth/inscripcion.html')

@inscripcion_bp.route('/buscar_usuario')
def buscar_usuario():
    term = request.args.get('term', '')
    headers = {'Clave-De-Autenticacion': current_app.config['TOKEN']}
    try:
        url_base_api = current_app.config["URL_BASE_API"].rstrip('/')
        r = requests.get(
            f'{url_base_api}/integrantes/sugerencias-correo',
            params={'term': term},
            headers=headers,
            timeout=10
        )
        r.raise_for_status()
        resultados = r.json()
    except Exception:
        resultados = []
    return jsonify(resultados)

@inscripcion_bp.route('/inscripcion', methods=['POST'])
def inscribir_equipo():
    nombre_equipo = request.form.get('nombreEquipo')
    pwd_equipo    = request.form.get('pwd_equipo')
    avatar_file   = request.files.get('avatar')  # <-- input del form debe ser name="avatar"

    # Validaciones básicas
    if not nombre_equipo or not pwd_equipo:
        flash("Todos los campos son obligatorios", "danger")
        return redirect(url_for('inscripcion.index'))

    # === Guardar avatar en /static/avatars/ y generar URL servible ===
    avatar_url = "SinAvatar"
    if avatar_file and avatar_file.filename:
        if not _ext_ok(avatar_file.filename):
            flash("Formato de imagen no permitido (usa png, jpg, jpeg, jfif o webp).", "danger")
            return redirect(url_for('inscripcion.index'))

        ext = '.' + avatar_file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(f"{uuid.uuid4().hex}{ext}")
        save_path = os.path.join(_upload_dir(), filename)

        try:
            avatar_file.save(save_path)
        except Exception as e:
            flash(f"Error al guardar el avatar: {e}", "danger")
            return redirect(url_for('inscripcion.index'))

        # ⚠️ URL pública que sí funciona en navegador
        avatar_url = f"/static/avatars/{filename}"

    # === Validar integrantes ===
    integrantes = request.form.getlist("correos[]")
    if len(integrantes) != 3:
        flash("Debe haber exactamente 3 integrantes en el equipo", "danger")
        return redirect(url_for('inscripcion.index'))

    for correo in integrantes:
        if not correo.endswith('@inacapmail.cl'):
            flash(f'El correo {correo} no es institucional. Solo @inacapmail.cl', 'danger')
            return redirect(url_for('inscripcion.index'))

    # === Payload a la API ===
    equipo_data = {
        'nombre_equipo': nombre_equipo,
        'pwd': pwd_equipo,
        'avatar': avatar_url  # ahora guarda /static/avatars/<archivo>
    }

    try:
        headers = {'Clave-De-Autenticacion': current_app.config['TOKEN']}
        url_base_api = current_app.config["URL_BASE_API"].rstrip('/')
        api_url = f'{url_base_api}/equipos'

        resp = requests.post(api_url, json=equipo_data, headers=headers, timeout=10)
        if resp.status_code == 201:
            equipo_id = resp.json().get('id_equipo')

            # Asignar integrantes (el primero es capitán)
            for i, correo in enumerate(integrantes):
                rol_id = 1 if i == 0 else 2
                asignar_data = {
                    'correo': correo,
                    'equipo_id': equipo_id,
                    'rol_id': rol_id
                }
                api_url_integrante = f'{url_base_api}/asignar-equipo'
                r2 = requests.post(api_url_integrante, json=asignar_data, headers=headers, timeout=10)
                if r2.status_code != 200:
                    msg = r2.json().get("error", "Error desconocido")
                    flash(f'Error al asignar {correo}: {msg}', 'danger')
                    return redirect(url_for('inscripcion.index'))

            flash("Equipo inscrito y miembros asignados correctamente", "success")
            return redirect(url_for('inscripcion.index'))

        else:
            try:
                detalle = resp.json()
            except Exception:
                detalle = {'status': resp.status_code, 'text': resp.text[:200]}
            flash(f"Error al inscribir el equipo en la API: {detalle}", "danger")
            return redirect(url_for('inscripcion.index'))

    except requests.RequestException as e:
        flash(f"Error al conectar con la API: {e}", "danger")
        return redirect(url_for('inscripcion.index'))
