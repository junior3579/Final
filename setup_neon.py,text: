import os
import sys

# Adicionar o diretório atual ao path para poder importar o backend
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.database_config import criar_tabelas_remoto

if __name__ == "__main__":
    print("--- Inicializador de Banco de Dados Neon ---")
    try:
        criar_tabelas_remoto()
        print("\n✅ Configuração concluída com sucesso!")
        print("As tabelas foram criadas ou já existiam no seu projeto Neon.")
    except Exception as e:
        print(f"\n❌ Ocorreu um erro durante a configuração: {e}")
        print("\nVerifique se suas credenciais no arquivo .env ou no database_config.py estão corretas.")
