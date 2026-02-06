
import pg8000
import os
import sys

# Adicionar o diretório pai ao sys.path para importar database_config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database_config import DB_CONFIG

def migrate():
    conn = pg8000.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    queries = [
        # Renomear coluna data_recebimento para data_registro se ela existir e data_registro não existir
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cofre_historico' AND column_name='data_recebimento') 
            AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cofre_historico' AND column_name='data_registro') THEN
                ALTER TABLE cofre_historico RENAME COLUMN data_recebimento TO data_registro;
            END IF;
        END $$;
        """,
        # Garantir que a coluna data_registro existe caso nenhuma das duas exista
        "ALTER TABLE cofre_historico ADD COLUMN IF NOT EXISTS data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"
    ]
    
    try:
        for query in queries:
            print(f"Executando: {query[:100]}...")
            cursor.execute(query)
        conn.commit()
        print("\n✅ Correção de colunas do cofre concluída com sucesso!")
    except Exception as e:
        print(f"\n❌ Erro na migração: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
