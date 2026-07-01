"""Rate limiter compartido para endpoints públicos.

Usamos slowapi (basado en limits) con almacenamiento en memoria. Para
despliegues multi-proceso o multi-host, configurar `storage_uri` a Redis.

Ejemplo en endpoint:
    @router.get("/download/{token}")
    @limiter.limit(limite_descarga)
    async def descargar(token: str, request: Request, ...):
        ...
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import obtener_configuracion

_config = obtener_configuracion()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",
)


def limite_descarga() -> str:
    """Devuelve la cadena de límite (p. ej. "30/minute") según configuración.
    Si `RATE_LIMIT_DOWNLOADS_PER_MINUTE` es 0, retorna un límite muy alto
    (efectivamente desactivado)."""
    n = _config.RATE_LIMIT_DOWNLOADS_PER_MINUTE
    if n <= 0:
        return "100000/minute"
    return f"{n}/minute"
