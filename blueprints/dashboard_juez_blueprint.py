from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
import requests

dashboard_juez_bp = Blueprint('dashboard_juez_bp', __name__)

@dashboard_juez_bp.route('/dashboard/juez', methods=['GET', 'POST'])
def dashboard_juez():

    if session.get('rol') != 'juez':
        flash("Acceso solo para jueces.", "danger")
        return redirect(url_for('login.formulario_login'))
    
    clave = current_app.config['TOKEN']
    headers = {'Clave-De-Autenticacion': clave}
    url_base_api = current_app.config["URL_BASE_API"]

    # Obtener torneos
    torneos = requests.get(f"{url_base_api}/torneos", headers=headers).json()

    torneo_id = request.args.get('torneo_id')
    desafio_id = request.args.get('desafio_id')

    desafios = []
    envios = []

    if torneo_id:
        # Obtener desafíos del torneo seleccionado
        desafios_api = requests.get(f"{url_base_api}/desafios", headers=headers).json()

        for d in desafios_api:
            if str(d.get('torneo_id')) == str(torneo_id):
                desafios.append(d)

    if desafio_id:
        # Obtener respuestas de ese desafío
        respuestas = requests.get(f"{url_base_api}/respuestas", headers=headers).json()

        for r in respuestas:
            if str(r.get('desafio_id')) == str(desafio_id):
                envios.append(r)

        # Obtener equipos para hacer el join y mostrar el nombre
        equipos = requests.get(f"{url_base_api}/equipos", headers=headers).json()
        equipos_dict = {}
        
        for e in equipos:
            cod = e.get('CodigoEquipo')
            nombre = e.get('NombreEquipo')
            if cod is not None:
                equipos_dict[cod] = nombre

        for envio in envios:
            envio['nombre_equipo'] = equipos_dict.get(envio['equipo_id'], 'Desconocido')

    return render_template(
        'dashboard_jueces/dashboard_juez.html',
        torneos=torneos,
        desafios=desafios,
        envios=envios,
        torneo_id=torneo_id,
        desafio_id=desafio_id
    )

@dashboard_juez_bp.route('/dashboard/juez/comentar/<int:id_respuesta_codigo>', methods=['POST'])
def comentar_envio(id_respuesta_codigo):
    clave = current_app.config['TOKEN']
    headers = {'Clave-De-Autenticacion': clave}
    url_base_api = current_app.config["URL_BASE_API"]

    comentario = request.form.get('comentario')
    estado = request.form.get('estado')  # "aprobado" o "rechazado"

    # Actualizar estado y comentario en la API
    data = {
        "comentario": comentario,
        "estado": estado
    }
    r = requests.put(f"{url_base_api}/respuestas/{id_respuesta_codigo}/estado", json=data, headers=headers)
    if r.status_code == 200:
        flash("Envío calificado correctamente", "success")
    else:
        flash("Error al calificar el envío", "danger")
    # Redirige manteniendo los filtros
    torneo_id = request.args.get('torneo_id')
    desafio_id = request.args.get('desafio_id')
    return redirect(url_for('dashboard_juez_bp.dashboard_juez', torneo_id=torneo_id, desafio_id=desafio_id))