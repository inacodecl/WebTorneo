from flask import Flask, render_template
from config import config
from blueprints.equipo_blueprint import equipo_bp
from blueprints.integrante_blueprint import integrante_bp 
from blueprints.fase_blueprint import fase_bp
from blueprints.desafio_blueprint import desafio_bp
from blueprints.torneo_blueprint import torneo_bp
from blueprints.registro_blueprint import registro_bp
from blueprints.resultado_fase_blueprint import resultado_fase_bp
from blueprints.resultado_torneo_blueprint import resultado_torneo_bp
from blueprints.respuesta_codigo_blueprint import respuesta_codigo_bp
from blueprints.inscripcion_blueprint import inscripcion_bp
from blueprints.login_blueprint import login_bp
from blueprints.dashboard_equipo_blueprint import dashboard_equipo_bp
from blueprints.dashboard_admin_blueprint import dashboard_admin_bp
from blueprints.ranking import ranking_bp
from blueprints.dashboard_juez_blueprint import juez_bp
from blueprints.dashboard_juez_blueprint import juez_bp




app = Flask(__name__)

app.config.update(config)

# Registrar el blueprint para inscripciones
app.register_blueprint(inscripcion_bp, url_prefix='/inscripcion')
app.register_blueprint(login_bp, url_prefix='/login')
app.register_blueprint(equipo_bp, url_prefix='/equipo')
app.register_blueprint(integrante_bp, url_prefix='/integrante')
app.register_blueprint(fase_bp, url_prefix='/fase')
app.register_blueprint(desafio_bp, url_prefix='/desafio')
app.register_blueprint(torneo_bp, url_prefix='/torneo')
app.register_blueprint(registro_bp, url_prefix='/registro')
app.register_blueprint(resultado_fase_bp, url_prefix='/resultado_fase') 
app.register_blueprint(resultado_torneo_bp, url_prefix='/resultado_torneo')
app.register_blueprint(respuesta_codigo_bp, url_prefix='/respuesta_codigo')
app.register_blueprint(dashboard_equipo_bp)
app.register_blueprint(juez_bp)
app.register_blueprint(dashboard_admin_bp)
app.register_blueprint(ranking_bp)
app.secret_key = "dev"  # o tu clave


# Ruta principal
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
