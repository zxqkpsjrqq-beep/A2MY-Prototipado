#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python simulador.py CT-04 --anomalia
