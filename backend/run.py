"""
Ponto de entrada do backend MiroFish
"""

import os
import sys

# Corrigir encoding no console Windows: configurar UTF-8 antes de qualquer import
if sys.platform == 'win32':
    # Definir variavel de ambiente para garantir UTF-8
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    # Reconfigurar streams de saida para UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Adicionar diretorio raiz do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.config import Config


def main():
    """Funcao principal"""
    # Validar configuracao
    errors = Config.validate()
    if errors:
        print("Erro de configuracao:")
        for err in errors:
            print(f"  - {err}")
        print("\nVerifique as configuracoes no arquivo .env")
        sys.exit(1)

    # Criar aplicacao
    app = create_app()

    # Obter configuracao de execucao
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5001))
    debug = Config.DEBUG

    # Iniciar servico
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    main()
