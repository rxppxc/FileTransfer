from sqlalchemy import String, Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.infrastructure.database import Base
from datetime import datetime
import typing

if typing.TYPE_CHECKING:
    from app.domain.models.carpeta import Carpeta
    from app.domain.models.user import Usuario


class Puerto(Base):
    __tablename__ = "puertos"

    id:          Mapped[int]      = mapped_column(Integer, primary_key=True, index=True)
    nombre:      Mapped[str]      = mapped_column(String(255), nullable=False, unique=True)
    descripcion: Mapped[str|None] = mapped_column(Text)
    created_at:  Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    carpetas: Mapped[list["Carpeta"]] = relationship("Carpeta", back_populates="puerto")

    # Operadores del muelle que tienen este puerto asignado
    operadores: Mapped[list["Usuario"]] = relationship(
        "Usuario",
        secondary="usuarios_puertos",
        back_populates="puertos_asignados",
    )
