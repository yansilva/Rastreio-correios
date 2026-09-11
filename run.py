"""Ponto de entrada principal do Rastreio-correios.

Inicia o servidor web local e disponibiliza o painel operacional de rastreamento
e cotação de frete.

Uso:
    python run.py
"""
import sys
from pathlib import Path

# Assegura que o diretório 'Arquivos' esteja no PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent
DIR_ARQUIVOS = BASE_DIR / "Arquivos"

if str(DIR_ARQUIVOS) not in sys.path:
    sys.path.insert(0, str(DIR_ARQUIVOS))

from server import ServerConfig, iniciar_servidor

if __name__ == "__main__":
    config = ServerConfig.from_env(base_dir=BASE_DIR)
    iniciar_servidor(config=config, abrir_browser=True)
