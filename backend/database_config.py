
import sqlite3
import os
from datetime import datetime, timezone

# Caminho para o banco de dados SQLite local
DB_PATH = os.path.join(os.path.dirname(__file__), "stake_arena_local.db")

def conectar_banco_local():
    try:
        conn = sqlite3.connect(DB_PATH)
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco local: {e}")
        return None

def executar_query_fetchall(query, params=()):
    # Converter sintaxe PostgreSQL (%s) para SQLite (?)
    query = query.replace("%s", "?")
    conn = conectar_banco_local()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchall()
        return result
    except Exception as e:
        print(f"Erro na query: {e}")
        return None
    finally:
        conn.close()

def executar_query_commit(query, params=()):
    # Converter sintaxe PostgreSQL (%s) para SQLite (?)
    query = query.replace("%s", "?")
    conn = conectar_banco_local()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro na query: {e}")
        return False
    finally:
        conn.close()

def criar_tabelas_remoto():
    # Mantendo o nome da função para compatibilidade com main.py
    queries = [
        '''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            pontos INTEGER NOT NULL,
            whatsapp TEXT,
            pix_tipo TEXT,
            pix_chave TEXT,
            last_seen TIMESTAMP,
            posicao INTEGER
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS salas (
            id_sala INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_sala TEXT NOT NULL,
            valor_inicial INTEGER NOT NULL,
            criador TEXT NOT NULL,
            jogadores TEXT,
            whatsapp TEXT,
            categoria_id INTEGER,
            FOREIGN KEY(categoria_id) REFERENCES categorias(id)
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS apostas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_sala INTEGER NOT NULL,
            id_usuario INTEGER NOT NULL,
            valor_aposta INTEGER NOT NULL,
            status TEXT DEFAULT 'pendente',
            resultado TEXT DEFAULT 'pendente',
            FOREIGN KEY(id_sala) REFERENCES salas(id_sala),
            FOREIGN KEY(id_usuario) REFERENCES usuarios(id)
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            valor INTEGER NOT NULL,
            status TEXT DEFAULT 'pendente',
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(id_usuario) REFERENCES usuarios(id)
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS torneios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            status TEXT DEFAULT 'inscricao', -- inscricao, em_andamento, finalizado
            vencedor_id INTEGER,
            FOREIGN KEY(vencedor_id) REFERENCES usuarios(id)
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS torneio_participantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            torneio_id INTEGER NOT NULL,
            usuario_id INTEGER NOT NULL,
            status TEXT DEFAULT 'ativo', -- ativo, eliminado
            FOREIGN KEY(torneio_id) REFERENCES torneios(id),
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
        '''
    ]
    for q in queries:
        executar_query_commit(q)

def reordenar_posicoes():
    query_usuarios = "SELECT id FROM usuarios ORDER BY posicao ASC, id ASC"
    usuarios = executar_query_fetchall(query_usuarios)
    
    if not usuarios:
        return
    
    for index, (user_id,) in enumerate(usuarios, start=1):
        executar_query_commit(
            "UPDATE usuarios SET posicao = ? WHERE id = ?",
            (index, user_id)
        )

def obter_proxima_posicao_vaga():
    result = executar_query_fetchall("SELECT posicao FROM usuarios ORDER BY posicao")
    posicoes_ocupadas = {r[0] for r in result if r[0] is not None}
    
    pos = 1
    while pos in posicoes_ocupadas:
        pos += 1
    return pos

def obter_menor_id_vago():
    """
    Encontra o menor ID disponível na tabela usuarios para reutilização.
    """
    result = executar_query_fetchall("SELECT id FROM usuarios ORDER BY id")
    ids_ocupados = {r[0] for r in result}
    
    id_vago = 1
    while id_vago in ids_ocupados:
        id_vago += 1
    return id_vago

def atualizar_atividade_usuario(id_usuario):
    executar_query_commit(
        "UPDATE usuarios SET last_seen = ? WHERE id = ?",
        (datetime.now(timezone.utc).isoformat(), id_usuario)
    )

def listar_usuarios_online(minutos=5):
    from datetime import timedelta
    limite = (datetime.now(timezone.utc) - timedelta(minutes=minutos)).isoformat()
    result = executar_query_fetchall(
        "SELECT nome, last_seen FROM usuarios WHERE last_seen >= ? ORDER BY last_seen DESC",
        (limite,)
    )
    if not result:
        return []
    
    usuarios_online = []
    for nome, last_seen_str in result:
        if last_seen_str:
            try:
                last_seen = datetime.fromisoformat(last_seen_str)
                last_seen_local = last_seen - timedelta(hours=3)
                usuarios_online.append({
                    'nome': nome,
                    'last_seen': last_seen_local.strftime('%H:%M:%S')
                })
            except:
                continue
    
    return usuarios_online
