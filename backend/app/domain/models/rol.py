from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.infrastructure.database import Base
from datetime import datetime


class Permiso(Base):
    __tablename__ = "permisos"

    id:          Mapped[int]      = mapped_column(Integer, primary_key=True, index=True)
    codigo:      Mapped[str]      = mapped_column(String(50), nullable=False, unique=True, index=True)
    nombre:      Mapped[str]      = mapped_column(String(150), nullable=False)
    descripcion: Mapped[str|None] = mapped_column(Text)
    created_at:  Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    roles: Mapped[list["RolPermiso"]] = relationship(
        "RolPermiso", back_populates="permiso", cascade="all, delete-orphan"
    )


class Rol(Base):
    __tablename__ = "roles"

    id:          Mapped[int]      = mapped_column(Integer, primary_key=True, index=True)
    nombre:      Mapped[str]      = mapped_column(String(100), nullable=False, unique=True, index=True)
    descripcion: Mapped[str|None] = mapped_column(Text)
    es_sistema:  Mapped[bool]     = mapped_column(default=False, server_default="false")
    created_at:  Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    permisos: Mapped[list["RolPermiso"]] = relationship(
        "RolPermiso", back_populates="rol", cascade="all, delete-orphan"
    )


class RolPermiso(Base):
    __tablename__ = "roles_permisos"
    __table_args__ = (UniqueConstraint("rol_id", "permiso_id", name="uq_roles_permisos_rol_permiso"),)

    id:         Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    rol_id:     Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    permiso_id: Mapped[int] = mapped_column(ForeignKey("permisos.id", ondelete="CASCADE"), nullable=False, index=True)

    rol:     Mapped["Rol"]     = relationship("Rol",     back_populates="permisos")
    permiso: Mapped["Permiso"] = relationship("Permiso", back_populates="roles")
