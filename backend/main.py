import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from backend.database_config import criar_tabelas_remoto
from backend.socketio_instance import init_socketio
from backend.routes.auth import auth_bp
from backend.routes.usuarios import usuarios_bp
from backend.routes.salas import salas_bp
from backend.routes.apostas import apostas_bp
from backend.routes.online import online_bp
from backend.routes.transacoes import transacoes_bp
from backend.routes.admin_features import admin_features_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'
socketio = init_socketio(app)

# Habilitar CORS para todas as rotas
CORS(app)

# Registrar blueprints
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(usuarios_bp, url_prefix='/api')
app.register_blueprint(salas_bp, url_prefix="/api")
app.register_blueprint(apostas_bp, url_prefix="/api")
app.register_blueprint(online_bp, url_prefix="/api")
app.register_blueprint(transacoes_bp, url_prefix='/api')
app.register_blueprint(admin_features_bp, url_prefix='/api')

# Criar tabelas no banco de dados
with app.app_context():
    criar_tabelas_remoto()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


# Para deploy no Render/Gunicorn
port = int(os.environ.get("PORT", 5000))

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
