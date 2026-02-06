
import psycopg2
from psycopg2 import pool
import os
from datetime import datetime, timezone

# Configuração do Neon Postgres
NEON_DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://neondb_owner:npg_V8qafPvicJO4@ep-crimson-queen-acirpfh4-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require")

# Pool de conexões para eficiência
try:
    connection_pool = psycopg2.pool.SimpleConnectionPool(
        1, 10, NEON_DATABASE_URL
    )
except Exception as e:
    print(f"Erro ao criar pool de conexões Neon: {e}")
    connection_pool = None

def conectar_banco_remoto():
    if not connection_pool:
        return None
    try:
        return connection_pool.getconn()
    except Exception as e:
        print(f"Erro ao obter conexão do pool: {e}")
        return None

def liberar_conexao(conn):
    if connection_pool and conn:
        connection_pool.putconn(conn)

def executar_query_fetchall(query, params=()):
    conn = conectar_banco_remoto()
    if not conn:
        return None
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchall()
            return result
    except Exception as e:
        print(f"Erro na query fetchall: {e}")
        return None
    finally:
        liberar_conexao(conn)

def executar_query_commit(query, params=()):
    conn = conectar_banco_remoto()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            conn.commit()
            return True
    except Exception as e:
        print(f"Erro na query commit: {e}")
        conn.rollback()
        return False
    finally:
        liberar_conexao(conn)

def criar_tabelas_remoto():
    queries = [
        '''
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
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
        CREATE TABLE IF NOT EXISTS categorias (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL UNIQUE
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS salas (
            id_sala SERIAL PRIMARY KEY,
            nome_sala TEXT NOT NULL,
            valor_inicial INTEGER NOT NULL,
            criador TEXT NOT NULL,
            jogadores TEXT,
            whatsapp TEXT,
            categoria_id INTEGER REFERENCES categorias(id)
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS apostas (
            id SERIAL PRIMARY KEY,
            id_sala INTEGER NOT NULL REFERENCES salas(id_sala),
            id_usuario INTEGER NOT NULL REFERENCES usuarios(id),
            valor_aposta INTEGER NOT NULL,
            status TEXT DEFAULT 'pendente',
            resultado TEXT DEFAULT 'pendente'
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS transacoes (
            id SERIAL PRIMARY KEY,
            id_usuario INTEGER NOT NULL REFERENCES usuarios(id),
            tipo TEXT NOT NULL,
            valor INTEGER NOT NULL,
            status TEXT DEFAULT 'pendente',
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS torneios (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            status TEXT DEFAULT 'inscricao',
            vencedor_id INTEGER REFERENCES usuarios(id)
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS torneio_participantes (
            id SERIAL PRIMARY KEY,
            torneio_id INTEGER NOT NULL REFERENCES torneios(id),
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
            status TEXT DEFAULT 'ativo'
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
            "UPDATE usuarios SET posicao = %s WHERE id = %s",
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
    result = executar_query_fetchall("SELECT id FROM usuarios ORDER BY id")
    ids_ocupados = {r[0] for r in result}
    
    id_vago = 1
    while id_vago in ids_ocupados:
        id_vago += 1
    return id_vago

def atualizar_atividade_usuario(id_usuario):
    executar_query_commit(
        "UPDATE usuarios SET last_seen = %s WHERE id = %s",
        (datetime.now(timezone.utc), id_usuario)
    )

def listar_usuarios_online(minutos=5):
    from datetime import timedelta
    limite = datetime.now(timezone.utc) - timedelta(minutes=minutos)
    result = executar_query_fetchall(
        "SELECT nome, last_seen FROM usuarios WHERE last_seen >= %s ORDER BY last_seen DESC",
        (limite,)
    )
    if not result:
        return []
    
    usuarios_online = []
    for nome, last_seen in result:
        if last_seen:
            try:
                # last_seen já deve ser um objeto datetime vindo do psycopg2
                last_seen_local = last_seen - timedelta(hours=3)
                usuarios_online.append({
                    'nome': nome,
                    'last_seen': last_seen_local.strftime('%H:%M:%S')
                })
            except:
                continue
    
    return usuarios_online
