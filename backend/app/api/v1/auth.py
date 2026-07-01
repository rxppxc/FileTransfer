from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.infrastructure.database import obtener_sesion_bd
from app.domain.repositories.user_repository import RepositorioUsuario
from app.domain.repositories.audit_repository import RepositorioAuditoria
from app.domain.models.audit_log import AccionAuditoria
from app.domain.models.user import Usuario
from app.domain.models.rol import Permiso, RolPermiso
from app.domain.services.auth_service import ServicioAutenticacion
from app.domain.schemas.user import SolicitudLogin, RespuestaToken, SalidaUsuario
from app.core.security import obtener_id_usuario_actual, crear_token_acceso
from app.core.http_utils import obtener_ip, obtener_agente
from app.core.rate_limit import limiter

enrutador = APIRouter(prefix="/auth", tags=["autenticacion"])


@enrutador.post("/login", response_model=RespuestaToken)
@limiter.limit("10/minute")
async def iniciar_sesion(
    cuerpo:  SolicitudLogin,
    request: Request,
    sesion:  AsyncSession = Depends(obtener_sesion_bd),
):
    svc   = ServicioAutenticacion(RepositorioUsuario(sesion))
    audit = RepositorioAuditoria(sesion)
    try:
        resultado = await svc.login(cuerpo.username, cuerpo.password)
        await audit.registrar(
            AccionAuditoria.LOGIN_EXITOSO,
            user_id=resultado.user.id, username=resultado.user.username,
            ip=obtener_ip(request), agente=obtener_agente(request),
        )
        return resultado
    except HTTPException as exc:
        await audit.registrar(
            AccionAuditoria.LOGIN_FALLIDO,
            username=cuerpo.username,
            detalle={"motivo": exc.detail},
            ip=obtener_ip(request), agente=obtener_agente(request),
        )
        raise


@enrutador.post("/logout", status_code=204)
async def cerrar_sesion(
    request: Request,
    user_id: int = Depends(obtener_id_usuario_actual),
    sesion:  AsyncSession = Depends(obtener_sesion_bd),
):
    usuario = await RepositorioUsuario(sesion).buscar_por_id(user_id)
    await RepositorioAuditoria(sesion).registrar(
        AccionAuditoria.CERRAR_SESION,
        user_id=user_id,
        username=usuario.username if usuario else None,
        ip=obtener_ip(request), agente=obtener_agente(request),
    )


@enrutador.post("/session-expired", status_code=204)
async def sesion_expirada(
    request: Request,
    user_id: int = Depends(obtener_id_usuario_actual),
    sesion:  AsyncSession = Depends(obtener_sesion_bd),
):
    usuario = await RepositorioUsuario(sesion).buscar_por_id(user_id)
    await RepositorioAuditoria(sesion).registrar(
        AccionAuditoria.SESION_EXPIRADA,
        user_id=user_id,
        username=usuario.username if usuario else None,
        ip=obtener_ip(request), agente=obtener_agente(request),
    )


@enrutador.post("/refresh", response_model=RespuestaToken)
async def refrescar_sesion(
    user_id: int = Depends(obtener_id_usuario_actual),
    sesion:  AsyncSession = Depends(obtener_sesion_bd),
):
    usuario = await RepositorioUsuario(sesion).buscar_por_id(user_id)
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario no encontrado.")
    token = crear_token_acceso(subject=usuario.id, extra={"username": usuario.username})
    return RespuestaToken(access_token=token, user=SalidaUsuario.model_validate(usuario))


@enrutador.get("/me", response_model=SalidaUsuario)
async def perfil_actual(
    user_id: int = Depends(obtener_id_usuario_actual),
    sesion:  AsyncSession = Depends(obtener_sesion_bd),
):
    usuario = await RepositorioUsuario(sesion).buscar_por_id(user_id)
    return SalidaUsuario.model_validate(usuario)


@enrutador.get("/me/permisos", response_model=list[str])
async def permisos_actuales(
    user_id: int = Depends(obtener_id_usuario_actual),
    sesion:  AsyncSession = Depends(obtener_sesion_bd),
):
    usuario = (await sesion.execute(select(Usuario).where(Usuario.id == user_id))).scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    if usuario.rol_id is None:
        return []
    resultado = await sesion.execute(
        select(Permiso.codigo)
        .join(RolPermiso, RolPermiso.permiso_id == Permiso.id)
        .where(RolPermiso.rol_id == usuario.rol_id)
        .order_by(Permiso.codigo)
    )
    return [row[0] for row in resultado.all()]
