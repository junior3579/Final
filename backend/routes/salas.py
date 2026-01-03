from flask import Blueprint, request, jsonify
from backend.database_config import executar_query_fetchall, executar_query_commit
from backend.socketio_instance import get_socketio

salas_bp = Blueprint('salas', __name__)

def validar_pontos(pontos):
    try:
        pontos_int = int(pontos)
        if pontos_int <= 0:
            return None, "O valor de pontos deve ser maior que 0"
        if pontos_int % 2 != 0:
            return None, "Não aceita número ímpar, apenas par"
        return pontos_int, None
    except:
        return None, "Por favor, insira um valor válido"

def obter_jogadores(jogadores_str):
    jogadores_dict = {}
    tokens = jogadores_str.split(",") if jogadores_str else []
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        if token.isdigit():
            res = executar_query_fetchall("SELECT nome, whatsapp FROM usuarios WHERE id = %s", (token,))
        else:
            res = executar_query_fetchall("SELECT nome, whatsapp FROM usuarios WHERE nome = %s", (token,))
        if res:
            nome_jogador, whatsapp = res[0]
            if whatsapp and whatsapp != "Não cadastrado":
                jogadores_dict[nome_jogador] = whatsapp
    return jogadores_dict

@salas_bp.route('/salas', methods=['GET'])
def listar_salas():
    salas = executar_query_fetchall("SELECT id_sala, nome_sala, valor_inicial, criador, jogadores, whatsapp, categoria_id FROM salas")
    if not salas:
        return jsonify([])
    
    salas_list = []
    for sala in salas:
        id_sala, nome_sala, valor_inicial, criador, jogadores, whatsapp, categoria_id = sala
        jogadores_dict = obter_jogadores(jogadores)
        
        salas_list.append({
            'id_sala': id_sala,
            'nome_sala': nome_sala,
            'valor_inicial': valor_inicial,
            'criador': criador,
            'jogadores': jogadores_dict,
            'whatsapp': whatsapp,
            'categoria_id': categoria_id
        })
    
    return jsonify(salas_list)

@salas_bp.route('/salas', methods=['POST'])
def criar_sala():
    data = request.get_json()
    nome_sala = data.get('nome_sala')
    valor_inicial = data.get('valor_inicial')
    criador = data.get('criador')
    whatsapp = data.get('whatsapp', 'Não cadastrado')
    
    if not nome_sala or not valor_inicial or not criador:
        return jsonify({'error': 'Nome da sala, valor inicial e criador são obrigatórios'}), 400
    
    # Verificar se usuário existe e buscar saldo
    saldo_usuario = executar_query_fetchall("SELECT pontos FROM usuarios WHERE nome = %s", (criador,))
    if not saldo_usuario:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    saldo_usuario = saldo_usuario[0][0]
    
    # Validar valor inicial
    valor_inicial_validado, erro = validar_pontos(valor_inicial)
    if valor_inicial_validado is None:
        return jsonify({'error': erro}), 400
    
    if saldo_usuario < valor_inicial_validado:
        return jsonify({'error': 'Saldo insuficiente para criar esta sala'}), 400
    
    # Verificar limite de salas por usuário
    count_salas = executar_query_fetchall("SELECT COUNT(*) FROM salas WHERE criador = %s", (criador,))
    if count_salas and count_salas[0][0] >= 2:
        return jsonify({'error': 'Você já tem 2 salas criadas'}), 400
    
    categoria_id = data.get('categoria_id')
    
    # Criar sala
    sucesso = executar_query_commit(
        "INSERT INTO salas (nome_sala, valor_inicial, criador, jogadores, whatsapp, categoria_id) VALUES (%s, %s, %s, %s, %s, %s)",
        (nome_sala, valor_inicial_validado, criador, criador, whatsapp, categoria_id)
    )
    
    if sucesso:
        # Debitar metade do valor inicial do criador
        novos_pontos = saldo_usuario - (valor_inicial_validado // 2)
        executar_query_commit("UPDATE usuarios SET pontos = %s WHERE nome = %s", (novos_pontos, criador))
        return jsonify({
            'message': f'Sala {nome_sala} criada com sucesso',
            'novos_pontos': novos_pontos
        })
    else:
        return jsonify({'error': 'Erro ao criar sala'}), 500

@salas_bp.route('/salas/<int:id_sala>/entrar', methods=['POST'])
def entrar_em_sala(id_sala):
    data = request.get_json()
    id_usuario = data.get('id_usuario')
    nome_usuario = data.get('nome_usuario')
    
    if not id_usuario or not nome_usuario:
        return jsonify({'error': 'ID e nome do usuário são obrigatórios'}), 400
    
    # Buscar saldo do usuário
    saldo_usuario = executar_query_fetchall("SELECT pontos FROM usuarios WHERE id = %s", (id_usuario,))
    if not saldo_usuario:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    saldo_usuario = saldo_usuario[0][0]
    
    # Buscar informações da sala
    sala = executar_query_fetchall("SELECT nome_sala, valor_inicial, jogadores, criador FROM salas WHERE id_sala = %s", (id_sala,))
    if not sala:
        return jsonify({'error': 'Sala não encontrada'}), 404
    
    nome_sala, valor_inicial, jogadores, criador = sala[0]
    
    # Verificar se tem saldo suficiente
    if saldo_usuario < valor_inicial // 2:
        return jsonify({'error': 'Saldo insuficiente'}), 400
    
    # Verificar se já está na sala
    jogadores_lista = jogadores.split(",") if jogadores else []
    if len(jogadores_lista) >= 2:
        return jsonify({'error': 'A sala já está cheia (2 jogadores)'}), 400
    if str(id_usuario) in jogadores_lista or nome_usuario in jogadores_lista:
        return jsonify({'error': 'Você já está na sala'}), 400
    
    # Adicionar jogador à sala
    novos_jogadores = jogadores + f",{id_usuario}" if jogadores else str(id_usuario)
    sucesso = executar_query_commit("UPDATE salas SET jogadores = %s WHERE id_sala = %s", (novos_jogadores, id_sala))
    
    if sucesso:
        # Debitar metade do valor inicial
        novos_pontos = saldo_usuario - (valor_inicial // 2)
        executar_query_commit("UPDATE usuarios SET pontos = %s WHERE id = %s", (novos_pontos, id_usuario))
        
        # Notificação via Socket.IO removida temporariamente para evitar erro de conexão/timeout
        # O redirecionamento via WhatsApp já cumpre o papel de notificar o criador
        pass

        # Buscar informações do criador para redirecionamento ao WhatsApp
        criador_info = executar_query_fetchall(
            "SELECT nome, whatsapp FROM usuarios WHERE nome = %s",
            (criador,)
        )
        
        dados_criador = None
        if criador_info:
            dados_criador = {
                'nome': criador_info[0][0],
                'whatsapp': criador_info[0][1] if criador_info[0][1] and criador_info[0][1] != 'Não cadastrado' else None
            }
        
        return jsonify({
            'message': f'Você entrou na sala {id_sala}',
            'novos_pontos': novos_pontos,
            'sala_info': {
                'nome': nome_sala,
                'valor': valor_inicial
            },
            'criador_info': dados_criador
        })
    else:
        return jsonify({'error': 'Erro ao entrar na sala'}), 500

@salas_bp.route('/salas/<int:id_sala>', methods=['DELETE'])
def remover_sala(id_sala):
    # Verificar se sala existe
    sala = executar_query_fetchall("SELECT * FROM salas WHERE id_sala = %s", (id_sala,))
    if not sala:
        return jsonify({'error': 'Sala não encontrada'}), 404
    
    sucesso = executar_query_commit("DELETE FROM salas WHERE id_sala = %s", (id_sala,))
    
    if sucesso:
        return jsonify({'message': f'Sala {id_sala} removida com sucesso'})
    else:
        return jsonify({'error': 'Erro ao remover sala'}), 500

@salas_bp.route('/salas/<int:id_sala>/jogadores', methods=['GET'])
def obter_jogadores_sala(id_sala):
    sala = executar_query_fetchall("SELECT jogadores FROM salas WHERE id_sala = %s", (id_sala,))
    if not sala:
        return jsonify({'error': 'Sala não encontrada'}), 404
    
    jogadores_dict = obter_jogadores(sala[0][0])
    return jsonify(jogadores_dict)

@salas_bp.route('/salas/<int:id_sala>/definir-ganhador', methods=['POST'])
def definir_ganhador_sala(id_sala):
    data = request.get_json()
    vencedor_id = data.get('vencedor_id')
    
    if not vencedor_id:
        return jsonify({'error': 'ID do vencedor é obrigatório'}), 400
    
    # Buscar informações da sala
    sala = executar_query_fetchall(
        "SELECT valor_inicial, jogadores, criador FROM salas WHERE id_sala = %s",
        (id_sala,)
    )
    
    if not sala:
        return jsonify({'error': 'Sala não encontrada'}), 404
    
    valor_inicial, jogadores, criador = sala[0]
    
    # Verificar se o vencedor está na sala
    jogadores_lista = jogadores.split(",") if jogadores else []
    vencedor_str = str(vencedor_id)
    
    # Buscar nome do vencedor
    vencedor_info = executar_query_fetchall("SELECT nome FROM usuarios WHERE id = %s", (vencedor_id,))
    if not vencedor_info:
        return jsonify({'error': 'Vencedor não encontrado'}), 404
    
    vencedor_nome = vencedor_info[0][0]
    
    # Verificar se está na sala (por ID ou nome)
    if vencedor_str not in jogadores_lista and vencedor_nome not in jogadores_lista:
        return jsonify({'error': 'Vencedor não está na sala'}), 400
    
    # Atualizar sala com vencedor e status
    sucesso = executar_query_commit(
        "UPDATE salas SET vencedor_id = %s, status = 'finalizada' WHERE id_sala = %s",
        (vencedor_id, id_sala)
    )
    
    if sucesso:
        # Adicionar pontos ao vencedor (valor total da sala)
        premio = valor_inicial
        executar_query_commit(
            "UPDATE usuarios SET pontos = pontos + %s WHERE id = %s",
            (premio, vencedor_id)
        )
        
        # Emitir notificação via Socket.IO
        socketio = get_socketio()
        if socketio:
            socketio.emit('sala_finalizada', {
                'id_sala': id_sala,
                'vencedor_id': vencedor_id,
                'vencedor_nome': vencedor_nome,
                'premio': premio
            })
        
        return jsonify({
            'message': 'Ganhador definido com sucesso',
            'vencedor_id': vencedor_id,
            'vencedor_nome': vencedor_nome,
            'premio': premio
        })
    
    return jsonify({'error': 'Erro ao definir ganhador'}), 500

