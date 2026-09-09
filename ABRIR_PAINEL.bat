@echo off
title Painel de Rastreio - Servidor Local
cd /d "%~dp0"
echo Iniciando o Servidor de Rastreio...
if exist "Arquivos\venv\Scripts\python.exe" (
    "Arquivos\venv\Scripts\python.exe" "Arquivos\servidor_rastreio.py"
) else (
    python "Arquivos\servidor_rastreio.py"
)
pause
