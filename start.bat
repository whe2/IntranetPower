@echo off
chcp 65001 > nul
title THE HUB - Intranet Server
echo.
echo ============================================
echo   THE HUB - Servidor de Intranet Corporativa
echo ============================================
echo.
echo [*] Iniciando servidor FastAPI en http://127.0.0.1:8000
echo [*] Presiona CTRL+C para detener el servidor
echo.

cd /d "%~dp0"
call venv\Scripts\activate.bat

echo [*] Verificando base de datos...
python init_db.py

echo.
echo [*] Iniciando servidor...
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
pause
