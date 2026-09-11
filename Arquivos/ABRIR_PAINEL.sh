#!/usr/bin/env bash
# Redireciona para o script de inicialização principal na raiz do projeto
cd "$(dirname "$0")/.."
exec ./abrir_painel.sh "$@"
