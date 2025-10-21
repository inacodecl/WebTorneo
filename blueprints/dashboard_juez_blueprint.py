from flask import Blueprint, render_template, request, redirect, url_for, flash
import requests

# Intentamos tomar config desde config.py, con fallback por si no está
try:
    from config import API_BASE, JWT_COOKIE_NAME
except Exception:
    API_BASE = "http://localhost:4000/api"
    JWT_COOKIE_NAME = "token"

juez_bp = Blueprint("juez", __name__, url_prefix="/juez")

def _headers():
    """Devuelve headers con token si existe. Si no usas JWT, vuelve {}."""
    tok = request.cookies.get(JWT_COOKIE_NAME)
    return {"Authorization": f"Bearer {tok}"} if tok else {}

@juez_bp.route("/", methods=["GET"])
def dashboard():
    # Filtros por querystring
    torneo_id  = request.args.get("torneo_id") or ""
    desafio_id = request.args.get("desafio_id") or ""

    # 1) Traer desafíos y torneos para los select
    try:
        r_desafios = requests.get(f"{API_BASE}/desafios", headers=_headers(), timeout=10)
        desafios = r_desafios.json() if r_desafios.ok else []
    except Exception:
        desafios = []

    try:
        r_torneos = requests.get(f"{API_BASE}/torneos", headers=_headers(), timeout=10)
        torneos = r_torneos.json() if r_torneos.ok else []
    except Exception:
        torneos = []

    # 2) Traer envíos (respuestas) y filtrar por desafío si corresponde
    try:
        r_envios = requests.get(f"{API_BASE}/respuestas", headers=_headers(), timeout=15)
        todos_envios = r_envios.json() if r_envios.ok else []
    except Exception:
        todos_envios = []

    envios = []
    for r in todos_envios:
        # campos típicos esperados: id_respuesta_codigo, equipo_id, desafio_id, archivo, fecha_envio...
        ok_desafio = (not desafio_id) or str(r.get("desafio_id")) == str(desafio_id)
        if ok_desafio:
            envios.append(r)

    # 3) Traer calificaciones guardadas (para mostrar junto a cada envío)
    califs = []
    params = {}
    if torneo_id:
        params["torneo_id"] = torneo_id
    if desafio_id:
        params["desafio_id"] = desafio_id

    try:
        r_calif = requests.get(f"{API_BASE}/juez", params=params, headers=_headers(), timeout=10)
        califs = r_calif.json() if r_calif.ok else []
    except Exception:
        califs = []

    # Indexar última calificación por (equipo_id, desafio_id)
    calif_idx = {}
    for c in califs:
        key = (c.get("equipo_id"), c.get("desafio_id"))
        c_time = c.get("actualizado_en")
        if key not in calif_idx or (c_time and c_time > calif_idx[key].get("actualizado_en", "")):
            calif_idx[key] = c

    return render_template(
        "dashboard_jueces/dashboard_juez.html",
        torneos=torneos,
        desafios=desafios,
        torneo_id=torneo_id,
        desafio_id=desafio_id,
        envios=envios,
        calif_idx=calif_idx
    )

@juez_bp.route("/calificar", methods=["POST"])
def calificar():
    data = {
        "torneo_id":    request.form.get("torneo_id") or None,
        "desafio_id":   request.form.get("desafio_id") or None,
        "equipo_id":    request.form.get("equipo_id") or None,
        "respuesta_id": request.form.get("respuesta_id") or None,
        "estado":       request.form.get("estado") or "pendiente",
        "puntaje":      request.form.get("puntaje") or None,
        "comentario":   request.form.get("comentario") or None,
        # Identificación del juez (ajústalo a tu login real)
        "juez_id_text": request.form.get("juez_id_text") or "j001",
        "juez_nombre":  request.form.get("juez_nombre")  or "Juez",
    }

    try:
        r = requests.post(f"{API_BASE}/juez", json=data, headers=_headers(), timeout=10)
        if r.ok:
            flash("✅ Calificación guardada", "success")
        else:
            flash(f"❌ Error al guardar: {r.text}", "danger")
    except Exception as e:
        flash(f"❌ Error de red: {e}", "danger")

    # Volver al dashboard del juez
    return redirect(url_for("juez.dashboard"))
