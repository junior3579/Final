from flask import Blueprint, jsonify
from backend.database_config import listar_usuarios_online

online_bp = Blueprint('online', __name__)

@online_bp.route('/usuarios-online', methods=['GET'])
def get_usuarios_online():
    usuarios_online = listar_usuarios_online(minutos=5)
    return jsonify({
        'usuarios_online': usuarios_online,
        'total': len(usuarios_online)
    })

