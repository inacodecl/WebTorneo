from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import requests

registro_bp = Blueprint('registro', __name__, url_prefix='/registros')

@registro_bp.route('/', methods=['GET', 'POST'])
def registro():
    url_base_api = current_app.config["URL_BASE_API"]
    headers = {'Clave-De-Autenticacion': current_app.config['TOKEN']}
    api_url = f'{url_base_api}/registros'

    # --- EDITAR ---
    registro_editar = None
    editar_id = request.args.get('editar')
    if editar_id is not None and editar_id != '':
        try:
            response = requests.get(f"{api_url}/{editar_id}", headers=headers)
            if response.status_code == 200:
                registro_editar = response.json()
            else:
                data = response.json()
                error_msg = data.get('error') or data.get('mensaje') or "Registro no encontrado"
                flash(error_msg, "danger")
        except Exception as e:
            flash(f"Error al conectar con la API: {str(e)}", "danger")

    # --- CREAR O ACTUALIZAR ---
    if request.method == 'POST':
        id_registro = request.form.get('id_registro')
        torneo_id = request.form.get('torneo_id')
        equipo_id = request.form.get('equipo_id')

        if not torneo_id or not equipo_id:
            flash('Faltan datos obligatorios', 'danger')
            return redirect(url_for('registro.registro'))

        registro_data = {
            'torneo_id': int(torneo_id),
            'equipo_id': int(equipo_id)
        }

        try:
            if id_registro:  # Actualizar
                response = requests.put(f"{api_url}/{id_registro}", json=registro_data, headers=headers)
                data = response.json()
                if response.status_code == 200:
                    flash(data.get('mensaje', "Registro actualizado con éxito"), "success")
                else:
                    error_msg = data.get('error') or data.get('mensaje') or "Error al actualizar el registro"
                    flash(error_msg, "danger")
            else:  # Crear
                response = requests.post(api_url, json=registro_data, headers=headers)
                data = response.json()
                if response.status_code == 201:
                    flash(data.get('mensaje', 'Registro creado correctamente'), 'success')
                else:
                    error_msg = data.get('error') or data.get('mensaje') or 'Error desconocido'
                    flash(error_msg, 'danger')
        except Exception as e:
            flash(f'Error al conectar con la API: {str(e)}', 'danger')

        return redirect(url_for('registro.registro'))

    # --- LISTAR REGISTROS ---
    try:
        response = requests.get(api_url, headers=headers)
        registros = response.json() if response.status_code == 200 else []
    except Exception as e:
        flash(f"Error al conectar con la API: {str(e)}", "danger")
        registros = []

    # Puedes cargar aquí equipos y torneos para los selects
    try:
        equipos = requests.get(f"{url_base_api}/equipos", headers=headers).json()
    except Exception:
        equipos = []
    try:
        torneos = requests.get(f"{url_base_api}/torneos", headers=headers).json()
    except Exception:
        torneos = []

    return render_template(
        'registro.html',
        registros=registros,
        registro_editar=registro_editar,
        equipos=equipos,
        torneos=torneos
    )