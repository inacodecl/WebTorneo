from flask import render_template, request, jsonify, Blueprint, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename
import requests
import os

inscripcion_bp = Blueprint('inscripcion', __name__)

@inscripcion_bp.route('/')
def index():
    return render_template('auth/inscripcion.html')

@inscripcion_bp.route('/buscar_usuario')
def buscar_usuario():
    term = request.args.get('term', '').strip()
    headers = {'Clave-De-Autenticacion': current_app.config['TOKEN']}
    url_base_api = current_app.config["URL_BASE_API"].rstrip('/')

    try:
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
    # === Campos del form ===
    nombre_equipo = (request.form.get('nombreEquipo') or '').strip()
    pwd_equipo    = (request.form.get('pwd_equipo') or '').strip()
    avatar_file   = request.files.get('avatar')  # <input name="avatar">
    integrantes   = [c.strip() for c in request.form.getlist("correos[]") if c.strip()]

    # Validaciones básicas
    if not nombre_equipo or not pwd_equipo:
        flash("Todos los campos son obligatorios", "danger")
        return redirect(url_for('inscripcion.index'))

    if len(integrantes) != 3:
        flash("Debe haber exactamente 3 integrantes en el equipo", "danger")
        return redirect(url_for('inscripcion.index'))

    for correo in integrantes:
        if not correo.endswith('@inacapmail.cl'):
            flash(f'El correo {correo} no es institucional. Solo @inacapmail.cl', 'danger')
            return redirect(url_for('inscripcion.index'))

    # === Armar request a la API (multipart/form-data) ===
    url_base_api = current_app.config["URL_BASE_API"].rstrip('/')
    headers = {'Clave-De-Autenticacion': current_app.config['TOKEN']}

    data = {
        'nombre_equipo': nombre_equipo,
        'pwd': pwd_equipo,
        'estado': '1',  # activo; tu SQL lista con WHERE estado=1
    }

    files = None
    if avatar_file and avatar_file.filename:
        # NO pongas Content-Type manual: requests lo define al usar 'files'
        filename = secure_filename(avatar_file.filename)
        files = {'avatar': (filename, avatar_file.stream, avatar_file.mimetype)}

    try:
        resp = requests.post(
            f'{url_base_api}/equipos',
            headers=headers,
            data=data,     # <- clave: data + files => multipart
            files=files,   # <- aquí viaja la imagen a la API (multer)
            timeout=20
        )
    except requests.RequestException as e:
        flash(f"Error al conectar con la API: {e}", "danger")
        return redirect(url_for('inscripcion.index'))

    if resp.status_code != 201:
        try:
            detalle = resp.json()
        except Exception:
            detalle = {'status': resp.status_code, 'text': resp.text[:200]}
        flash(f"Error al inscribir el equipo en la API: {detalle}", "danger")
        return redirect(url_for('inscripcion.index'))

    equipo_id = resp.json().get('id_equipo')

    # === Asignar integrantes (el primero capitán) ===
    try:
        for i, correo in enumerate(integrantes):
            rol_id = 1 if i == 0 else 2
            asignar_data = {'correo': correo, 'equipo_id': equipo_id, 'rol_id': rol_id}
            r2 = requests.post(
                f'{url_base_api}/asignar-equipo',
                headers=headers,
                json=asignar_data,
                timeout=10
            )
            if r2.status_code != 200:
                try:
                    msg = r2.json().get("error", "Error desconocido")
                except Exception:
                    msg = r2.text[:200]
                flash(f'Error al asignar {correo}: {msg}', 'danger')
                return redirect(url_for('inscripcion.index'))
    except requests.RequestException as e:
        flash(f"Error al asignar integrantes: {e}", "danger")
        return redirect(url_for('inscripcion.index'))

    flash("Equipo inscrito y miembros asignados correctamente", "success")
    return redirect(url_for('inscripcion.index'))
