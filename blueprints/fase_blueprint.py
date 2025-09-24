from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, session
import requests

fase_bp = Blueprint('fase', __name__, url_prefix='/fases')

def solo_admin(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('rol') != 'admin':
            flash("Acceso solo para administradores.", "danger")
            return redirect(url_for('login.formulario_login'))
        return f(*args, **kwargs)
    return decorated_function

@fase_bp.route('/', methods=['GET', 'POST'])
@solo_admin
def fase():
    url_base_api = current_app.config["URL_BASE_API"]
    headers = {'Clave-De-Autenticacion': current_app.config['TOKEN']}

    # --- CREAR O ACTUALIZAR ---
    if request.method == 'POST':
        id_fase = request.form.get('id_fase')
        dificultad = request.form.get('dificultad')
        torneo_id = request.form.get('torneo_id')

        if not dificultad or not torneo_id:
            flash('Faltan datos obligatorios', 'danger')
            return redirect(url_for('fase.fase'))

        fase_data = {
            'dificultad': dificultad,
            'torneo_id': int(torneo_id)
        }

        try:
            if id_fase:  # Actualizar
                response = requests.put(f'{url_base_api}/fases/{id_fase}', json=fase_data, headers=headers)
                data = response.json()
                if response.status_code == 200:
                    flash(data.get('message', 'Fase actualizada correctamente'), "success")
                else:
                    error_msg = data.get('error') or data.get('message') or 'Error desconocido'
                    flash(error_msg, "danger")
            else:  # Crear
                response = requests.post(f"{url_base_api}/fases", json=fase_data, headers=headers)
                data = response.json()
                if response.status_code == 201:
                    flash(data.get('message', 'Fase creada correctamente'), 'success')
                else:
                    error_msg = data.get('error') or data.get('message') or 'Error desconocido'
                    flash(error_msg, 'danger')
        except Exception as e:
            flash(f'Error al conectar con la API: {str(e)}', 'danger')

        return redirect(url_for('fase.fase'))

    # --- LISTAR FASES ---
    try:
        response = requests.get(f"{url_base_api}/fases", headers=headers)
        fases = response.json() if response.status_code == 200 else []
    except Exception as e:
        flash(f"Error al conectar con la API: {str(e)}", "danger")
        fases = []

    # --- LISTAR TORNEOS PARA EL FORMULARIO ---
    try:
        torneos = requests.get(f"{url_base_api}/torneos", headers=headers).json()
    except Exception as e:
        torneos = []

    # --- EDITAR (cargar datos en el form) ---
    fase_editar = None
    editar_id = request.args.get('editar')
    if editar_id:
        try:
            response = requests.get(f'{url_base_api}/fases/{editar_id}', headers=headers)
            if response.status_code == 200:
                fase_editar = response.json()
            else:
                data = response.json()
                error_msg = data.get('error') or data.get('message') or 'Error desconocido'
                flash(error_msg, "danger")
        except Exception as e:
            flash(f"Error al conectar con la API: {str(e)}", "danger")

    return render_template(
        'dashboard_admin/fase.html',
        fases=fases,
        fase_editar=fase_editar,
        torneos=torneos
    )