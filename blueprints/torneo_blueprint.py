from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
import requests

torneo_bp = Blueprint('torneo', __name__, url_prefix='/torneos')

def solo_admin(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('rol') != 'admin':
            flash("Acceso solo para administradores.", "danger")
            return redirect(url_for('login.formulario_login'))
        return f(*args, **kwargs)
    return decorated_function

@torneo_bp.route('/', methods=['GET', 'POST'])
@solo_admin
def torneo():
    url_base_api = current_app.config["URL_BASE_API"]
    headers = {'Clave-De-Autenticacion': current_app.config['TOKEN']}

    # --- CREAR O ACTUALIZAR ---
    if request.method == 'POST':
        id_torneo = request.form.get('id_torneo')
        nombre = request.form.get('nombre')
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_termino = request.form.get('fecha_termino')
        estado = request.form.get('estado')

        if not nombre or not fecha_inicio or not fecha_termino or estado not in ['0', '1', 0, 1]:
            flash('Faltan datos obligatorios', 'danger')
            return redirect(url_for('torneo.torneo'))

        torneo_data = {
            'nombre': nombre,
            'fecha_inicio': fecha_inicio,
            'fecha_termino': fecha_termino,
            'estado': int(estado)
        }

        try:
            if id_torneo:  # Actualizar
                response = requests.put(f'{url_base_api}/torneos/{id_torneo}', json=torneo_data, headers=headers)
                data = response.json()
                if response.status_code == 200:
                    flash(data.get('mensaje', 'Torneo actualizado correctamente'), "success")
                else:
                    error_msg = data.get('error') or data.get('mensaje') or 'Error desconocido'
                    flash(error_msg, "danger")
            else:  # Crear
                response = requests.post(f"{url_base_api}/torneos", json=torneo_data, headers=headers)
                data = response.json()
                if response.status_code == 201:
                    flash(data.get('mensaje', 'Torneo creado correctamente'), 'success')
                else:
                    error_msg = data.get('error') or data.get('mensaje') or 'Error desconocido'
                    flash(error_msg, 'danger')
        except Exception as e:
            flash(f'Error al conectar con la API: {str(e)}', 'danger')

        return redirect(url_for('torneo.torneo'))

    # --- LISTAR TORNEOS ---
    try:
        response = requests.get(f"{url_base_api}/torneos", headers=headers)
        torneos = response.json() if response.status_code == 200 else []
    except Exception as e:
        flash(f"Error al conectar con la API: {str(e)}", "danger")
        torneos = []

    # --- EDITAR (cargar datos en el form) ---
    torneo_editar = None
    editar_id = request.args.get('editar')
    if editar_id:
        try:
            response = requests.get(f'{url_base_api}/torneos/{editar_id}', headers=headers)
            if response.status_code == 200:
                torneo_editar = response.json()
            else:
                data = response.json()
                error_msg = data.get('error') or data.get('mensaje') or 'Error desconocido'
                flash(error_msg, "danger")
        except Exception as e:
            flash(f"Error al conectar con la API: {str(e)}", "danger")

    return render_template(
        'dashboard_admin/torneo.html',
        torneos=torneos,
        torneo_editar=torneo_editar
    )