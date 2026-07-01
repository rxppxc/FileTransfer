from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.infrastructure.database import Base
from datetime import datetime
import enum


class AccionAuditoria(str, enum.Enum):
    LOGIN_EXITOSO           = "LOGIN_EXITOSO"
    LOGIN_FALLIDO           = "LOGIN_FALLIDO"
    CERRAR_SESION           = "CERRAR_SESION"
    SESION_EXPIRADA         = "SESION_EXPIRADA"
    TRANSFERENCIA_CREADA    = "TRANSFERENCIA_CREADA"
    TRANSFERENCIA_ELIMINADA = "TRANSFERENCIA_ELIMINADA"
    DESCARGA_REALIZADA      = "DESCARGA_REALIZADA"


class RegistroAuditoria(Base):
    __tablename__ = "audit_logs"

    id:        Mapped[int]             = mapped_column(Integer, primary_key=True, index=True)
    user_id:   Mapped[int | None]      = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    username:  Mapped[str | None]      = mapped_column(String(100))
    accion:    Mapped[AccionAuditoria] = mapped_column(SAEnum(AccionAuditoria, name="accionauditoria"))
    detalle:   Mapped[dict | None]     = mapped_column(JSON, nullable=True)
    ip:        Mapped[str | None]      = mapped_column(String(45))
    agente:    Mapped[str | None]      = mapped_column(String(500))
    creado_en: Mapped[datetime]        = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
