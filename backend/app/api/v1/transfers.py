from urllib.parse import quote as url_quote
from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.infrastructure.database import obtener_sesion_bd
from app.domain.repositories.user_repository import RepositorioUsuario
from app.domain.repositories.transfer_repository import RepositorioTransferencia
from app.domain.repositories.audit_repository import RepositorioAuditoria
from app.domain.models.audit_log import AccionAuditoria
from app.domain.models.puerto import Puerto
from app.domain.services.transfer_service import ServicioTransferencia
from app.domain.schemas.transfer import (
    DatosCrearTransferencia, DatosCrearBorrador, DatosProcesarTransferencia, DatosReenviar,
    DatosDevolver, SalidaTransferencia, RespuestaTransferenciaPublica,
)
from app.domain.models.user import Usuario
from app.core.security import obtener_id_usuario_actual
from app.core.permisos import requerir_permiso, requerir_algun_permiso, usuario_tiene_permiso, es_admin_efectivo
from app.core.email import enviar_notificacion_transferencia, enviar_notificacion_devolucion
from app.core.http_utils import obtener_ip, obtener_agente
from app.core.rate_limit import limiter, limite_descarga
from app.core.config import obtener_configuracion

_configuracion = obtener_configuracion()

enrutador = APIRouter(prefix="/transfers", tags=["transferencias"])


def _obtener_servicio(sesion: AsyncSession = Depends(obtener_sesion_bd)) -> ServicioTransferencia:
    return ServicioTransferencia(RepositorioTransferencia(sesion))


async def _obtener_usuario_actual(
    user_id: int = Depends(obtener_id_usuario_actual),
    sesion:  AsyncSession = Depends(obtener_sesion_bd),
) -> Usuario:
    usuario = await RepositorioUsuario(sesion).buscar_por_id(user_id)
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario no encontrado.")
    return usuario


@enrutador.get("/puertos")
async def listar_puertos_publico(
    _: Usuario = Depends(_obtener_usuario_actual),
    sesion: AsyncSession = Depends(obtener_sesion_bd),
):
    """Lista todos los puertos — accesible por cualquier usuario autenticado."""
    resultado = await sesion.execute(select(Puerto).order_by(Puerto.nombre))
    puertos = resultado.scalars().all()
    return [{"id": p.id, "nombre": p.nombre} for p in puertos]


@enrutador.get("/", response_model=list[SalidaTransferencia])
async def listar_transferencias(
    usuario: Usuario = Depends(_obtener_usuario_actual),
    svc: ServicioTransferencia = Depends(_obtener_servicio),
):
    return await svc.listar_por_usuario(usuario.id)


@enrutador.post("/", response_model=SalidaTransferencia, status_code=201)
async def crear_transferencia(
    request:          Request,
    background_tasks: BackgroundTasks,
    files:         list[UploadFile] = File(...),
    title:         Optional[str]    = Form(None),
    message:       Optional[str]    = Form(None),
    recipient:     Optional[str]    = Form(None),
    max_downloads: Optional[int]    = Form(None),
    puerto_id:     Optional[int]    = Form(None),
    marino:        Optional[str]    = Form(None),
    naviera:       Optional[str]    = Form(None),
    usuario: Usuario = Depends(_obtener_usuario_actual),
    _perm:   int     = Depends(requerir_permiso("T-CREAR-COMPLETA")),
    svc: ServicioTransferencia = Depends(_obtener_servicio),
    sesion: AsyncSession = Depends(obtener_sesion_bd),
):
    datos = DatosCrearTransferencia(
        title=title, message=message, recipient=recipient,
        max_downloads=max_downloads,
        puerto_id=puerto_id, marino=marino, naviera=naviera,
    )
    resultado = await svc.crear(usuario.id, datos, files)

    await RepositorioAuditoria(sesion).registrar(
        AccionAuditoria.TRANSFERENCIA_CREADA,
        user_id=usuario.id, username=usuario.username,
        detalle={
            "token":        resultado.token,
            "titulo":       resultado.title,
            "destinatario": resultado.recipient,
            "marino":       resultado.marino,
            "naviera":      resultado.naviera,
            "archivos":     [f.original_name for f in resultado.files],
            "expira_en":    resultado.expires_at.isoformat() if resultado.expires_at else None,
        },
        ip=obtener_ip(request), agente=obtener_agente(request),
    )

    if resultado.recipient:
        fecha_exp = resultado.expires_at.strftime("%d/%m/%Y a las %H:%M") if resultado.expires_at else "—"
        background_tasks.add_task(
            enviar_notificacion_transferencia,
            recipient_email=resultado.recipient,
            sender_name=usuario.full_name,
            title=resultado.title,
            message=resultado.message,
            token=resultado.token,
            expires_at=fecha_exp,
            cantidad_archivos=len(resultado.files),
        )

    return resultado


# ── Flujo Naviera / Sector Pacífico ───────────────────────────────────────────

@enrutador.post("/borrador", response_model=SalidaTransferencia, status_code=201)
async def crear_borrador(
    request:          Request,
    background_tasks: BackgroundTasks,
    files:       list[UploadFile] = File(...),
    title:       str              = Form(...),
    message:     Optional[str]    = Form(None),
    recipient:   Optional[str]    = Form(None),
    usuario: Usuario = Depends(_obtener_usuario_actual),
    _perm:   int     = Depends(requerir_permiso("T-CREAR-BASICA")),
    svc:     ServicioTransferencia = Depends(_obtener_servicio),
    sesion:  AsyncSession = Depends(obtener_sesion_bd),
):
    datos = DatosCrearBorrador(title=title, message=message, recipient=recipient)
    resultado = await svc.crear_borrador(usuario.id, datos, files)

    await RepositorioAuditoria(sesion).registrar(
        AccionAuditoria.TRANSFERENCIA_CREADA,
        user_id=usuario.id, username=usuario.username,
        detalle={
            "token":     resultado.token,
            "titulo":    resultado.title,
            "estado":    "borrador",
            "archivos":  [f.original_name for f in resultado.files],
        },
        ip=obtener_ip(request), agente=obtener_agente(request),
    )

    if resultado.recipient:
        fecha_exp = resultado.expires_at.strftime("%d/%m/%Y a las %H:%M") if resultado.expires_at else "—"
        background_tasks.add_task(
            enviar_notificacion_transferencia,
            recipient_email=resultado.recipient,
            sender_name=usuario.full_name,
            title=resultado.title,
            message=resultado.message,
            token=resultado.token,
            expires_at=fecha_exp,
            cantidad_archivos=len(resultado.files),
        )

    return resultado


@enrutador.get("/todas-activas", response_model=list[SalidaTransferencia])
async def listar_todas_activas(
    _perm: int = Depends(requerir_algun_permiso("T-PROCESAR-PACIFICO")),
    svc: ServicioTransferencia = Depends(_obtener_servicio),
):
    """Todas las transferencias activas de todos los usuarios (Sector Pacífico y Admin)."""
    return await svc.listar_todas_activas()


@enrutador.get("/cola-pacifico", response_model=list[SalidaTransferencia])
async def cola_pacifico(
    _perm: int = Depends(requerir_permiso("T-PROCESAR-PACIFICO")),
    svc: ServicioTransferencia = Depends(_obtener_servicio),
):
    """Lista todas las transferencias en estado borrador (cola compartida)."""
    return await svc.listar_borradores()


@enrutador.get("/by-id/{transfer_id}", response_model=SalidaTransferencia)
async def obtener_transferencia(
    transfer_id: int,
    usuario: Usuario = Depends(_obtener_usuario_actual),
    _perm:   int     = Depends(requerir_algun_permiso("T-PROCESAR-PACIFICO", "T-CREAR-BASICA", "T-CREAR-COMPLETA")),
    svc:     ServicioTransferencia = Depends(_obtener_servicio),
    sesion:  AsyncSession = Depends(obtener_sesion_bd),
):
    resultado = await svc.obtener_por_id(transfer_id)
    # Sector Pacífico y Administrador ven cualquier transferencia (procesan la
    # cola global). El resto (Naviera) solo puede ver las suyas — evita el IDOR
    # de enumerar ids para leer transferencias de otras navieras. Devolvemos 404
    # (no 403) para no filtrar la existencia del id.
    puede_ver_todas = es_admin_efectivo(usuario) or await usuario_tiene_permiso(
        sesion, usuario.id, "T-PROCESAR-PACIFICO"
    )
    if not puede_ver_todas and resultado.user_id != usuario.id:
        raise HTTPException(status_code=404, detail="Transferencia no encontrada.")
    return resultado


@enrutador.patch("/by-id/{transfer_id}/procesar", response_model=SalidaTransferencia)
async def procesar_transferencia(
    transfer_id: int,
    datos: DatosProcesarTransferencia,
    request: Request,
    usuario: Usuario = Depends(_obtener_usuario_actual),
    _perm:   int     = Depends(requerir_permiso("T-PROCESAR-PACIFICO")),
    svc:     ServicioTransferencia = Depends(_obtener_servicio),
    sesion:  AsyncSession = Depends(obtener_sesion_bd),
):
    resultado = await svc.procesar(transfer_id, datos)
    await RepositorioAuditoria(sesion).registrar(
        AccionAuditoria.TRANSFERENCIA_CREADA,
        user_id=usuario.id, username=usuario.username,
        detalle={"token": resultado.token, "accion": "procesado", "campos": datos.model_dump(exclude_none=True)},
        ip=obtener_ip(request), agente=obtener_agente(request),
    )
    return resultado


@enrutador.post("/by-id/{transfer_id}/archivos", response_model=SalidaTransferencia)
async def agregar_archivos(
    transfer_id: int,
    files: list[UploadFile] = File(...),
    usuario: Usuario = Depends(_obtener_usuario_actual),
    _perm:   int     = Depends(requerir_permiso("T-PROCESAR-PACIFICO")),
    svc:     ServicioTransferencia = Depends(_obtener_servicio),
):
    return await svc.agregar_archivos(transfer_id, files, usuario.id)


@enrutador.delete("/by-id/{transfer_id}/archivos/{archivo_id}", response_model=SalidaTransferencia)
async def quitar_archivo(
    transfer_id: int,
    archivo_id:  int,
    _perm: int = Depends(requerir_permiso("T-PROCESAR-PACIFICO")),
    svc:   ServicioTransferencia = Depends(_obtener_servicio),
):
    return await svc.eliminar_archivo(transfer_id, archivo_id)


@enrutador.post("/by-id/{transfer_id}/reenviar", response_model=SalidaTransferencia)
async def reenviar_transferencia(
    transfer_id:      int,
    datos:            DatosReenviar,
    request:          Request,
    background_tasks: BackgroundTasks,
    usuario: Usuario = Depends(_obtener_usuario_actual),
    _perm:   int     = Depends(requerir_permiso("T-PROCESAR-PACIFICO")),
    svc:     ServicioTransferencia = Depends(_obtener_servicio),
    sesion:  AsyncSession = Depends(obtener_sesion_bd),
):
    resultado = await svc.reenviar(transfer_id, datos)

    # Email solo al reenviar — archivos NO se adjuntan
    if resultado.recipient:
        fecha_exp = resultado.expires_at.strftime("%d/%m/%Y a las %H:%M") if resultado.expires_at else "—"
        background_tasks.add_task(
            enviar_notificacion_transferencia,
            recipient_email=resultado.recipient,
            sender_name=usuario.full_name,
            title=resultado.title,
            message=resultado.message,
            token=resultado.token,
            expires_at=fecha_exp,
            cantidad_archivos=len(resultado.files),
        )

    await RepositorioAuditoria(sesion).registrar(
        AccionAuditoria.TRANSFERENCIA_CREADA,
        user_id=usuario.id, username=usuario.username,
        detalle={"token": resultado.token, "accion": "reenviada"},
        ip=obtener_ip(request), agente=obtener_agente(request),
    )
    return resultado


@enrutador.post("/by-id/{transfer_id}/devolver", response_model=SalidaTransferencia)
async def devolver_transferencia(
    transfer_id:      int,
    datos:            DatosDevolver,
    request:          Request,
    background_tasks: BackgroundTasks,
    usuario: Usuario = Depends(_obtener_usuario_actual),
    _perm:   int     = Depends(requerir_permiso("T-PROCESAR-PACIFICO")),
    svc:     ServicioTransferencia = Depends(_obtener_servicio),
    sesion:  AsyncSession = Depends(obtener_sesion_bd),
):
    """Sector Pacífico devuelve la transferencia a la Naviera con un motivo.
    Envía correo automáticamente a la Naviera dueña con el motivo y un enlace
    directo al panel de corrección."""
    resultado = await svc.devolver(transfer_id, datos)

    # Recuperamos la Naviera dueña para su email
    naviera = await RepositorioUsuario(sesion).buscar_por_id(resultado.user_id)
    if naviera and naviera.email:
        enlace = f"{_configuracion.app_base_url}/transfers/{resultado.id}/corregir"
        background_tasks.add_task(
            enviar_notificacion_devolucion,
            email_destinatario   = naviera.email,
            nombre_destinatario  = naviera.full_name,
            titulo_transferencia = resultado.title,
            motivo               = datos.motivo,
            quien_devolvio       = "Sector Pacífico",
            url_correccion       = enlace,
        )

    await RepositorioAuditoria(sesion).registrar(
        AccionAuditoria.TRANSFERENCIA_CREADA,
        user_id=usuario.id, username=usuario.username,
        detalle={"token": resultado.token, "accion": "devuelta", "motivo": datos.motivo},
        ip=obtener_ip(request), agente=obtener_agente(request),
    )
    return resultado


# ── Flujo Muelle/Operador ────────────────────────────────────────────────────

@enrutador.get("/cola-muelle", response_model=list[SalidaTransferencia])
async def cola_muelle(
    usuario: Usuario = Depends(_obtener_usuario_actual),
    _perm:   int     = Depends(requerir_permiso("T-PROCESAR-MUELLE")),
    svc:     ServicioTransferencia = Depends(_obtener_servicio),
):
    """Transferencias activas asignadas a los puertos del operador."""
    puerto_ids = [p.id for p in usuario.puertos_asignados]
    return await svc.listar_cola_muelle(puerto_ids)


@enrutador.post("/by-id/{transfer_id}/procesada", response_model=SalidaTransferencia)
async def marcar_transferencia_procesada(
    transfer_id: int,
    request:     Request,
    usuario: Usuario = Depends(_obtener_usuario_actual),
    _perm:   int     = Depends(requerir_permiso("T-PROCESAR-MUELLE")),
    svc:     ServicioTransferencia = Depends(_obtener_servicio),
    sesion:  AsyncSession = Depends(obtener_sesion_bd),
):
    """Muelle/Operador marca la transferencia como procesada — fin del flujo."""
    puerto_ids = [p.id for p in usuario.puertos_asignados]
    resultado  = await svc.marcar_procesada(transfer_id, usuario.id, puerto_ids)
    await RepositorioAuditoria(sesion).registrar(
        AccionAuditoria.TRANSFERENCIA_CREADA,
        user_id=usuario.id, username=usuario.username,
        detalle={"token": resultado.token, "accion": "procesada_por_muelle"},
        ip=obtener_ip(request), agente=obtener_agente(request),
    )
    return resultado


@enrutador.post("/by-id/{transfer_id}/devolver-muelle", response_model=SalidaTransferencia)
async def devolver_desde_muelle(
    transfer_id:      int,
    datos:            DatosDevolver,
    request:          Request,
    background_tasks: BackgroundTasks,
    usuario: Usuario = Depends(_obtener_usuario_actual),
    _perm:   int     = Depends(requerir_permiso("T-PROCESAR-MUELLE")),
    svc:     ServicioTransferencia = Depends(_obtener_servicio),
    sesion:  AsyncSession = Depends(obtener_sesion_bd),
):
    """Muelle/Operador devuelve la transferencia al Sector Pacífico con un
    motivo (ej. puerto incorrecto). Se envía correo al buzón `MAIL_FROM` como
    alerta al equipo, ya que un rol SP puede tener varios integrantes."""
    puerto_ids = [p.id for p in usuario.puertos_asignados]
    resultado  = await svc.devolver_desde_muelle(transfer_id, datos, usuario.id, puerto_ids)

    if _configuracion.MAIL_FROM:
        enlace = f"{_configuracion.app_base_url}/dashboard"
        background_tasks.add_task(
            enviar_notificacion_devolucion,
            email_destinatario   = _configuracion.MAIL_FROM,
            nombre_destinatario  = "Sector Pacífico",
            titulo_transferencia = resultado.title,
            motivo               = datos.motivo,
            quien_devolvio       = f"Muelle/Operador — {usuario.full_name}",
            url_correccion       = enlace,
        )

    await RepositorioAuditoria(sesion).registrar(
        AccionAuditoria.TRANSFERENCIA_CREADA,
        user_id=usuario.id, username=usuario.username,
        detalle={"token": resultado.token, "accion": "devuelta_por_muelle", "motivo": datos.motivo},
        ip=obtener_ip(request), agente=obtener_agente(request),
    )
    return resultado


@enrutador.post("/by-id/{transfer_id}/resubmit", response_model=SalidaTransferencia)
async def resubmit_transferencia(
    transfer_id: int,
    request:     Request,
    usuario: Usuario = Depends(_obtener_usuario_actual),
    _perm:   int     = Depends(requerir_permiso("T-CREAR-BASICA")),
    svc:     ServicioTransferencia = Depends(_obtener_servicio),
    sesion:  AsyncSession = Depends(obtener_sesion_bd),
):
    """Naviera re-envía una transferencia devuelta — vuelve a estado borrador."""
    resultado = await svc.resubmit(transfer_id, usuario.id)
    await RepositorioAuditoria(sesion).registrar(
        AccionAuditoria.TRANSFERENCIA_CREADA,
        user_id=usuario.id, username=usuario.username,
        detalle={"token": resultado.token, "accion": "resubmit"},
        ip=obtener_ip(request), agente=obtener_agente(request),
    )
    return resultado


@enrutador.post("/by-id/{transfer_id}/corregir/archivos", response_model=SalidaTransferencia)
async def corregir_agregar_archivos(
    transfer_id: int,
    files: list[UploadFile] = File(...),
    usuario: Usuario = Depends(_obtener_usuario_actual),
    _perm:   int     = Depends(requerir_permiso("T-CREAR-BASICA")),
    svc:     ServicioTransferencia = Depends(_obtener_servicio),
):
    """Naviera agrega archivos a una transferencia devuelta."""
    return await svc.corregir_agregar_archivos(transfer_id, files, usuario.id)


@enrutador.delete("/by-id/{transfer_id}/corregir/archivos/{archivo_id}", response_model=SalidaTransferencia)
async def corregir_eliminar_archivo(
    transfer_id: int,
    archivo_id:  int,
    usuario: Usuario = Depends(_obtener_usuario_actual),
    _perm:   int     = Depends(requerir_permiso("T-CREAR-BASICA")),
    svc:     ServicioTransferencia = Depends(_obtener_servicio),
):
    """Naviera elimina un archivo de una transferencia devuelta."""
    return await svc.corregir_eliminar_archivo(transfer_id, archivo_id, usuario.id)


@enrutador.get("/preview/{token}/{file_id}")
@limiter.limit(limite_descarga)
async def previsualizar_archivo(
    request: Request,
    token:   str,
    file_id: int,
    svc:     ServicioTransferencia = Depends(_obtener_servicio),
):
    ruta, mime, nombre = await svc.obtener_ruta_preview(token, file_id)
    return FileResponse(
        path=ruta,
        media_type=mime or "application/octet-stream",
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{url_quote(nombre)}",
            "Cache-Control": "private, max-age=300",
        },
    )


@enrutador.get("/public/{token}", response_model=RespuestaTransferenciaPublica)
@limiter.limit(limite_descarga)
async def obtener_transferencia_publica(
    request: Request,
    token: str,
    svc: ServicioTransferencia = Depends(_obtener_servicio),
):
    return await svc.obtener_publica(token)


@enrutador.get("/download/{token}")
@limiter.limit(limite_descarga)
async def descargar_transferencia(
    token:   str,
    request: Request,
    svc:     ServicioTransferencia = Depends(_obtener_servicio),
    sesion:  AsyncSession = Depends(obtener_sesion_bd),
):
    ruta, nombre_archivo = await svc.obtener_ruta_descarga(token)

    transferencia = await RepositorioTransferencia(sesion).buscar_por_token(token)
    if transferencia:
        await RepositorioAuditoria(sesion).registrar(
            AccionAuditoria.DESCARGA_REALIZADA,
            user_id=transferencia.user_id,
            username=transferencia.usuario.username if transferencia.usuario else None,
            detalle={"token": token, "archivo": nombre_archivo, "titulo": transferencia.title},
            ip=obtener_ip(request), agente=obtener_agente(request),
        )

    return FileResponse(path=ruta, filename=nombre_archivo, media_type="application/octet-stream")


@enrutador.delete("/{token}", status_code=204)
async def eliminar_transferencia(
    token:   str,
    request: Request,
    usuario: Usuario = Depends(_obtener_usuario_actual),
    svc:     ServicioTransferencia = Depends(_obtener_servicio),
    sesion:  AsyncSession = Depends(obtener_sesion_bd),
):
    transferencia = await RepositorioTransferencia(sesion).buscar_por_token(token)
    await svc.eliminar(token, usuario.id)

    await RepositorioAuditoria(sesion).registrar(
        AccionAuditoria.TRANSFERENCIA_ELIMINADA,
        user_id=usuario.id, username=usuario.username,
        detalle={
            "token":  token,
            "titulo": transferencia.title if transferencia else None,
        },
        ip=obtener_ip(request), agente=obtener_agente(request),
    )
