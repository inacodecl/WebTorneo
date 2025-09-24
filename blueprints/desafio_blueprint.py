from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, session
import requests

desafio_bp = Blueprint('desafio', __name__)

def solo_admin(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('rol') != 'admin':
            flash("Acceso solo para administradores.", "danger")
            return redirect(url_for('login.formulario_login'))
        return f(*args, **kwargs)
    return decorated_function

@desafio_bp.route('/', methods=['GET', 'POST'])
@solo_admin
def desafio():
    url_base_api = current_app.config["URL_BASE_API"]
    headers = {'Clave-De-Autenticacion': current_app.config['TOKEN']}

    # --- CREAR O ACTUALIZAR ---
    if request.method == 'POST':
        id_desafio = request.form.get('id_desafio')
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        fase_id = request.form.get('fase_id')
        torneo_id = request.form.get('torneo_id')

        if not titulo or not descripcion or not fase_id or not torneo_id:
            flash('Faltan datos obligatorios', 'danger')
            return redirect(url_for('desafio.desafio'))

        desafio_data = {
            'titulo': titulo,
            'descripcion': descripcion,
            'fase_id': int(fase_id),
            'torneo_id': int(torneo_id)
        }

        try:
            if id_desafio:  # Actualizar
                response = requests.put(f'{url_base_api}/desafios/{id_desafio}', json=desafio_data, headers=headers)
                data = response.json()
                if response.status_code == 200:
                    flash(data.get('message', 'Desafío actualizado correctamente'), "success")
                else:
                    error_msg = data.get('error') or data.get('message') or 'Error desconocido'
                    flash(error_msg, "danger")
            else:  # Crear
                response = requests.post(f"{url_base_api}/desafios", json=desafio_data, headers=headers)
                data = response.json()
                if response.status_code == 201:
                    flash(data.get('message', 'Desafío creado correctamente'), 'success')
                else:
                    error_msg = data.get('error') or data.get('message') or 'Error desconocido'
                    flash(error_msg, 'danger')
        except Exception as e:
            flash(f'Error al conectar con la API: {str(e)}', 'danger')

        return redirect(url_for('desafio.desafio'))

    # --- LISTAR DESAFÍOS ---
    try:
        response = requests.get(f"{url_base_api}/desafios", headers=headers)
        desafios = response.json() if response.status_code == 200 else []
    except Exception as e:
        flash(f"Error al conectar con la API: {str(e)}", "danger")
        desafios = []

    # --- LISTAR TORNEOS Y FASES PARA EL FORMULARIO ---
    try:
        torneos = requests.get(f"{url_base_api}/torneos", headers=headers).json()
        fases = requests.get(f"{url_base_api}/fases", headers=headers).json()
    except Exception as e:
        torneos, fases = [], []

    # --- EDITAR (cargar datos en el form) ---
    desafio_editar = None
    editar_id = request.args.get('editar')
    if editar_id:
        try:
            response = requests.get(f'{url_base_api}/desafios/{editar_id}', headers=headers)
            if response.status_code == 200:
                desafio_editar = response.json()
            else:
                data = response.json()
                error_msg = data.get('error') or data.get('message') or 'Error desconocido'
                flash(error_msg, "danger")
        except Exception as e:
            flash(f"Error al conectar con la API: {str(e)}", "danger")

    return render_template(
        'dashboard_admin/desafio.html',
        desafios=desafios,
        desafio_editar=desafio_editar,
        torneos=torneos,
        fases=fases
    )