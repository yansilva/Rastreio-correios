@echo off
title Painel de Rastreio - Servidor Local
cd /d "%~dp0"
echo ======================================================
echo Iniciando o Painel de Rastreio e Frete...
echo ======================================================
rem Escuta so neste PC (127.0.0.1). Para abrir no celular pelo Wi-Fi, use ABRIR_PAINEL_CELULAR.bat.
if exist "Arquivos\venv\Scripts\python.exe" (
    "Arquivos\venv\Scripts\python.exe" run.py
) else (
    python run.py
)
pause
