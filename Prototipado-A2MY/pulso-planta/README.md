# Pulso Planta – prototipo en Python

App de terreno para mantenimiento predictivo (FastAPI + SQLite + plantillas Jinja2, mobile-first).

## Ejecutar
```
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0
```
Abre http://localhost:8000 (desde el celular: http://IP-DEL-PC:8000, misma red WiFi).
La cámara del QR necesita HTTPS en el celular; para pruebas usa un túnel (ngrok o cloudflared) o el campo manual de ID.

## Simular el sensor (otra terminal)
```
python simulador.py                    # lecturas normales
python simulador.py CT-04 --anomalia   # sube la vibración de CT-04 hasta falla
```

## Estructura
- app/models.py  tablas: Usuario, Equipo, Mantencion, Lectura, Evento (registro total)
- app/db.py      conexión y datos de ejemplo
- app/main.py    rutas, máquina de estados y API del sensor (POST /api/lecturas, header x-api-key)
- app/templates  pantallas (HTML con Jinja2); app/static/style.css estilos
- simulador.py   sensor falso

## Pendiente para producción
Login corporativo, notificaciones push/SMS reales, PostgreSQL + TimescaleDB, MQTT para sensores,
umbrales por máquina, roles/permisos, modo sin conexión (PWA), pruebas automáticas y HTTPS.
