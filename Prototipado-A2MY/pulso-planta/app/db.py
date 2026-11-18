import random
from sqlmodel import SQLModel, Session, create_engine, select
from .models import Equipo, Mantencion, Lectura, Evento

engine = create_engine("sqlite:///pulso.db", connect_args={"check_same_thread": False})


def get_session():
    with Session(engine) as s:
        yield s


def init_db():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        if s.exec(select(Equipo)).first():
            return
        # id, nombre, fabricante, modelo, año modelo, año fab, país, serie, zona, horas, estado
        equipos = [
            ("LL-01", "Llenadora rotativa", "KHS GmbH", "Innofill DRV-60", "2019", "2018", "Alemania", "KHS-60-8841", "Línea 1", 12480, 0),
            ("TP-02", "Taponadora", "Sidel SA", "Cappingmaster C20", "2020", "2020", "Francia", "SDL-C20-3310", "Línea 1", 9310, 0),
            ("EQ-03", "Etiquetadora", "Krones AG", "Contiroll 570", "2016", "2015", "Alemania", "KRN-570-0927", "Línea 2", 15220, 0),
            ("CT-04", "Cinta transportadora", "Rexnord", "TableTop 882", "2014", "2013", "Estados Unidos", "RXN-882-5502", "Línea 2", 20110, 1),
        ]
        for d in equipos:
            s.add(Equipo(id=d[0], nombre=d[1], fabricante=d[2], modelo=d[3], anio_modelo=d[4],
                         anio_fab=d[5], pais=d[6], serie=d[7], zona=d[8], horas=d[9], estado=d[10]))
            for i in range(24):
                base = 2.2 + random.random() * .5
                if d[0] == "CT-04":
                    base += max(0, i - 10) * .2
                s.add(Lectura(equipo_id=d[0], rms=round(base, 2)))
        mants = [
            ("LL-01", "2026-09-24", "Preventivo", "Terminado", "R. Fuentes", "Cambio de sellos y lubricación"),
            ("LL-01", "2026-03-12", "Preventivo", "Terminado", "A. Rojas", "Revisión de válvulas de llenado"),
            ("TP-02", "2026-10-17", "Preventivo", "Terminado", "C. Vega", "Ajuste de cabezales"),
            ("EQ-03", "2026-07-30", "Correctivo", "Terminado", "A. Rojas", "Reemplazo de rodillo de encolado"),
            ("CT-04", "2026-06-27", "Preventivo", "Terminado", "R. Fuentes", "Lubricación de rodamientos"),
            ("CT-04", "2026-11-02", "Preventivo", "En proceso", "C. Vega", "Cambio de cadena (pendiente repuesto)"),
        ]
        for m in mants:
            s.add(Mantencion(equipo_id=m[0], fecha=m[1], tipo=m[2], estado=m[3], tecnico=m[4], nota=m[5]))
        s.add(Evento(usuario="SISTEMA", equipo_id="CT-04", texto="Vibración sobre umbral de alerta (4.9 mm/s)"))
        s.commit()
