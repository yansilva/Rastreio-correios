@echo off
title Painel de Rastreio - Servidor Local
cd /d "%~dp0"
echo ======================================================
echo Iniciando o Painel de Rastreio e Frete...
echo ======================================================
if exist "Arquivos\venv\Scripts\python.exe" (
    "Arquivos\venv\Scripts\python.exe" run.py
) else (
    python run.py
)
pause
