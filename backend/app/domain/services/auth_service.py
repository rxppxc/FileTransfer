import asyncio
import logging
from fastapi import HTTPException, status
from ldap3.core.exceptions import LDAPException
from app.core.ldap import servicio_ldap
from app.core.security import crear_token_acceso
from app.domain.models.user import EstadoUsuario
from app.domain.repositories.user_repository import RepositorioUsuario
from app.domain.schemas.user import RespuestaToken, SalidaUsuario

logger = logging.getLogger(__name__)


class ServicioAutenticacion:
    def __init__(self, repo_usuario: RepositorioUsuario):
        self.repo_usuario = repo_usuario

    async def login(self, nombre_usuario: str, contrasena: str) -> RespuestaToken:
        # 1. Buscar en Active Directory
        try:
            ldap_usuario = await asyncio.to_thread(
                servicio_ldap.buscar_usuario, nombre_usuario
            )
        except LDAPException as e:
            logger.error(f"Error de conexión con Active Directory: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No se pudo conectar al servidor de Active Directory. Verifica tu conexión de red.",
            )

        if not ldap_usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado en Active Directory.",
            )

        # 2. Verificar contraseña contra AD
        try:
            autenticado = await asyncio.to_thread(
                servicio_ldap.autenticar, ldap_usuario["dn"], contrasena
            )
        except Exception as e:
            logger.error(f"Error inesperado al verificar credenciales LDAP: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Error al verificar credenciales. Inténtalo de nuevo.",
            )
        if not autenticado:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Contraseña incorrecta. Verifica tus credenciales de red.",
            )

        # 3. Verificar que el usuario está registrado en el sistema local
        usuario = await self.repo_usuario.actualizar_desde_ldap(ldap_usuario)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes acceso al sistema. Contacta al administrador de TI para que registre tu usuario.",
            )
        if usuario.status != EstadoUsuario.ACTIVO:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tu cuenta está deshabilitada. Contacta al administrador de TI.",
            )

        token = crear_token_acceso(subject=usuario.id, extra={"username": usuario.username})
        return RespuestaToken(
            access_token=token,
            user=SalidaUsuario.model_validate(usuario),
        )
