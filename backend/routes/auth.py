from flask import Blueprint, request, jsonify
from backend.database_config import executar_query_fetchall, atualizar_atividade_usuario
from backend.socketio_instance import get_socketio

auth_bp = Blueprint('auth', __name__)

SENHA_ADMIN = "3579"

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    nome = data.get('nome')
    senha = data.get('senha')
    
    if not nome or not senha:
        return jsonify({'error': 'Nome e senha são obrigatórios'}), 400
    
    # Verificar se é admin
    if nome == "admin" and senha == SENHA_ADMIN:
        return jsonify({
            'success': True,
            'user': {
                'id': 0,
                'nome': 'admin',
                'tipo': 'admin',
                'pontos': 0
            }
        })
    
    # Verificar usuário comum
    result = executar_query_fetchall(
        "SELECT id, pontos FROM usuarios WHERE nome = %s AND senha = %s",
        (nome, senha)
    )
    
    if result:
        id_usuario, pontos = result[0]
        atualizar_atividade_usuario(id_usuario)
        socketio = get_socketio()
        if socketio:
            socketio.emit("user_online", {"nome": nome})
        return jsonify({
            'success': True,
            'user': {
                'id': id_usuario,
                'nome': nome,
                'tipo': 'usuario',
                'pontos': pontos
            }
        })
    
    return jsonify({'error': 'Credenciais inválidas'}), 401

