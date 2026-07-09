import re
from pydantic import BaseModel, field_validator
from datetime import datetime
from app.domain.models.transfer import EstadoTransferencia

_EMAIL_RE   = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
TITULO_MAX  = 255
MENSAJE_MAX = 2000


class SalidaArchivoTransferencia(BaseModel):
    id:            int
    original_name: str
    mime_type:     str | None
    size:          int
    es_original:   bool = True
    subido_por_id: int | None = None

    model_config = {"from_attributes": True}


class SalidaPuertoBasico(BaseModel):
    id:     int
    nombre: str
    model_config = {"from_attributes": True}


class SalidaCarpetaBasica(BaseModel):
    id:        int
    nombre:    str
    puerto_id: int | None = None
    puerto:    SalidaPuertoBasico | None = None
    model_config = {"from_attributes": True}


class SalidaTransferencia(BaseModel):
    id:            int
    token:         str
    title:         str | None
    message:       str | None
    recipient:     str | None
    expires_at:    datetime | None
    downloads:     int
    max_downloads: int | None
    status:        EstadoTransferencia
    created_at:    datetime
    files:         list[SalidaArchivoTransferencia] = []
    total_size:    int
    is_expired:    bool
    carpeta_id:    int | None = None
    carpeta:       SalidaCarpetaBasica | None = None
    puerto_id:     int | None = None
    puerto:        SalidaPuertoBasico | None = None
    marino:        str | None = None
    user_id:       int
    titulo_original:       str | None = None
    mensaje_original:      str | None = None
    destinatario_original: str | None = None
    observaciones:         str | None = None

    model_config = {"from_attributes": True}


class DatosCrearTransferencia(BaseModel):
    title:         str
    recipient:     str
    message:       str | None = None
    max_downloads: int | None = None
    carpeta_id:    int | None = None
    puerto_id:     int | None = None
    marino:        str | None = None

    @field_validator("title")
    @classmethod
    def validar_titulo(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El título es obligatorio.")
        if len(v) > TITULO_MAX:
            raise ValueError(f"El título no puede superar {TITULO_MAX} caracteres.")
        return v

    @field_validator("recipient")
    @classmethod
    def validar_destinatario(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El destinatario es obligatorio.")
        if not _EMAIL_RE.match(v):
            raise ValueError("El correo del destinatario no tiene un formato válido.")
        return v

    @field_validator("message")
    @classmethod
    def validar_mensaje(cls, v: str | None) -> str | None:
        if v is not None and len(v) > MENSAJE_MAX:
            raise ValueError(f"El mensaje no puede superar {MENSAJE_MAX} caracteres.")
        return v or None

    @field_validator("max_downloads")
    @classmethod
    def validar_max_descargas(cls, v: int | None) -> int | None:
        if v is not None and v < 1:
            raise ValueError("El límite de descargas debe ser al menos 1.")
        return v

    @field_validator("marino")
    @classmethod
    def validar_marino(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if len(v) > 255:
                raise ValueError("El nombre del marino no puede superar 255 caracteres.")
        return v or None


class DatosCrearBorrador(BaseModel):
    """Datos para crear un borrador (flujo Naviera). Destinatario opcional;
    el Sector Pacífico puede completarlo / corregirlo después."""
    title:       str
    message:     str | None = None
    recipient:   str | None = None

    @field_validator("title")
    @classmethod
    def validar_titulo(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El título es obligatorio.")
        if len(v) > TITULO_MAX:
            raise ValueError(f"El título no puede superar {TITULO_MAX} caracteres.")
        return v

    @field_validator("recipient")
    @classmethod
    def validar_destinatario(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not _EMAIL_RE.match(v):
            raise ValueError("El correo del destinatario no tiene un formato válido.")
        return v

    @field_validator("message")
    @classmethod
    def validar_mensaje(cls, v: str | None) -> str | None:
        if v is not None and len(v) > MENSAJE_MAX:
            raise ValueError(f"El mensaje no puede superar {MENSAJE_MAX} caracteres.")
        return v or None


class DatosProcesarTransferencia(BaseModel):
    """Patch parcial para Sector Pacífico mientras procesa el borrador."""
    title:         str | None = None
    message:       str | None = None
    recipient:     str | None = None
    max_downloads: int | None = None
    carpeta_id:    int | None = None
    puerto_id:     int | None = None
    marino:        str | None = None
    observaciones: str | None = None

    @field_validator("title")
    @classmethod
    def _v_title(cls, v):
        if v is None: return None
        v = v.strip()
        if not v: raise ValueError("El título no puede estar vacío.")
        if len(v) > TITULO_MAX: raise ValueError(f"Máximo {TITULO_MAX} caracteres.")
        return v

    @field_validator("recipient")
    @classmethod
    def _v_recipient(cls, v):
        if v is None: return None
        v = v.strip()
        if not v: return None
        if not _EMAIL_RE.match(v):
            raise ValueError("El correo del destinatario no tiene un formato válido.")
        return v

    @field_validator("message")
    @classmethod
    def _v_message(cls, v):
        if v is None: return None
        if len(v) > MENSAJE_MAX: raise ValueError(f"Máximo {MENSAJE_MAX} caracteres.")
        return v or None


class DatosReenviar(BaseModel):
    """Reenvía un borrador: cambia a ACTIVA y dispara correo. Permite anexar
    un nuevo mensaje. La expiración se renueva siempre a partir de este
    momento usando TRANSFER_EXPIRY_DAYS (no es configurable por el cliente)."""
    message: str | None = None

    @field_validator("message")
    @classmethod
    def _v_message(cls, v):
        if v is None: return None
        if len(v) > MENSAJE_MAX: raise ValueError(f"Máximo {MENSAJE_MAX} caracteres.")
        return v or None


class DatosDevolver(BaseModel):
    """Devuelve una transferencia a la Naviera con un motivo obligatorio."""
    motivo: str

    @field_validator("motivo")
    @classmethod
    def _v_motivo(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El motivo es obligatorio para devolver la transferencia.")
        if len(v) > MENSAJE_MAX:
            raise ValueError(f"El motivo no puede superar {MENSAJE_MAX} caracteres.")
        return v


class RespuestaTransferenciaPublica(BaseModel):
    id:            int
    token:         str
    title:         str | None
    message:       str | None
    expires_at:    datetime | None
    downloads:     int
    max_downloads: int | None
    is_expired:    bool
    files:         list[SalidaArchivoTransferencia] = []
    total_size:    int
    sender:        str

    model_config = {"from_attributes": True}
