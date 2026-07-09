from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, BigInteger, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.infrastructure.database import Base
from datetime import datetime, timezone
import enum
import typing

if typing.TYPE_CHECKING:
    from app.domain.models.puerto import Puerto


class EstadoTransferencia(str, enum.Enum):
    BORRADOR    = "draft"       # creado por Naviera, pendiente de revisión de SP
    ACTIVA      = "active"      # SP la procesó y asignó puerto → visible por Muelle
    EXPIRADA    = "expired"     # venció por fecha o descargas
    ELIMINADA   = "deleted"     # borrada lógicamente
    DEVUELTO    = "returned"    # SP la devolvió a la Naviera con motivo
    REVISION_SP = "review"      # Muelle la devolvió a SP con motivo (queda en cola de SP)
    PROCESADA   = "processed"   # Muelle marcó como procesada — estado final del flujo


class Transferencia(Base):
    __tablename__ = "transfers"
    __table_args__ = (
        Index("ix_transfers_expires_at", "expires_at"),
        Index("ix_transfers_status",     "status"),
    )

    id:            Mapped[int]                    = mapped_column(Integer, primary_key=True, index=True)
    user_id:       Mapped[int]                    = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token:         Mapped[str]                    = mapped_column(String(64), unique=True, nullable=False, index=True)
    title:         Mapped[str | None]             = mapped_column(String(255))
    message:       Mapped[str | None]             = mapped_column(Text)
    recipient:     Mapped[str | None]             = mapped_column(String(255))
    expires_at:    Mapped[datetime | None]        = mapped_column(DateTime(timezone=True))
    downloads:     Mapped[int]                    = mapped_column(Integer, default=0)
    max_downloads: Mapped[int | None]             = mapped_column(Integer)
    status:        Mapped[str]                    = mapped_column(String(20), default="active", server_default="active", index=True)
    created_at:    Mapped[datetime]               = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:    Mapped[datetime]               = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    puerto_id:  Mapped[int | None] = mapped_column(ForeignKey("puertos.id",  ondelete="SET NULL"), nullable=True, index=True)
    marino:     Mapped[str | None] = mapped_column(String(255))
    naviera:    Mapped[str | None] = mapped_column(String(255))

    # Snapshot original (inmutable) capturado al crear el borrador
    titulo_original:      Mapped[str | None] = mapped_column(String(255))
    mensaje_original:     Mapped[str | None] = mapped_column(Text)
    destinatario_original: Mapped[str | None] = mapped_column(String(255))

    # Observaciones internas del Sector Pacífico (no se envían al destinatario)
    observaciones: Mapped[str | None] = mapped_column(Text)

    usuario:  Mapped["Usuario"]                     = relationship(back_populates="transferencias")
    archivos: Mapped[list["ArchivoTransferencia"]]  = relationship(back_populates="transferencia", cascade="all, delete-orphan")
    puerto:   Mapped["Puerto | None"]               = relationship("Puerto")

    @property
    def files(self) -> list["ArchivoTransferencia"]:
        return self.archivos

    @property
    def is_expired(self) -> bool:
        # Estados que están vivos en algún paso del flujo — no cuentan como expirados
        estados_vivos = {
            EstadoTransferencia.BORRADOR,
            EstadoTransferencia.DEVUELTO,
            EstadoTransferencia.REVISION_SP,
            EstadoTransferencia.PROCESADA,
        }
        if self.status in estados_vivos:
            return False
        if self.status != EstadoTransferencia.ACTIVA:
            return True
        if self.expires_at and self.expires_at < datetime.now(timezone.utc):
            return True
        if self.max_downloads and self.downloads >= self.max_downloads:
            return True
        return False

    @property
    def total_size(self) -> int:
        return sum(archivo.size for archivo in self.archivos)


class ArchivoTransferencia(Base):
    __tablename__ = "transfer_files"

    id:            Mapped[int]        = mapped_column(Integer, primary_key=True, index=True)
    transfer_id:   Mapped[int]        = mapped_column(ForeignKey("transfers.id", ondelete="CASCADE"), index=True)
    original_name: Mapped[str]        = mapped_column(String(500), nullable=False)
    stored_name:   Mapped[str]        = mapped_column(String(500), nullable=False)
    path:          Mapped[str]        = mapped_column(String(1000), nullable=False)
    mime_type:     Mapped[str | None] = mapped_column(String(255))
    size:          Mapped[int]        = mapped_column(BigInteger, default=0)
    created_at:    Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())
    subido_por_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    es_original:   Mapped[bool]       = mapped_column(default=True, server_default="true")

    transferencia: Mapped["Transferencia"] = relationship(back_populates="archivos")
