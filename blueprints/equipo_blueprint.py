import requests
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
import os

# Crear Blueprint
equipo_bp = Blueprint('equipo', __name__)

# Ruta para listar todos los equipos
@equipo_bp.route('/', methods=['GET'])
def listar_equipos():
    url_base_api = current_app.config["URL_BASE_API"]
    headers = {'Clave-De-Autenticacion': current_app.config['TOKEN']}

    try:
        response = requests.get(f"{url_base_api}/equipos", headers=headers)
        equipos = response.json() if response.status_code == 200 else []
    except Exception as e:
        flash(f"Error al conectar con la API: {str(e)}", "danger")
        equipos = []

    return render_template(
        'dashboard_admin/equipo.html',  
        equipos=equipos
    )