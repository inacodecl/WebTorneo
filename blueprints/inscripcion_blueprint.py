from flask import render_template, request, jsonify, Blueprint, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename
import requests
import os
import uuid

inscripcion_bp = Blueprint('inscripcion', __name__)

# Carpeta donde se guardan temporalmente los avatares
UPLOAD_FOLDER = './static/avatars'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

extensiones_permitidas = ['png', 'jpg', 'jpeg', 'jfif']

def comprobar_extension(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in extensiones_permitidas
@inscripcion_bp.route('/')
def index():
    return render_template('auth/inscripcion.html')

@inscripcion_bp.route('/buscar_usuario')
def buscar_usuario():
    term = request.args.get('term', '')
    headers = {'Clave-De-Autenticacion': current_app.config['TOKEN']}
    try:
        url_base_api = current_app.config["URL_BASE_API"]
        response = requests.get(f'{url_base_api}/integrantes/sugerencias-correo', params={'term': term}, headers=headers)
        resultados = response.json()
    except Exception as e:
        resultados = []

    return jsonify(resultados)

@inscripcion_bp.route('/inscripcion', methods=['POST'])
def inscribir_equipo():
    nombre_equipo = request.form.get('nombreEquipo')
    pwd_equipo = request.form.get('pwd_equipo')
    avatar = request.files.get('avatar')

    if not nombre_equipo or not pwd_equipo:
        flash("Todos los campos son obligatorios", "danger")
        return redirect(url_for('inscripcion.index'))  # Redirigir al formulario

    # Guardar avatar en /static/avatars/
    avatar_url = "SinAvatar"
    if avatar and comprobar_extension(avatar.filename):
        ext = avatar.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filename = secure_filename(filename)
        
        avatar_path = os.path.join(UPLOAD_FOLDER, filename)
        avatar.save(avatar_path)

        avatar_url = f'avatars/{filename}'

    # Validar los integrantes
    integrantes = request.form.getlist("correos[]")
    if len(integrantes) != 3:
        flash("Debe haber exactamente 3 integrantes en el equipo", "danger")
        return redirect(url_for('inscripcion.index'))  # Redirigir al formulario

    # Validar correos institucionales
    for correo in integrantes:
        if not correo.endswith('@inacapmail.cl'):
            flash(f'El correo {correo} no es institucional. Solo se pueden asignar correos institucionales (@inacapmail.cl)', 'danger')
            return redirect(url_for('inscripcion.index'))

    # Datos que se enviarán a la API para crear el equipo
    equipo_data = {
        'nombre_equipo': nombre_equipo,
        'pwd': pwd_equipo,
        'avatar': avatar_url
    }

    
    try:
        # Crear el equipo en la API de Node.js
        headers = {'Clave-De-Autenticacion': current_app.config['TOKEN']}
        url_base_api = current_app.config["URL_BASE_API"]
        api_url = f'{url_base_api}/equipos'
        response = requests.post(api_url, json=equipo_data, headers=headers)

        if response.status_code == 201:
            equipo_id = response.json().get('id_equipo')

            # Asignar integrantes al equipo
            for correo in integrantes:
                rol_id = 2  # Asumimos que el rol por defecto es "Integrante"
                if correo == integrantes[0]:  # El primer integrante es el capitán
                    rol_id = 1
                asignar_data = {
                    'correo': correo,
                    'equipo_id': equipo_id,
                    'rol_id': rol_id
                }

                api_url_integrante = f'{url_base_api}/asignar-equipo'
                response_integrante = requests.post(api_url_integrante, json=asignar_data, headers=headers)

                if response_integrante.status_code != 200:
                    flash(f'Error al asignar el integrante con correo {correo}: {response_integrante.json().get("error")}', 'danger')
                    return redirect(url_for('inscripcion.index'))

            flash("Equipo inscrito y miembros asignados correctamente", "success")
            return redirect(url_for('inscripcion.index'))  # Redirigir al índice

        else:
            flash("Error al inscribir el equipo en la API", "danger")
            return redirect(url_for('inscripcion.index'))

    except Exception as e:
        flash(f"Error al conectar con la API: {str(e)}", "danger")
        return redirect(url_for('inscripcion.index')) 