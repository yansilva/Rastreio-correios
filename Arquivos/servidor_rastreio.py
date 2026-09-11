"""Servidor web local do Painel de Rastreio e Frete.

Este módulo serve como fachada retrocompatível delegando para o pacote modular `Arquivos.server`.

Para execução direta recomendada a partir da raiz do projeto:
    python run.py
ou:
    python Arquivos/servidor_rastreio.py
"""
import os
import sys
from pathlib import Path

# Garante que 'Arquivos' esteja no sys.path para importações relativas e módulos irmãos
DIR_ARQUIVOS = Path(__file__).resolve().parent
if str(DIR_ARQUIVOS) not in sys.path:
    sys.path.insert(0, str(DIR_ARQUIVOS))

from server import (
    RastreioRequestHandler,
    ServerConfig,
    abrir_navegador,
    iniciar_servidor,
)

# Símbolos legados preservados para compatibilidade
PORT = 8000
HTML_FILE = "relatorio_rastreio.html"
RastreioHandler = RastreioRequestHandler
open_browser = abrir_navegador

if __name__ == "__main__":
    # Garante que o diretório de trabalho seja a raiz do projeto para consistência
    raiz = DIR_ARQUIVOS.parent
    os.chdir(str(raiz))

    config = ServerConfig.from_env(base_dir=raiz)
    iniciar_servidor(config=config, abrir_browser=True)
