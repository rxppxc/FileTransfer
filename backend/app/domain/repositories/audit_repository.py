from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models.audit_log import RegistroAuditoria, AccionAuditoria


class RepositorioAuditoria:
    def __init__(self, sesion: AsyncSession):
        self.sesion = sesion

    async def registrar(
        self,
        accion: AccionAuditoria,
        *,
        user_id:  int | None  = None,
        username: str | None  = None,
        detalle:  dict | None = None,
        ip:       str | None  = None,
        agente:   str | None  = None,
    ) -> None:
        self.sesion.add(RegistroAuditoria(
            accion=accion, user_id=user_id, username=username,
            detalle=detalle, ip=ip, agente=agente,
        ))
