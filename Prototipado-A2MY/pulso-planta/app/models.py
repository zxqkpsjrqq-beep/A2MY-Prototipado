from datetime import datetime
from typing import Optional
import annotationlib
from sqlmodel import SQLModel, Field
from sqlmodel.main import SQLModelMetaclass

_orig_new = SQLModelMetaclass.__new__


def _patched_new(cls, name, bases, class_dict, **kwargs):
    annotate = annotationlib.get_annotate_from_class_namespace(class_dict)
    if annotate is not None and "__annotations__" not in class_dict:
        class_dict["__annotations__"] = annotationlib.call_annotate_function(
            annotate, format=annotationlib.Format.VALUE
        )
    return _orig_new(cls, name, bases, class_dict, **kwargs)


SQLModelMetaclass.__new__ = _patched_new


class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    codigo: str = Field(index=True, unique=True)  # ID de usuario de planta
    nombre: str
    correo: str  # correo de empresa
    area: str    # área encargada


class Equipo(SQLModel, table=True):
    id: str = Field(primary_key=True)  # lo que va dentro del QR
    nombre: str
    fabricante: str
    modelo: str
    anio_modelo: str
    anio_fab: str
    pais: str
    serie: str
    zona: str
    horas: int = 0
    estado: int = 0  # 0 normal, 1 posible anomalía, 2 falla potencial, 3 técnico en camino
    tecnico: Optional[str] = None


class Mantencion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    equipo_id: str = Field(index=True)
    fecha: str
    tipo: str     # Preventivo / Correctivo / Inspección
    estado: str   # "En proceso" o "Terminado"
    tecnico: str
    nota: str


class Lectura(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    equipo_id: str = Field(index=True)
    rms: float  # mm/s
    ts: datetime = Field(default_factory=datetime.now)


class Evento(SQLModel, table=True):  # "registro total" / auditoría
    id: Optional[int] = Field(default=None, primary_key=True)
    ts: datetime = Field(default_factory=datetime.now)
    usuario: str
    equipo_id: str
    texto: str