"""Capa de seguridad: emisión y verificación de tokens JWT.

El verificador `obtener_id_usuario_actual` hace una validación de BD en cada
request para que los cambios de estado del usuario (desactivado, rol revocado,
borrado) tengan efecto inmediato y no esperen al vencimiento del token.

Si esto se vuelve un problema de rendimiento se puede pasar a una caché corta
(Redis, 30-60s) o a una lista de revocación, pero por defecto preferimos
seguridad sobre micro-optimización.
"""
from datetime import datetime, timedelta, timezone
from typing import Any
import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import obtener_configuracion
from app.infrastructure.database import obtener_sesion_bd
from app.domain.models.user import Usuario, EstadoUsuario

configuracion  = obtener_configuracion()
esquema_bearer = HTTPBearer(auto_error=True)


# Solo para usuarios locales de prueba (user_type=LOCAL) — ver auth_service.py.
# bcrypt directo (no passlib): passlib 1.7.4 no es compatible con bcrypt>=4.1
# (falla su autodetección interna de un bug ya parcheado hace años).
def hashear_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def crear_token_acceso(subject: str | Any, extra: dict | None = None) -> str:
    expiracion = datetime.now(timezone.utc) + timedelta(minutes=configuracion.ACCESS_TOKEN_EXPIRE_MINUTES)
    carga      = {"sub": str(subject), "exp": expiracion}
    if extra:
        carga.update(extra)
    return jwt.encode(carga, configuracion.SECRET_KEY, algorithm=configuracion.ALGORITHM)


def decodificar_token(token: str) -> dict:
    try:
        return jwt.decode(token, configuracion.SECRET_KEY, algorithms=[configuracion.ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def obtener_id_usuario_actual(
    credenciales: HTTPAuthorizationCredentials = Depends(esquema_bearer),
    sesion:       AsyncSession                 = Depends(obtener_sesion_bd),
) -> int:
    """Devuelve el id del usuario autenticado, verificando que la cuenta siga
    activa en cada request. Cualquier cambio de estado (desactivado, borrado)
    invalida el token de inmediato sin esperar al vencimiento."""
    carga   = decodificar_token(credenciales.credentials)
    user_id = carga.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido.")
    try:
        uid = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido.")

    estado = (await sesion.execute(
        select(Usuario.status).where(Usuario.id == uid)
    )).scalar_one_or_none()
    if estado is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="La cuenta ya no existe.")
    # EstadoUsuario hereda de str, así que el miembro enum y su .value ("active")
    # comparan igual; una sola comparación cubre ambos casos.
    if estado != EstadoUsuario.ACTIVO.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="La cuenta está desactivada.")
    return uid
