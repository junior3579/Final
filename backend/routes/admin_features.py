from flask import Blueprint, request, jsonify
from backend.database_config import executar_query_fetchall, executar_query_commit

admin_features_bp = Blueprint('admin_features', __name__)

# --- Categorias ---

@admin_features_bp.route('/categorias', methods=['GET'])
def listar_categorias():
    categorias = executar_query_fetchall("SELECT id, nome FROM categorias")
    res = []
    if categorias:
        for c in categorias:
            count = executar_query_fetchall("SELECT COUNT(*) FROM salas WHERE categoria_id = %s", (c[0],))
            res.append({
                'id': c[0],
                'nome': c[1],
                'total_salas': count[0][0] if count else 0
            })
    return jsonify(res)

@admin_features_bp.route('/categorias', methods=['POST'])
def criar_categoria():
    data = request.get_json()
    nome = data.get('nome')
    if not nome:
        return jsonify({'error': 'Nome da categoria é obrigatório'}), 400
    
    sucesso = executar_query_commit("INSERT INTO categorias (nome) VALUES (%s)", (nome,))
    if sucesso:
        return jsonify({'message': 'Categoria criada com sucesso'})
    return jsonify({'error': 'Erro ao criar categoria ou nome já existe'}), 500

@admin_features_bp.route('/categorias/<int:id>', methods=['PUT'])
def renomear_categoria(id):
    data = request.get_json()
    novo_nome = data.get('nome')
    if not novo_nome:
        return jsonify({'error': 'Novo nome é obrigatório'}), 400
    
    sucesso = executar_query_commit("UPDATE categorias SET nome = %s WHERE id = %s", (novo_nome, id))
    if sucesso:
        return jsonify({'message': 'Categoria renomeada com sucesso'})
    return jsonify({'error': 'Erro ao renomear categoria'}), 500

@admin_features_bp.route('/categorias/<int:id>', methods=['DELETE'])
def remover_categoria(id):
    # Opcional: Desvincular salas antes de remover
    executar_query_commit("UPDATE salas SET categoria_id = NULL WHERE categoria_id = %s", (id,))
    sucesso = executar_query_commit("DELETE FROM categorias WHERE id = %s", (id,))
    if sucesso:
        return jsonify({'message': 'Categoria removida com sucesso'})
    return jsonify({'error': 'Erro ao remover categoria'}), 500

# --- Torneios ---

@admin_features_bp.route('/torneios', methods=['GET'])
def listar_torneios():
    torneios = executar_query_fetchall("SELECT id, nome, status, vencedor_id, valor_inscricao, premio, fase_atual FROM torneios")
    res = []
    if torneios:
        for t in torneios:
            participantes = executar_query_fetchall(
                "SELECT u.id, u.nome, tp.status FROM torneio_participantes tp JOIN usuarios u ON tp.usuario_id = u.id WHERE tp.torneio_id = %s",
                (t[0],)
            )
            res.append({
                'id': t[0],
                'nome': t[1],
                'status': t[2],
                'vencedor_id': t[3],
                'valor_inscricao': t[4] if len(t) > 4 else 0,
                'premio': t[5] if len(t) > 5 else 0,
                'fase_atual': t[6] if len(t) > 6 else 'inscricao',
                'participantes': [{'id': p[0], 'nome': p[1], 'status': p[2]} for p in participantes] if participantes else []
            })
    return jsonify(res)

@admin_features_bp.route('/torneios', methods=['POST'])
def criar_torneio():
    data = request.get_json()
    nome = data.get('nome')
    data_inicio = data.get('data_inicio')
    data_fim = data.get('data_fim')
    valor_inscricao = data.get('valor_inscricao', 0)
    premio = data.get('premio', 0)
    
    if not nome:
        return jsonify({'error': 'Nome do torneio é obrigatório'}), 400
    
    sucesso = executar_query_commit(
        "INSERT INTO torneios (nome, data_inicio, data_fim, valor_inscricao, premio) VALUES (%s, %s, %s, %s, %s)", 
        (nome, data_inicio, data_fim, valor_inscricao, premio)
    )
    if sucesso:
        return jsonify({'message': f'Torneio {nome} criado com sucesso'})
    return jsonify({'error': 'Erro ao criar torneio'}), 500

@admin_features_bp.route('/torneios/<int:id>/inscrever', methods=['POST'])
def inscrever_no_torneio(id):
    data = request.get_json()
    usuario_id = data.get('usuario_id')
    nome_usuario = data.get('nome_usuario') # Opcional para busca manual
    
    if not usuario_id and nome_usuario:
        res = executar_query_fetchall("SELECT id FROM usuarios WHERE nome = %s", (nome_usuario,))
        if res:
            usuario_id = res[0][0]
        else:
            return jsonify({'error': 'Usuário não encontrado pelo nome'}), 404

    if not usuario_id:
        return jsonify({'error': 'ID ou Nome do usuário é obrigatório'}), 400

    # REMOVIDA A RESTRIÇÃO - Agora permite adicionar em qualquer status
    torneio = executar_query_fetchall("SELECT status FROM torneios WHERE id = %s", (id,))
    if not torneio:
        return jsonify({'error': 'Torneio não encontrado'}), 404
    
    # Verificar se já está inscrito
    existe = executar_query_fetchall("SELECT id FROM torneio_participantes WHERE torneio_id = %s AND usuario_id = %s", (id, usuario_id))
    if existe:
        return jsonify({'error': 'Usuário já inscrito'}), 400
    
    sucesso = executar_query_commit("INSERT INTO torneio_participantes (torneio_id, usuario_id) VALUES (%s, %s)", (id, usuario_id))
    if sucesso:
        return jsonify({'message': 'Inscrição realizada com sucesso'})
    return jsonify({'error': 'Erro ao realizar inscrição'}), 500

@admin_features_bp.route('/torneios/<int:id>/iniciar', methods=['POST'])
def iniciar_torneio(id):
    # Ao iniciar, gerar os primeiros confrontos automaticamente
    participantes = executar_query_fetchall(
        "SELECT usuario_id FROM torneio_participantes WHERE torneio_id = %s AND status = 'ativo'",
        (id,)
    )
    
    if not participantes or len(participantes) < 2:
        return jsonify({'error': 'Necessário pelo menos 2 participantes para iniciar'}), 400
    
    import random
    lista_ids = [p[0] for p in participantes]
    random.shuffle(lista_ids)
    
    # Criar confrontos
    for i in range(0, len(lista_ids), 2):
        p1 = lista_ids[i]
        p2 = lista_ids[i+1] if i+1 < len(lista_ids) else None
        
        if p2:
            executar_query_commit(
                "INSERT INTO torneio_confrontos (torneio_id, fase_nome, jogador1_id, jogador2_id) VALUES (%s, %s, %s, %s)",
                (id, 'Primeira Fase', p1, p2)
            )
        else:
            # Jogador sem dupla passa automaticamente (BYE)
            executar_query_commit(
                "INSERT INTO torneio_confrontos (torneio_id, fase_nome, jogador1_id, vencedor_id, status) VALUES (%s, %s, %s, %s, %s)",
                (id, 'Primeira Fase', p1, p1, 'finalizado')
            )

    sucesso = executar_query_commit("UPDATE torneios SET status = 'em_andamento', fase_atual = 'Primeira Fase' WHERE id = %s", (id,))
    if sucesso:
        return jsonify({'message': 'Torneio iniciado e confrontos gerados!'})
    return jsonify({'error': 'Erro ao iniciar torneio'}), 500

@admin_features_bp.route('/torneios/<int:id>/confrontos', methods=['GET'])
def listar_confrontos(id):
    confrontos = executar_query_fetchall(
        """SELECT c.id, c.fase_nome, c.jogador1_id, u1.nome, c.jogador2_id, u2.nome, c.vencedor_id, c.status 
           FROM torneio_confrontos c
           LEFT JOIN usuarios u1 ON c.jogador1_id = u1.id
           LEFT JOIN usuarios u2 ON c.jogador2_id = u2.id
           WHERE c.torneio_id = %s ORDER BY c.id DESC""",
        (id,)
    )
    
    res = []
    for c in confrontos:
        res.append({
            'id': c[0],
            'fase': c[1],
            'p1_id': c[2],
            'p1_nome': c[3],
            'p2_id': c[4],
            'p2_nome': c[5] if c[4] else 'AGUARDANDO',
            'vencedor_id': c[6],
            'status': c[7]
        })
    return jsonify(res)

@admin_features_bp.route('/confrontos/<int:id_confronto>/vencedor', methods=['POST'])
def definir_vencedor_confronto(id_confronto):
    data = request.get_json()
    vencedor_id = data.get('vencedor_id')
    
    # Buscar info do confronto
    confronto = executar_query_fetchall("SELECT torneio_id, fase_nome, jogador1_id, jogador2_id FROM torneio_confrontos WHERE id = %s", (id_confronto,))
    if not confronto: return jsonify({'error': 'Confronto não encontrado'}), 404
    
    torneio_id, fase_atual, p1, p2 = confronto[0]
    perdedor_id = p1 if vencedor_id == p2 else p2
    
    # 1. Atualizar confronto
    executar_query_commit("UPDATE torneio_confrontos SET vencedor_id = %s, status = 'finalizado' WHERE id = %s", (vencedor_id, id_confronto))
    
    # 2. Eliminar perdedor
    if perdedor_id:
        executar_query_commit("UPDATE torneio_participantes SET status = 'eliminado' WHERE torneio_id = %s AND usuario_id = %s", (torneio_id, perdedor_id))
    
    # 3. Verificar se todos os confrontos da fase acabaram para gerar próxima fase
    pendentes = executar_query_fetchall("SELECT id FROM torneio_confrontos WHERE torneio_id = %s AND fase_nome = %s AND status = 'pendente'", (torneio_id, fase_atual))
    
    if not pendentes:
        # Gerar próxima fase automaticamente
        vencedores = executar_query_fetchall(
            "SELECT usuario_id FROM torneio_participantes WHERE torneio_id = %s AND status = 'ativo'", (torneio_id,)
        )
        
        if len(vencedores) == 1:
            # Temos um campeão!
            campeao_id = vencedores[0][0]
            executar_query_commit("UPDATE torneios SET status = 'finalizado', vencedor_id = %s WHERE id = %s", (campeao_id, torneio_id))
            # Premiar
            torneio_info = executar_query_fetchall("SELECT premio FROM torneios WHERE id = %s", (torneio_id,))
            if torneio_info and torneio_info[0][0] > 0:
                executar_query_commit("UPDATE usuarios SET pontos = pontos + %s WHERE id = %s", (torneio_info[0][0], campeao_id))
        else:
            # Criar nova fase
            try:
                fase_num = int(fase_atual.split()[-1])
                proxima_fase = f"Fase {fase_num + 1}"
            except:
                proxima_fase = "Próxima Fase"
                
            lista_vencedores = [v[0] for v in vencedores]
            import random
            random.shuffle(lista_vencedores)
            
            for i in range(0, len(lista_vencedores), 2):
                v1 = lista_vencedores[i]
                v2 = lista_vencedores[i+1] if i+1 < len(lista_vencedores) else None
                if v2:
                    executar_query_commit("INSERT INTO torneio_confrontos (torneio_id, fase_nome, jogador1_id, jogador2_id) VALUES (%s, %s, %s, %s)", (torneio_id, proxima_fase, v1, v2))
                else:
                    executar_query_commit("INSERT INTO torneio_confrontos (torneio_id, fase_nome, jogador1_id, vencedor_id, status) VALUES (%s, %s, %s, %s, %s)", (torneio_id, proxima_fase, v1, v1, 'finalizado'))
            
            executar_query_commit("UPDATE torneios SET fase_atual = %s WHERE id = %s", (proxima_fase, torneio_id))

    return jsonify({'message': 'Vencedor definido e chaves atualizadas!'})

@admin_features_bp.route('/torneios/<int:id>/eliminar', methods=['POST'])
def eliminar_participante(id):
    data = request.get_json()
    usuario_id = data.get('usuario_id')
    
    sucesso = executar_query_commit(
        "UPDATE torneio_participantes SET status = 'eliminado' WHERE torneio_id = %s AND usuario_id = %s",
        (id, usuario_id)
    )
    
    # Verificar se sobrou apenas um
    ativos = executar_query_fetchall("SELECT usuario_id FROM torneio_participantes WHERE torneio_id = %s AND status = 'ativo'", (id,))
    if ativos and len(ativos) == 1:
        vencedor_id = ativos[0][0]
        executar_query_commit("UPDATE torneios SET status = 'finalizado', vencedor_id = %s WHERE id = %s", (vencedor_id, id))
        return jsonify({'message': 'Participante eliminado. Torneio finalizado!', 'vencedor_id': vencedor_id})
    
    if sucesso:
        return jsonify({'message': 'Participante eliminado'})
    return jsonify({'error': 'Erro ao eliminar participante'}), 500

@admin_features_bp.route('/torneios/<int:id>', methods=['PUT'])
def editar_torneio(id):
    data = request.get_json()
    valor_inscricao = data.get('valor_inscricao')
    premio = data.get('premio')
    nome = data.get('nome')
    data_inicio = data.get('data_inicio')
    data_fim = data.get('data_fim')
    
    updates = []
    params = []
    
    if nome is not None:
        updates.append("nome = %s")
        params.append(nome)
    
    if valor_inscricao is not None:
        updates.append("valor_inscricao = %s")
        params.append(valor_inscricao)
    
    if premio is not None:
        updates.append("premio = %s")
        params.append(premio)

    if data_inicio is not None:
        updates.append("data_inicio = %s")
        params.append(data_inicio)

    if data_fim is not None:
        updates.append("data_fim = %s")
        params.append(data_fim)
    
    if not updates:
        return jsonify({'error': 'Nenhum campo para atualizar'}), 400
    
    params.append(id)
    query = f"UPDATE torneios SET {', '.join(updates)} WHERE id = %s"
    
    sucesso = executar_query_commit(query, tuple(params))
    if sucesso:
        return jsonify({'message': 'Torneio atualizado com sucesso'})
    return jsonify({'error': 'Erro ao atualizar torneio'}), 500

@admin_features_bp.route('/torneios/<int:id>/avancar-fase', methods=['POST'])
def avancar_fase_torneio(id):
    """Avança participantes vencedores para a próxima fase"""
    data = request.get_json()
    vencedores_ids = data.get('vencedores_ids', [])  # Lista de IDs dos vencedores
    nome_fase_atual = data.get('nome_fase_atual', '')
    nome_proxima_fase = data.get('nome_proxima_fase', '')
    
    if not vencedores_ids:
        return jsonify({'error': 'Lista de vencedores é obrigatória'}), 400
    
    # Marcar perdedores como eliminados
    participantes = executar_query_fetchall(
        "SELECT usuario_id FROM torneio_participantes WHERE torneio_id = %s AND status = 'ativo'",
        (id,)
    )
    
    for p in participantes:
        if p[0] not in vencedores_ids:
            executar_query_commit(
                "UPDATE torneio_participantes SET status = 'eliminado' WHERE torneio_id = %s AND usuario_id = %s",
                (id, p[0])
            )
    
    # Registrar fase no histórico
    vencedores_str = ','.join(map(str, vencedores_ids))
    executar_query_commit(
        "INSERT INTO torneio_fases (torneio_id, nome_fase, ordem, status, vencedores_ids) VALUES (%s, %s, (SELECT COALESCE(MAX(ordem), 0) + 1 FROM torneio_fases WHERE torneio_id = %s), 'concluida', %s)",
        (id, nome_fase_atual or 'Fase', id, vencedores_str)
    )
    
    # Atualizar fase atual do torneio
    if nome_proxima_fase:
        executar_query_commit(
            "UPDATE torneios SET fase_atual = %s WHERE id = %s",
            (nome_proxima_fase, id)
        )
    
    return jsonify({
        'message': 'Fase avançada com sucesso',
        'vencedores': vencedores_ids,
        'proxima_fase': nome_proxima_fase
    })

@admin_features_bp.route('/torneios/<int:id>/finalizar', methods=['POST'])
def finalizar_torneio(id):
    """Finaliza o torneio definindo o vencedor"""
    data = request.get_json()
    vencedor_id = data.get('vencedor_id')
    
    if not vencedor_id:
        return jsonify({'error': 'ID do vencedor é obrigatório'}), 400
    
    # Verificar se o vencedor está no torneio
    participante = executar_query_fetchall(
        "SELECT id FROM torneio_participantes WHERE torneio_id = %s AND usuario_id = %s",
        (id, vencedor_id)
    )
    
    if not participante:
        return jsonify({'error': 'Vencedor não está inscrito no torneio'}), 404
    
    # Marcar todos exceto o vencedor como eliminados
    executar_query_commit(
        "UPDATE torneio_participantes SET status = 'eliminado' WHERE torneio_id = %s AND usuario_id != %s",
        (id, vencedor_id)
    )
    
    # Finalizar torneio
    sucesso = executar_query_commit(
        "UPDATE torneios SET status = 'finalizado', vencedor_id = %s, fase_atual = 'finalizado' WHERE id = %s",
        (vencedor_id, id)
    )
    
    if sucesso:
        # Buscar prêmio do torneio
        torneio = executar_query_fetchall("SELECT premio FROM torneios WHERE id = %s", (id,))
        premio = torneio[0][0] if torneio and torneio[0][0] else 0
        
        # Adicionar prêmio ao vencedor se houver
        if premio > 0:
            executar_query_commit(
                "UPDATE usuarios SET pontos = pontos + %s WHERE id = %s",
                (premio, vencedor_id)
            )
        
        return jsonify({
            'message': 'Torneio finalizado com sucesso',
            'vencedor_id': vencedor_id,
            'premio': premio
        })
    
    return jsonify({'error': 'Erro ao finalizar torneio'}), 500

@admin_features_bp.route('/torneios/<int:id>/fases', methods=['GET'])
def listar_fases_torneio(id):
    """Lista todas as fases do torneio"""
    fases = executar_query_fetchall(
        "SELECT id, nome_fase, ordem, status, vencedores_ids FROM torneio_fases WHERE torneio_id = %s ORDER BY ordem",
        (id,)
    )
    
    res = []
    if fases:
        for f in fases:
            res.append({
                'id': f[0],
                'nome_fase': f[1],
                'ordem': f[2],
                'status': f[3],
                'vencedores_ids': f[4].split(',') if f[4] else []
            })
    
    return jsonify(res)

@admin_features_bp.route('/torneios/<int:id>', methods=['DELETE'])
def remover_torneio(id):
    """Remove um torneio e seus dados relacionados"""
    try:
        # 1. Remover fases do torneio
        executar_query_commit("DELETE FROM torneio_fases WHERE torneio_id = %s", (id,))
        
        # 2. Remover participantes do torneio
        executar_query_commit("DELETE FROM torneio_participantes WHERE torneio_id = %s", (id,))
        
        # 3. Remover o torneio
        sucesso = executar_query_commit("DELETE FROM torneios WHERE id = %s", (id,))
        
        if sucesso:
            return jsonify({'message': 'Torneio removido com sucesso'})
        else:
            return jsonify({'error': 'Não foi possível remover o torneio do banco de dados'}), 500
    except Exception as e:
        print(f"Erro ao remover torneio {id}: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500
