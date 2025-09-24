# controllers/integrante_controller.py
import requests
from flask import Blueprint, request, jsonify, flash, redirect, url_for, render_template
from werkzeug.exceptions import BadRequest

integrante_bp = Blueprint('integrante', __name__)

# Asignar un integrante a un equipo
@integrante_bp.route('/asignar', methods=['GET', 'POST' ])
def asignar_integrante():
    if request.method == 'POST':
        # Obtener los datos del formulario
        correo = request.form.get('correo')
        equipo_id = int(request.form.get('equipo_id'))
        rol_id = int(request.form.get('rol_id'))

        # # Validar que todos los datos estén presentes
        if not correo or not equipo_id or not rol_id:
            flash('Faltan datos obligatorios', 'danger')
            return redirect(url_for('integrante.asignar_integrante'))

        # Validar que el correo sea institucional
        if not correo.endswith('@inacapmail.cl'):
            flash('Solo se pueden asignar correos institucionales (@inacapmail.cl)', 'danger')
            return redirect(url_for('integrante.asignar_integrante'))

        # Preparar los datos para enviar a la API de Express
        data = {
            'correo': correo,
            'equipo_id': equipo_id,
            'rol_id': rol_id
        }

        try:
            api_url = 'http://localhost:4000/api/integrantes/asignar-equipo'  # Dirección de tu API en Express
            response = requests.post(api_url, json=data)

            if response.status_code == 200:
                flash('Integrante asignado correctamente', 'success')
                return redirect(url_for('integrante.lista_integrantes'))
            else:
                flash(f'Error: {response.json().get("error")}', 'danger')
                return redirect(url_for('integrante.asignar_integrante'))

        except Exception as e:
            flash(f'Error al conectar con la API: {str(e)}', 'danger')
            return redirect(url_for('integrante.asignar_integrante'))

    return render_template('asignar_integrante.html')

# Ruta para listar todos los equipos
@integrante_bp.route('/', methods=['GET'])
def listar_integrantes():
    try:
        api_url = 'http://localhost:4000/api/integrantes/listar-integrantes' 
        response = requests.get(api_url)

        if response.status_code == 200:
            integrantes = response.json()  # Obtenemos los resultados
            return render_template('listar_equipos_integrantes.html', integrantes=integrantes)
        else:
            flash("Error al obtener los desafíos", "danger")
            return render_template('listar_equipos_integrantes.html', integrantes=[])
    except Exception as e:
        flash(f"Error al conectar con la API: {str(e)}", "danger")
        return render_template('listar_equipos_integrantes.html', integrantes=[])