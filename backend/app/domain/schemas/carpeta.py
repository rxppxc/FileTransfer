from pydantic import BaseModel, field_validator
from datetime import datetime


class SalidaPuertoBasicoCarpeta(BaseModel):
    id:     int
    nombre: str
    model_config = {"from_attributes": True}


class SalidaCarpeta(BaseModel):
    id:          int
    nombre:      str
    descripcion: str | None
    created_at:  datetime
    total:       int = 0
    puerto_id:   int | None = None
    puerto:      SalidaPuertoBasicoCarpeta | None = None

    model_config = {"from_attributes": True}


class DatosCrearCarpeta(BaseModel):
    nombre:      str
    descripcion: str | None = None
    puerto_id:   int | None = None

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El nombre no puede estar vacío.")
        if len(v) > 255:
            raise ValueError("El nombre no puede superar 255 caracteres.")
        return v
