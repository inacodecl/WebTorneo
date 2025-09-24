from flask import Blueprint, render_template, session, redirect, url_for, flash, current_app
import requests

dashboard_equipo_bp = Blueprint('dashboard_equipo_bp', __name__)

@dashboard_equipo_bp.route('/dashboard/equipo')
def dashboard_equipo():
    
    equipo_id = session.get('equipo_id')

    if not equipo_id:
        flash("Debes iniciar sesión primero.", "warning")
        return redirect(url_for('login.formulario_login'))

    clave = current_app.config['TOKEN']
    headers = {'Clave-De-Autenticacion': clave}
    url_base_api = current_app.config["URL_BASE_API"]

    # Equipos
    equipos = requests.get(f"{url_base_api}/equipos", headers=headers).json()

    try:
        equipo_id_int = int(equipo_id)
    except Exception:
        equipo_id_int = -1

    equipo = {}

    for e in equipos:
        try:
            if int(e.get('CodigoEquipo', -1)) == equipo_id_int:
                equipo = e
                break
        except (TypeError, ValueError):
            continue

    # Integrantes
    integrantes = requests.get(f"{url_base_api}/integrantes/listar-integrantes", headers=headers).json()
    integrantes_equipo = []

    for i in integrantes:
        if i.get('nombre_equipo') == equipo.get('NombreEquipo'):
            integrantes_equipo.append(i)

    # Registros del torneo
    registros = requests.get(f"{url_base_api}/registros", headers=headers).json()
    torneos_ids = []

    for r in registros:
        try:
            if int(r.get('equipo_id', -1)) == equipo_id_int:
                torneos_ids.append(r['torneo_id'])
        except Exception:
            continue

    torneos = []

    for torneo_id in torneos_ids:
        torneo = requests.get(f"{url_base_api}/torneos/{torneo_id}", headers=headers).json()
        torneos.append(torneo)

    # Desafíos
    desafios = []

    for torneo_id in torneos_ids:
        ds = requests.get(f"{url_base_api}/desafios", headers=headers).json()
        for d in ds:
            if d.get('torneo_id') == torneo_id:
                desafios.append(d)

    # Resultados
    resultados_torneo = requests.get(f"{url_base_api}/resultados_torneo", headers=headers).json()
    resultados_equipo = []

    for r in resultados_torneo:
        try:
            if int(r.get('equipo_id', -1)) == equipo_id_int:
                resultados_equipo.append(r)
        except Exception:
            continue
   

    equipo_data = {
        "nombre_equipo": equipo.get("NombreEquipo"),
        "avatar": equipo.get("LogoEquipo"),
        "integrantes": integrantes_equipo,
        "torneos": torneos,
        "desafios": desafios,
        "resultados": resultados_equipo
    }

    return render_template('dashboard_equipos/dashboard_equipo.html', equipo=equipo_data)