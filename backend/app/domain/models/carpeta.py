from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.infrastructure.database import Base
from datetime import datetime
import typing

if typing.TYPE_CHECKING:
    from app.domain.models.transfer import Transferencia
    from app.domain.models.puerto import Puerto


class Carpeta(Base):
    __tablename__ = "carpetas"

    id:          Mapped[int]      = mapped_column(Integer, primary_key=True, index=True)
    nombre:      Mapped[str]      = mapped_column(String(255), nullable=False, unique=True)
    descripcion: Mapped[str|None] = mapped_column(Text)
    created_at:  Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    puerto_id:   Mapped[int|None] = mapped_column(ForeignKey("puertos.id", ondelete="SET NULL"), nullable=True, index=True)

    transferencias: Mapped[list["Transferencia"]] = relationship("Transferencia", back_populates="carpeta")
    puerto:         Mapped["Puerto | None"]        = relationship("Puerto", back_populates="carpetas")
