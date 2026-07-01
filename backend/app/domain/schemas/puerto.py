from pydantic import BaseModel, field_validator
from datetime import datetime


class SalidaPuerto(BaseModel):
    id:          int
    nombre:      str
    descripcion: str | None
    created_at:  datetime
    total:       int = 0

    model_config = {"from_attributes": True}


class SalidaPuertoMini(BaseModel):
    """Representación reducida de un Puerto — usada donde solo se necesita
    identificarlo (por ejemplo dentro de un Usuario o transferencia)."""
    id:     int
    nombre: str

    model_config = {"from_attributes": True}


class DatosAsignarPuertos(BaseModel):
    """Reemplaza la lista de puertos asignados a un usuario operador."""
    puerto_ids: list[int]

    @field_validator("puerto_ids")
    @classmethod
    def sin_duplicados(cls, v: list[int]) -> list[int]:
        return list(dict.fromkeys(v))


class DatosCrearPuerto(BaseModel):
    nombre:      str
    descripcion: str | None = None

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El nombre no puede estar vacío.")
        if len(v) > 255:
            raise ValueError("El nombre no puede superar 255 caracteres.")
        return v
