#!/usr/bin/env bash
# Script de inicialização multiplataforma para Linux e macOS

cd "$(dirname "$0")"

echo "======================================================"
echo "  Iniciando o Painel de Rastreio Correios & Tiny ERP"
echo "======================================================"

PYTHON_EXEC=""

if [ -f ".venv/bin/python" ]; then
    PYTHON_EXEC=".venv/bin/python"
elif [ -f "venv/bin/python" ]; then
    PYTHON_EXEC="venv/bin/python"
elif [ -f "Arquivos/venv/bin/python" ]; then
    PYTHON_EXEC="Arquivos/venv/bin/python"
else
    PYTHON_EXEC="python3"
fi

echo "Usando interpretador: $PYTHON_EXEC"
$PYTHON_EXEC run.py "$@"
