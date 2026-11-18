@echo off
cd /d "%~dp0"
call venv\Scripts\activate
echo Simulando sensor con falla creciente en CT-04. Cierra la ventana para detener.
python simulador.py CT-04 --anomalia
pause
