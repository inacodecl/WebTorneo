from flask import Blueprint, render_template, session, redirect, url_for, flash

dashboard_admin_bp = Blueprint('dashboard_admin_bp', __name__)

@dashboard_admin_bp.route('/dashboard/admin')
def dashboard_admin():
    # Solo permitir acceso si es admin
    if session.get('rol') != 'admin':
        flash("Acceso solo para administradores.", "danger")
        return redirect(url_for('login.formulario_login'))
    return render_template('dashboard_admin/dashboard_admin.html')