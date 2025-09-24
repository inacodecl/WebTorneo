from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from datetime import datetime
import requests

resultado_fase_bp = Blueprint('resultado_fase', __name__, url_prefix='/resultados_fase')

@resultado_fase_bp.route('/', methods=['GET', 'POST'])
def resultado_fase():
    url_base_api = current_app.config["URL_BASE_API"]
    headers = {'Clave-De-Autenticacion': current_app.config['TOKEN']}
    api_url = f'{url_base_api}/resultados_fase'

    # --- CREAR O ACTUALIZAR ---
    resultado_editar = None
    editar_id = request.args.get('editar')
    if editar_id:
        try:
            response = requests.get(f"{api_url}/{editar_id}", headers=headers)
            if response.status_code == 200:
                resultado_editar = response.json()
            else:
                data = response.json()
                error_msg = data.get('error') or data.get('message') or "Resultado no encontrado"
                flash(error_msg, "danger")
        except Exception as e:
            flash(f"Error al conectar con la API: {str(e)}", "danger")

    if request.method == 'POST':
        id_resultado = request.form.get('id_resultado')
        posicion = request.form.get('posicion')
        puntaje = request.form.get('puntaje')
        media_tiempo = request.form.get('media_tiempo')
        equipo_id = request.form.get('equipo_id')
        fase_id = request.form.get('fase_id')

        if not posicion or puntaje is None or not media_tiempo or equipo_id is None or fase_id is None:
            flash('Faltan datos obligatorios', 'danger')
            return redirect(url_for('resultado_fase.resultado_fase'))

        try:
            media_tiempo = datetime.strptime(media_tiempo, '%H:%M:%S').time().strftime('%H:%M:%S')
        except ValueError:
            flash('Formato de media_tiempo incorrecto. Use HH:MM:SS', 'danger')
            return redirect(url_for('resultado_fase.resultado_fase'))

        resultado_data = {
            'posicion': int(posicion),
            'puntaje': int(puntaje),
            'media_tiempo': media_tiempo,
            'equipo_id': int(equipo_id),
            'fase_id': int(fase_id)
        }

        try:
            if id_resultado:  # Actualizar
                response = requests.put(f"{api_url}/{id_resultado}", json=resultado_data, headers=headers)
                data = response.json()
                if response.status_code == 200:
                    flash(data.get('message', "Resultado actualizado con éxito"), "success")
                else:
                    error_msg = data.get('error') or data.get('message') or "Error al actualizar el resultado"
                    flash(error_msg, "danger")
            else:  # Crear
                response = requests.post(api_url, json=resultado_data, headers=headers)
                data = response.json()
                if response.status_code == 201:
                    flash(data.get('message', 'Resultado creado correctamente'), 'success')
                else:
                    error_msg = data.get('error') or data.get('message') or 'Error desconocido'
                    flash(error_msg, 'danger')
        except Exception as e:
            flash(f'Error al conectar con la API: {str(e)}', 'danger')

        return redirect(url_for('resultado_fase.resultado_fase'))

    # --- LISTAR RESULTADOS ---
    try:
        response = requests.get(api_url, headers=headers)
        resultados = response.json() if response.status_code == 200 else []
    except Exception as e:
        flash(f"Error al conectar con la API: {str(e)}", "danger")
        resultados = []

    # Puedes cargar aquí equipos y fases si quieres selects dinámicos
    try:
        equipos = requests.get(f"{url_base_api}/equipos", headers=headers).json()
    except Exception:
        equipos = []
    try:
        fases = requests.get(f"{url_base_api}/fases", headers=headers).json()
    except Exception:
        fases = []

    return render_template(
        'resultado_fase.html',
        resultados=resultados,
        resultado_editar=resultado_editar,
        equipos=equipos,
        fases=fases
    )