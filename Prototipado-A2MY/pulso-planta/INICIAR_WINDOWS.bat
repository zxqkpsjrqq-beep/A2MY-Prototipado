@echo off
cd /d "%~dp0"
title Pulso Planta
where python >nul 2>nul
if errorlevel 1 (
  echo No se encontro Python. Instalalo desde https://www.python.org/downloads/
  echo IMPORTANTE: marca la casilla "Add Python to PATH" al instalar.
  pause
  exit /b
)
if not exist venv (
  echo Preparando por primera vez, esto demora 1 o 2 minutos...
  python -m venv venv
)
call venv\Scripts\activate
pip install -q -r requirements.txt
echo.
echo ======================================================
echo  Pulso Planta funcionando. NO cierres esta ventana.
echo  En este computador:  http://localhost:8000
echo  En el celular (misma WiFi) usa tu IP de abajo + :8000
echo ======================================================
ipconfig | findstr "IPv4"
echo.
start "" cmd /c "timeout /t 4 >nul & start http://localhost:8000"
uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
