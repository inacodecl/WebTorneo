from flask import Blueprint, current_app, jsonify, request, session
import requests

ranking_bp = Blueprint('ranking', __name__, url_prefix='/ranking')

def _base(): 
    return current_app.config.get("URL_BASE_API", "").rstrip("/")

def _headers():
    return {"Clave-De-Autenticacion": current_app.config.get("TOKEN", "")}

@ranking_bp.route('/leaderboard', methods=['GET'])
def leaderboard():
    url_base = _base()
    headers = _headers()

    equipo_id = session.get('equipo_id') or request.args.get('equipo_id', type=int)

    if not equipo_id:
        return jsonify({"error": "No hay equipo_id en sesión"}), 400

    try:
        resultados = requests.get(f"{url_base}/resultados_torneo", headers=headers).json()
        equipos = requests.get(f"{url_base}/equipos", headers=headers).json()
    except Exception as e:
        return jsonify({"error": "Fallo al conectar con la API", "detail": str(e)}), 502

    # torneo_id actual en sesión
    torneo_id = request.args.get('torneo_id', type=int)

    if not torneo_id:
        # Detectar el torneo más reciente en el que el equipo participó
        recientes = []

        for r in resultados:
            try:
                if int(r.get('equipo_id', 0)) == int(equipo_id):
                    recientes.append(r)
            except Exception:
                continue

        recientes.sort(key=lambda x: x.get('torneo_id', 0), reverse=True)
        torneo_id = recientes[0]['torneo_id'] if recientes else None

    if not torneo_id:
        return jsonify({"items": [], "torneo_id": None, "equipo_id": equipo_id, "mi_posicion": None})

    # Filtrar resultados por torneo_id   
    ranking = []

    for r in resultados:
        if r.get('torneo_id') == torneo_id:
            ranking.append(r)

    # Ordenar por posición (o puntaje descendente como fallback)
    for r in ranking:
        r['pos'] = r.get('posicion') or r.get('Posicion')
        r['pts'] = r.get('puntaje') or r.get('Puntaje')
        r['tiempo'] = r.get('media_tiempo') or r.get('Media_Tiempo') or '00:00:00'

    ranking.sort(key=lambda x: (x['pos'] is None, x['pos'] if x['pos'] is not None else -x['pts']), reverse=False)

    # Añadir nombre/avatar
    eq_map = {}

    for e in equipos:
        codigo = e.get('CodigoEquipo')
        if codigo is not None:
            eq_map[codigo] = e

    for r in ranking:
        e_info = eq_map.get(r['equipo_id']) or {}
        r['nombre_equipo'] = e_info.get('nombre_equipo') or e_info.get('NombreEquipo') or f"Equipo {r['equipo_id']}"
        r['avatar'] = e_info.get('avatar') or e_info.get('LogoEquipo') or None
        r['posicion'] = r['pos']
        r['puntaje'] = r['pts']
        r['media_tiempo'] = r['tiempo']

    # Detectar posición propia
    mi = None
    for r in ranking:
        try:
            if int(r.get('equipo_id')) == int(equipo_id):
                mi = r
                break
        except Exception:
            continue

    return jsonify({
        "torneo_id": torneo_id,
        "equipo_id": equipo_id,
        "items": ranking,
        "mi_posicion": mi.get('pos') if mi else None
    })