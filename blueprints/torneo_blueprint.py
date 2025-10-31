from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
import requests
from datetime import datetime

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

def _headers():
    return {
        'Clave-De-Autenticacion': current_app.config['TOKEN'],
        'Content-Type': 'application/json'
    }

def _parse_date(s):
    # Espera formato YYYY-MM-DD
    return datetime.strptime(s, "%Y-%m-%d").date()

def _overlap(a1, a2, b1, b2):
    # Solapan si los rangos se tocan o cruzan
    return a1 <= b2 and b1 <= a2

@torneo_bp.route('/', methods=['GET', 'POST'])
@solo_admin
def torneo():
    url_base_api = current_app.config["URL_BASE_API"]
    headers = _headers()

    # --- CREAR / ACTUALIZAR ---
    if request.method == 'POST':
        id_torneo = request.form.get('id_torneo')
        nombre = request.form.get('nombre', '').strip()
        fecha_inicio = request.form.get('fecha_inicio', '').strip()
        fecha_termino = request.form.get('fecha_termino', '').strip()
        estado = request.form.get('estado')

        # Validaciones básicas
        if not nombre or not fecha_inicio or not fecha_termino or estado not in ['0', '1', 0, 1]:
            flash('Faltan datos obligatorios.', 'danger')
            return redirect(url_for('torneo.torneo'))

        # Validación de orden de fechas
        try:
            fi = _parse_date(fecha_inicio)
            ft = _parse_date(fecha_termino)
        except ValueError:
            flash('Formato de fecha inválido. Usa YYYY-MM-DD.', 'danger')
            return redirect(url_for('torneo.torneo'))

        if fi > ft:
            flash('La fecha de inicio no puede ser mayor que la fecha de término.', 'danger')
            return redirect(url_for('torneo.torneo'))

        # Validación de solapamiento con otros torneos
        try:
            resp_all = requests.get(f"{url_base_api}/torneos", headers=headers, timeout=10)
            existentes = resp_all.json() if resp_all.ok else []
        except Exception as e:
            existentes = []
            flash(f"Advertencia: no se pudo validar solapamiento ({e}).", "warning")

        for t in existentes or []:
            tid = t.get('id_torneo') if isinstance(t, dict) else t.id_torneo
            if id_torneo and str(tid) == str(id_torneo):
                continue  # ignorar el mismo al editar
            t_fi = t.get('fecha_inicio') if isinstance(t, dict) else t.fecha_inicio
            t_ft = t.get('fecha_termino') if isinstance(t, dict) else t.fecha_termino
            try:
                t_fi_d = _parse_date(t_fi)
                t_ft_d = _parse_date(t_ft)
            except Exception:
                continue
            if _overlap(fi, ft, t_fi_d, t_ft_d):
                flash(f"Las fechas se solapan con el torneo #{tid} ({t.get('nombre') or ''}). Cambia el rango.", "danger")
                return redirect(url_for('torneo.torneo'))

        torneo_data = {
            'nombre': nombre,
            'fecha_inicio': fecha_inicio,
            'fecha_termino': fecha_termino,
            'estado': int(estado)
        }

        try:
            if id_torneo:  # Actualizar
                response = requests.put(f'{url_base_api}/torneos/{id_torneo}', json=torneo_data, headers=headers, timeout=10)
                data = response.json() if response.content else {}
                if response.status_code == 200:
                    flash(data.get('mensaje', 'Torneo actualizado correctamente.'), "success")
                else:
                    error_msg = data.get('error') or data.get('mensaje') or 'Error desconocido al actualizar.'
                    flash(error_msg, "danger")
            else:  # Crear
                response = requests.post(f"{url_base_api}/torneos", json=torneo_data, headers=headers, timeout=10)
                data = response.json() if response.content else {}
                if response.status_code in (200, 201):
                    flash(data.get('mensaje', 'Torneo creado correctamente.'), 'success')
                else:
                    error_msg = data.get('error') or data.get('mensaje') or 'Error desconocido al crear.'
                    flash(error_msg, 'danger')
        except Exception as e:
            flash(f'Error al conectar con la API: {str(e)}', 'danger')

        return redirect(url_for('torneo.torneo'))

    # --- LISTAR TORNEOS ---
    try:
        response = requests.get(f"{url_base_api}/torneos", headers=headers, timeout=10)
        torneos = response.json() if response.status_code == 200 else []
    except Exception as e:
        flash(f"Error al conectar con la API: {str(e)}", "danger")
        torneos = []

    # --- EDITAR (cargar datos en el form) ---
    torneo_editar = None
    editar_id = request.args.get('editar')
    if editar_id:
        try:
            response = requests.get(f'{url_base_api}/torneos/{editar_id}', headers=headers, timeout=10)
            if response.status_code == 200:
                torneo_editar = response.json()
            else:
                data = response.json() if response.content else {}
                error_msg = data.get('error') or data.get('mensaje') or 'Error desconocido'
                flash(error_msg, "danger")
        except Exception as e:
            flash(f"Error al conectar con la API: {str(e)}", "danger")

    return render_template(
        'dashboard_admin/torneo.html',
        torneos=torneos,
        torneo_editar=torneo_editar
    )

# -------- ELIMINAR --------
@torneo_bp.post('/eliminar/<int:id_torneo>')
@solo_admin
def eliminar(id_torneo):
    url_base_api = current_app.config["URL_BASE_API"]
    headers = _headers()
    try:
        resp = requests.delete(f"{url_base_api}/torneos/{id_torneo}", headers=headers, timeout=10)
        data = resp.json() if resp.content else {}
        if resp.status_code == 200:
            flash(data.get('mensaje', 'Torneo eliminado.'), 'success')
        else:
            flash(data.get('error') or data.get('mensaje') or 'No se pudo eliminar el torneo.', 'danger')
    except Exception as e:
        flash(f"Error al conectar con la API: {e}", "danger")
    return redirect(url_for('torneo.torneo'))
