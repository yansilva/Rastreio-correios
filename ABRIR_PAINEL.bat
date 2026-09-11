@echo off
title Painel de Rastreio - Servidor Local
cd /d "%~dp0"

echo ======================================================
echo   Iniciando o Painel de Rastreio Correios & Tiny ERP
echo ======================================================

set PYTHON_EXEC=

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXEC=.venv\Scripts\python.exe"
) else if exist "venv\Scripts\python.exe" (
    set "PYTHON_EXEC=venv\Scripts\python.exe"
) else if exist "Arquivos\venv\Scripts\python.exe" (
    set "PYTHON_EXEC=Arquivos\venv\Scripts\python.exe"
) else (
    set "PYTHON_EXEC=python"
)

echo Usando interpretador: %PYTHON_EXEC%
%PYTHON_EXEC% run.py %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] O servidor encerrou com codigo %ERRORLEVEL%.
    echo Verifique o diagnostico executando: %PYTHON_EXEC% run.py --check
    echo.
    pause
)
