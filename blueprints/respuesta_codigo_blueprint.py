from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, current_app, session, jsonify
)
import requests
import sys
import io
import os
import re
from datetime import datetime

respuesta_codigo_bp = Blueprint('respuesta_codigo_bp', __name__)

# Para probar el codigo
@respuesta_codigo_bp.route('/probar_codigo', methods=['POST'])
def probar_codigo():
    data = request.get_json()
    codigo = data.get('codigo', '')

    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = mystdout = io.StringIO()
    sys.stderr = mystderr = io.StringIO()

    exito = True
    try:
        exec(codigo, {})
    except Exception as e:
        exito = False
        print(f"Error: {e}")

    sys.stdout = old_stdout
    sys.stderr = old_stderr

    salida = mystdout.getvalue() + mystderr.getvalue()
    return jsonify({"salida": salida, "exito": exito})

# Aqui se crea la respuesta
@respuesta_codigo_bp.route('/crear', methods=['GET', 'POST'])
def crear_respuesta():
    url_base_api = current_app.config["URL_BASE_API"].rstrip("/")
    headers = {'Clave-De-Autenticacion': current_app.config['TOKEN']}
    api_url = f'{url_base_api}/respuestas'

    if request.method == 'POST':
        # leemos lo que llega
        tiempo = request.form.get('tiempo')
        equipo_id = request.form.get('equipo_id')
        desafio_id = request.form.get('desafio_id')
        codigo = request.form.get('codigo_real')

        if not tiempo or not equipo_id or not desafio_id or not codigo:
            flash('Faltan datos obligatorios', 'danger')
            return redirect(url_for('respuesta_codigo_bp.crear_respuesta', desafio_id=desafio_id))

        # 1) obtener nombre de equipo desde API
        nombre_equipo = obtener_nombre_equipo(int(equipo_id), headers, url_base_api)
        # 2) construir un nombre único y amistoso
        archivo_nombre = construir_nombre_archivo(nombre_equipo, int(desafio_id))

        # 3) guardar archivo en carpeta por equipo/desafío
        try:
            carpeta_destino = os.path.join("archivos_codigos", f"equipo_{slugify(nombre_equipo)}", f"desafio_{desafio_id}")
            os.makedirs(carpeta_destino, exist_ok=True)
            ruta_archivo = os.path.join(carpeta_destino, archivo_nombre)
            with open(ruta_archivo, "w", encoding="utf-8") as f:
                f.write(codigo)
        except Exception as e:
            flash(f"Error al guardar el archivo: {str(e)}", "danger")
            return redirect(url_for('respuesta_codigo_bp.crear_respuesta', desafio_id=desafio_id))

        # 4) enviar metadatos a la API (usa el nombre generado)
        respuesta_data = {
            'archivo_nombre': archivo_nombre,
            'tiempo': tiempo,
            'equipo_id': int(equipo_id),
            'desafio_id': int(desafio_id)
        }

        try:
            response = requests.post(api_url, json=respuesta_data, headers=headers, timeout=20)
            data = response.json() if response.content else {}
            if response.status_code == 201:
                flash(data.get('message', 'Respuesta creada correctamente'), 'success')
                return redirect(url_for('respuesta_codigo_bp.listar_respuestas'))
            else:
                error_msg = data.get('error') or data.get('message') or f'Error {response.status_code}'
                flash(error_msg, 'danger')
        except Exception as e:
            flash(f'Error al conectar con la API: {str(e)}', 'danger')

        return redirect(url_for('respuesta_codigo_bp.crear_respuesta', desafio_id=desafio_id))

    # GET: Renderizar formulario con un nombre de vista “sugerido” (opcional)
    equipo_id = session.get('equipo_id')
    desafio_id = request.args.get('desafio_id', type=int)
    if not equipo_id or not desafio_id:
        flash("Faltan datos para responder al desafío", "warning")
        return redirect(url_for('dashboard_equipo_bp.dashboard_equipo'))

    # sugerencia de nombre (solo visual si lo muestras en el template)
    nombre_equipo = obtener_nombre_equipo(int(equipo_id), headers, url_base_api)
    archivo_nombre = construir_nombre_archivo(nombre_equipo, int(desafio_id))

    return render_template(
        'dashboard_equipos/crear_respuesta_codigo.html',
        equipo_id=equipo_id,
        desafio_id=desafio_id,
        archivo_nombre=archivo_nombre  # si lo muestras; no confíes en él para guardado
    )

# Listar todas las respuestas
@respuesta_codigo_bp.route('/')
def listar_respuestas():
    url_base_api = current_app.config["URL_BASE_API"]
    headers = {'Clave-De-Autenticacion': current_app.config['TOKEN']}
    api_url = f'{url_base_api}/respuestas'

    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            respuestas = response.json()
            return render_template('listar_respuestas_codigo.html', respuestas=respuestas)
        else:
            error_msg = response.json().get('error') or "Error al obtener las respuestas"
            flash(error_msg, "danger")
    except Exception as e:
        flash(f"Error al conectar con la API: {str(e)}", "danger")

    return render_template('listar_respuestas_codigo.html', respuestas=[])

#  Obtener una respuesta por el ID
@respuesta_codigo_bp.route('/<int:id>')
def obtener_respuesta(id):
    url_base_api = current_app.config["URL_BASE_API"]
    headers = {'Clave-De-Autenticacion': current_app.config['TOKEN']}
    api_url = f'{url_base_api}/respuestas/{id}'

    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            respuesta = response.json()
            return render_template('actualizar_respuesta_codigo.html', respuesta=respuesta)
        else:
            flash("Respuesta no encontrada", "danger")
    except Exception as e:
        flash(f"Error al conectar con la API: {str(e)}", "danger")

    return redirect(url_for('respuesta_codigo_bp.listar_respuestas'))

# Actualizar una respuesta existente
@respuesta_codigo_bp.route('/<int:id>/actualizar', methods=['POST'])
def actualizar_respuesta(id):
    url_base_api = current_app.config["URL_BASE_API"]
    headers = {'Clave-De-Autenticacion': current_app.config['TOKEN']}
    api_url = f'{url_base_api}/respuestas/{id}'

    archivo_nombre = request.form.get('archivo_nombre')
    tiempo = request.form.get('tiempo')
    equipo_id = request.form.get('equipo_id')
    desafio_id = request.form.get('desafio_id')

    if not archivo_nombre or not tiempo or not equipo_id or not desafio_id:
        flash("Todos los campos son obligatorios", "danger")
        return redirect(url_for('respuesta_codigo_bp.obtener_respuesta', id=id))

    respuesta_data = {
        'archivo_nombre': archivo_nombre,
        'tiempo': tiempo,
        'equipo_id': int(equipo_id),
        'desafio_id': int(desafio_id)
    }

    try:
        response = requests.put(api_url, json=respuesta_data, headers=headers)
        data = response.json()
        if response.status_code == 200:
            flash(data.get('message', "Respuesta actualizada correctamente"), "success")
        else:
            error_msg = data.get('error') or data.get('message') or "Error al actualizar la respuesta"
            flash(error_msg, "danger")
    except Exception as e:
        flash(f"Error al conectar con la API: {str(e)}", "danger")

    return redirect(url_for('respuesta_codigo_bp.obtener_respuesta', id=id))

def slugify(texto: str) -> str:
    if not texto:
        return "equipo"
    # Mantiene letras/números/guion/guion_bajo, reemplaza el resto por _
    s = re.sub(r'[^a-zA-Z0-9_-]+', '_', texto.strip())
    return s.strip('_').lower() or "equipo"

def obtener_nombre_equipo(equipo_id: int, headers: dict, base_url: str) -> str:
    try:
        resp = requests.get(f"{base_url.rstrip('/')}/equipos", headers=headers, timeout=10)
        equipos = resp.json() if resp.status_code == 200 else []
        for e in equipos:
            try:
                codigo = e.get('CodigoEquipo') or e.get('id_equipo') or e.get('equipo_id')
                if int(codigo) == int(equipo_id):
                    return e.get('NombreEquipo') or e.get('nombre_equipo') or f"equipo_{equipo_id}"
            except Exception:
                continue
    except Exception:
        pass
    return f"equipo_{equipo_id}"

def construir_nombre_archivo(nombre_equipo: str, desafio_id: int) -> str:
    base_equipo = slugify(nombre_equipo)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    nombre = f"{base_equipo}_desafio-{desafio_id}_{ts}.py"
    # Asegurar <= 150 chars
    if len(nombre) > 150:
        # recortar la parte del equipo
        exceso = len(nombre) - 150
        base_equipo = base_equipo[:-exceso] if exceso < len(base_equipo) else base_equipo[:1]
        nombre = f"{base_equipo}_desafio-{desafio_id}_{ts}.py"
    return nombre