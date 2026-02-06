
import os
import sys

# Adiciona o diretório atual ao path para que o pacote 'backend' seja encontrado
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.main import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
