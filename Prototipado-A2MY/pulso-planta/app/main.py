import os
from datetime import date
from fastapi import FastAPI, Request, Form, Depends, Header, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlmodel import Session, select
from starlette.middleware.sessions import SessionMiddleware

from .db import get_session, init_db
from .models import Usuario, Equipo, Mantencion, Lectura, Evento

LIM_ALERTA, LIM_CRITICO = 4.5, 7.1  # mm/s RMS (referencial ISO 20816): calibrar por máquina
ESTADOS = ["Normal", "Posible anomalía", "Falla potencial", "Técnico en camino"]
ENC = {"nombre": "Marcela Soto", "cargo": "Encargada de planta", "fono": "+56955550142"}
TECNICOS = ["R. Fuentes · Mecánico", "A. Rojas · Mecánico", "C. Vega · Lubricación"]
API_KEY = os.getenv("API_KEY", "sensor-demo")
BASE = os.path.dirname(__file__)

app = FastAPI(title="Pulso Planta")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET", "cambiar-en-produccion"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE, "templates"))


@app.on_event("startup")
def _start():
    init_db()


class NoAuth(Exception):
    pass


@app.exception_handler(NoAuth)
async def _noauth(request, exc):
    return RedirectResponse("/login", 303)


def user(request: Request, s: Session = Depends(get_session)):
    u = s.exec(select(Usuario).where(Usuario.codigo == request.session.get("u"))).first()
    if not u:
        raise NoAuth()
    return u


def page(request, name, u=None, **ctx):
    ctx.update(u=u, ESTADOS=ESTADOS, msg=request.session.pop("msg", None), enc=ENC, LA=LIM_ALERTA, LC=LIM_CRITICO)
    return templates.TemplateResponse(request, name, ctx)


def log(s, u, equipo, texto):
    s.add(Evento(usuario=u if isinstance(u, str) else u.codigo, equipo_id=equipo, texto=texto))


def ultima(s, eid):
    f = s.exec(select(Mantencion.fecha).where(Mantencion.equipo_id == eid, Mantencion.estado == "Terminado")
               .order_by(Mantencion.fecha.desc())).first()
    return f or "Sin registro"


def ultimo_rms(s, eid):
    return s.exec(select(Lectura.rms).where(Lectura.equipo_id == eid).order_by(Lectura.id.desc())).first() or 0.0


def y(v):
    return round(122 - v / 9 * 114)


def puntos(lect):
    v = [l.rms for l in lect]
    n = max(len(v) - 1, 1)
    return " ".join(f"{10 + i * 340 / n:.0f},{y(x)}" for i, x in enumerate(v))


# ---------- sesión ----------
@app.get("/login")
def login_form(request: Request):
    return page(request, "login.html")


@app.post("/login")
def login(request: Request, codigo: str = Form(...), nombre: str = Form(...), correo: str = Form(...),
          area: str = Form(...), s: Session = Depends(get_session)):
    codigo = codigo.strip().upper()
    u = s.exec(select(Usuario).where(Usuario.codigo == codigo)).first()
    if not u:
        u = Usuario(codigo=codigo, nombre=nombre.strip(), correo=correo.strip(), area=area)
        s.add(u)
    log(s, codigo, "—", "Inició sesión")
    s.commit()
    request.session["u"] = codigo
    return RedirectResponse("/", 303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", 303)


# ---------- pantallas ----------
@app.get("/")
def equipos(request: Request, u=Depends(user), s: Session = Depends(get_session)):
    rows = [(e, ultima(s, e.id), ultimo_rms(s, e.id)) for e in s.exec(select(Equipo)).all()]
    c = [sum(1 for r in rows if r[0].estado == 0), sum(1 for r in rows if r[0].estado == 1),
         sum(1 for r in rows if r[0].estado >= 2)]
    return page(request, "equipos.html", u, rows=rows, c=c, tab="eq")


@app.get("/equipo/{eid}")
def detalle(eid: str, request: Request, tab: str = "ficha", u=Depends(user), s: Session = Depends(get_session)):
    e = s.get(Equipo, eid)
    if not e:
        raise HTTPException(404, "Equipo no existe")
    mant = s.exec(select(Mantencion).where(Mantencion.equipo_id == eid).order_by(Mantencion.fecha.desc())).all()
    lect = s.exec(select(Lectura).where(Lectura.equipo_id == eid).order_by(Lectura.id.desc()).limit(24)).all()[::-1]
    return page(request, "detalle.html", u, e=e, mant=mant, sub=tab, ult=ultima(s, eid), pts=puntos(lect),
                rms=lect[-1].rms if lect else 0, ya=y(LIM_ALERTA), yc=y(LIM_CRITICO), tecnicos=TECNICOS,
                eq_id=eid, tab="eq")


def volver(eid, tab="ficha"):
    return RedirectResponse(f"/equipo/{eid}?tab={tab}", 303)


@app.post("/equipo/{eid}/revision")
def revision(eid: str, resultado: str = Form(...), u=Depends(user), s: Session = Depends(get_session)):
    e = s.get(Equipo, eid)
    if resultado == "falsa":
        e.estado = 0
        s.add(Lectura(equipo_id=eid, rms=2.3))
        log(s, u, eid, "Descartó falsa alarma")
    else:
        e.estado = 2
        log(s, u, eid, "Confirmó falla potencial en terreno")
    s.add(e)
    s.commit()
    return volver(eid)


@app.post("/equipo/{eid}/llamar")
def llamar(eid: str, tecnico: str = Form(...), u=Depends(user), s: Session = Depends(get_session)):
    e = s.get(Equipo, eid)
    e.estado, e.tecnico = 3, tecnico
    s.add(e)
    s.add(Mantencion(equipo_id=eid, fecha=date.today().isoformat(), tipo="Correctivo", estado="En proceso",
                     tecnico=tecnico.split(" · ")[0], nota="OT por falla potencial detectada"))
    log(s, u, eid, f"Llamó a técnico: {tecnico}")
    s.commit()
    return volver(eid)


@app.post("/equipo/{eid}/cerrar")
def cerrar(eid: str, u=Depends(user), s: Session = Depends(get_session)):
    e = s.get(Equipo, eid)
    e.estado, e.tecnico = 0, None
    for m in s.exec(select(Mantencion).where(Mantencion.equipo_id == eid, Mantencion.estado == "En proceso")).all():
        m.estado, m.fecha = "Terminado", date.today().isoformat()
        s.add(m)
    s.add(e)
    s.add(Lectura(equipo_id=eid, rms=2.0))
    log(s, u, eid, "Cerró reparación, equipo normal")
    s.commit()
    return volver(eid, "mant")


@app.post("/equipo/{eid}/mantencion")
def nueva_mant(eid: str, tipo: str = Form(...), nota: str = Form(...), u=Depends(user), s: Session = Depends(get_session)):
    s.add(Mantencion(equipo_id=eid, fecha=date.today().isoformat(), tipo=tipo, estado="En proceso", tecnico=u.nombre, nota=nota))
    log(s, u, eid, f"Registró mantención: {nota}")
    s.commit()
    return volver(eid, "mant")


@app.get("/escanear")
def escanear(request: Request, u=Depends(user), s: Session = Depends(get_session)):
    return page(request, "escanear.html", u, equipos=s.exec(select(Equipo)).all(), tab="sc")


@app.get("/qr/{eid}")  # el QR de la máquina contiene solo el ID (o esta URL)
def qr(eid: str, u=Depends(user), s: Session = Depends(get_session)):
    if not s.get(Equipo, eid):
        request_msg = "QR no reconocido"
        raise HTTPException(404, request_msg)
    log(s, u, eid, "Escaneó QR y abrió ficha")
    s.commit()
    return volver(eid)


@app.get("/nuevo")
def nuevo_form(request: Request, u=Depends(user)):
    return page(request, "nuevo.html", u, tab="sc")


@app.post("/nuevo")
def nuevo(request: Request, id: str = Form(...), nombre: str = Form(...), fabricante: str = Form(""),
          modelo: str = Form(""), pais: str = Form(""), anio_modelo: str = Form(""), anio_fab: str = Form(""),
          serie: str = Form(""), zona: str = Form("Sin zona"), u=Depends(user), s: Session = Depends(get_session)):
    eid = id.strip().upper()
    if s.get(Equipo, eid):
        request.session["msg"] = "Ya existe un equipo con ese ID"
        return RedirectResponse("/nuevo", 303)
    s.add(Equipo(id=eid, nombre=nombre, fabricante=fabricante or "—", modelo=modelo or "—", pais=pais or "—",
                 anio_modelo=anio_modelo or "—", anio_fab=anio_fab or "—", serie=serie or "—", zona=zona))
    log(s, u, eid, "Registró nuevo equipo")
    s.commit()
    return volver(eid)


@app.get("/alertas")
def alertas(request: Request, u=Depends(user), s: Session = Depends(get_session)):
    act = s.exec(select(Equipo).where(Equipo.estado > 0)).all()
    ev = s.exec(select(Evento).order_by(Evento.id.desc()).limit(15)).all()
    return page(request, "alertas.html", u, act=act, ev=ev, tab="al")


@app.get("/perfil")
def perfil(request: Request, u=Depends(user), s: Session = Depends(get_session)):
    ev = s.exec(select(Evento).where(Evento.usuario == u.codigo).order_by(Evento.id.desc())).all()
    return page(request, "perfil.html", u, ev=ev, tab="pf")


@app.post("/sos")
def sos(request: Request, tipo: str = Form(...), equipo: str = Form(""), u=Depends(user), s: Session = Depends(get_session)):
    log(s, u, equipo or "PLANTA", f"EMERGENCIA: {tipo} · alerta enviada a {ENC['nombre']}")
    s.commit()
    # TODO producción: enviar push/SMS/WhatsApp real a la encargada de planta
    request.session["msg"] = f"Alerta enviada a {ENC['nombre']}"
    return RedirectResponse(request.headers.get("referer", "/"), 303)


# ---------- API del sensor ----------
class LecturaIn(BaseModel):
    equipo_id: str
    rms: float


@app.post("/api/lecturas")
def recibir(l: LecturaIn, x_api_key: str = Header(""), s: Session = Depends(get_session)):
    if x_api_key != API_KEY:
        raise HTTPException(401, "API key inválida")
    e = s.get(Equipo, l.equipo_id)
    if not e:
        raise HTTPException(404, "Equipo no existe")
    s.add(Lectura(equipo_id=e.id, rms=l.rms))
    if l.rms >= LIM_CRITICO and e.estado < 2:
        e.estado = 2
        log(s, "SISTEMA", e.id, f"Vibración crítica ({l.rms} mm/s)")
    elif l.rms >= LIM_ALERTA and e.estado == 0:
        e.estado = 1
        log(s, "SISTEMA", e.id, f"Anomalía detectada ({l.rms} mm/s)")
        # TODO producción: notificación push a usuarios del área
    s.add(e)
    s.commit()
    return {"ok": True, "estado": ESTADOS[e.estado]}
