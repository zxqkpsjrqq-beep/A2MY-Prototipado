#!/bin/bash
cd "$(dirname "$0")"
command -v python3 >/dev/null || { echo "Instala Python 3 desde python.org"; exit 1; }
[ -d venv ] || { echo "Preparando por primera vez..."; python3 -m venv venv; }
source venv/bin/activate
pip install -q -r requirements.txt
echo "Pulso Planta: http://localhost:8000  (celular: http://TU-IP:8000)"
(sleep 3; (open http://localhost:8000 || xdg-open http://localhost:8000) >/dev/null 2>&1) &
uvicorn app.main:app --host 0.0.0.0 --port 8000
