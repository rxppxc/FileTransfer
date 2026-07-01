"""Utilidades comunes para inspeccionar peticiones HTTP entrantes."""
from fastapi import Request


def obtener_ip(request: Request) -> str | None:
    """IP del cliente. Prioriza X-Forwarded-For si la app va detrás de proxy."""
    fwd = request.headers.get("X-Forwarded-For")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


def obtener_agente(request: Request) -> str | None:
    """User-Agent del cliente, truncado a 500 caracteres."""
    ua = request.headers.get("User-Agent", "")
    return ua[:500] if ua else None
