@echo off
title Painel de Rastreio - Servidor na Rede Local (Wi-Fi)
cd /d "%~dp0"
echo ======================================================
echo Iniciando o Painel de Rastreio e Frete para o celular...
echo ======================================================
rem Escuta na rede local: qualquer aparelho do mesmo Wi-Fi pode abrir o painel (use so em casa).
rem O endereco para o celular aparece no log de inicio (http://IP-do-PC:8000).
set SERVER_HOST=0.0.0.0
if exist "Arquivos\venv\Scripts\python.exe" (
    "Arquivos\venv\Scripts\python.exe" run.py
) else (
    python run.py
)
pause
