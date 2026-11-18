"""Simula el sensor de vibración. Uso:
   python simulador.py                 -> lecturas normales para todos los equipos
   python simulador.py CT-04 --anomalia -> sube la vibración de un equipo
"""
import json, random, sys, time, urllib.request

URL, KEY = "http://127.0.0.1:8000/api/lecturas", "sensor-demo"
EQUIPOS = ["LL-01", "TP-02", "EQ-03", "CT-04"]


def enviar(eid, rms):
    req = urllib.request.Request(URL, json.dumps({"equipo_id": eid, "rms": rms}).encode(),
                                 {"Content-Type": "application/json", "x-api-key": KEY})
    print(eid, rms, urllib.request.urlopen(req).read().decode())


if __name__ == "__main__":
    objetivo = sys.argv[1] if len(sys.argv) > 1 else None
    anomalia = "--anomalia" in sys.argv
    rms_obj = 4.8
    while True:
        for e in EQUIPOS:
            if anomalia and e == objetivo:
                rms_obj += random.uniform(.3, .9)
                enviar(e, round(rms_obj, 2))
            else:
                enviar(e, round(random.uniform(2.0, 2.8), 2))
        time.sleep(3)
