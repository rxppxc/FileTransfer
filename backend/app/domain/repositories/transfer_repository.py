from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from app.domain.models.transfer import Transferencia, ArchivoTransferencia, EstadoTransferencia
from app.domain.models.carpeta import Carpeta
from app.domain.models.puerto import Puerto


class RepositorioTransferencia:
    def __init__(self, sesion: AsyncSession):
        self.sesion = sesion

    async def buscar_por_token(self, token: str) -> Transferencia | None:
        resultado = await self.sesion.execute(
            select(Transferencia)
            .options(
                selectinload(Transferencia.archivos),
                selectinload(Transferencia.usuario),
                selectinload(Transferencia.carpeta),
                selectinload(Transferencia.puerto),
            )
            .where(Transferencia.token == token)
        )
        return resultado.scalar_one_or_none()

    async def buscar_por_id(self, transfer_id: int) -> Transferencia | None:
        resultado = await self.sesion.execute(
            select(Transferencia)
            .options(
                selectinload(Transferencia.archivos),
                selectinload(Transferencia.usuario),
                selectinload(Transferencia.carpeta),
                selectinload(Transferencia.puerto),
            )
            .where(Transferencia.id == transfer_id)
        )
        return resultado.scalar_one_or_none()

    async def listar_por_estado(self, estado: EstadoTransferencia, limit: int = 100) -> list[Transferencia]:
        resultado = await self.sesion.execute(
            select(Transferencia)
            .options(
                selectinload(Transferencia.archivos),
                selectinload(Transferencia.usuario),
                selectinload(Transferencia.carpeta),
                selectinload(Transferencia.puerto),
            )
            .where(Transferencia.status == estado)
            .order_by(Transferencia.created_at.desc())
            .limit(limit)
        )
        return list(resultado.scalars().all())

    async def listar_por_estados(self, estados: list[EstadoTransferencia], limit: int = 200) -> list[Transferencia]:
        """Igual que listar_por_estado pero acepta varios estados (OR).
        Usado para la cola de SP que junta 'draft' + 'review'."""
        valores = [e.value if hasattr(e, "value") else e for e in estados]
        resultado = await self.sesion.execute(
            select(Transferencia)
            .options(
                selectinload(Transferencia.archivos),
                selectinload(Transferencia.usuario),
                selectinload(Transferencia.carpeta),
                selectinload(Transferencia.puerto),
            )
            .where(Transferencia.status.in_(valores))
            .order_by(Transferencia.created_at.desc())
            .limit(limit)
        )
        return list(resultado.scalars().all())

    async def listar_activas_por_puertos(self, puerto_ids: list[int], limit: int = 500) -> list[Transferencia]:
        """Transferencias activas asignadas a alguno de los puertos indicados.
        Usada por la cola del Muelle/Operador."""
        if not puerto_ids:
            return []
        resultado = await self.sesion.execute(
            select(Transferencia)
            .options(
                selectinload(Transferencia.archivos),
                selectinload(Transferencia.usuario),
                selectinload(Transferencia.carpeta),
                selectinload(Transferencia.puerto),
            )
            .where(
                Transferencia.status == EstadoTransferencia.ACTIVA,
                Transferencia.puerto_id.in_(puerto_ids),
            )
            .order_by(Transferencia.created_at.desc())
            .limit(limit)
        )
        return list(resultado.scalars().all())

    async def guardar(self, transferencia: Transferencia) -> None:
        await self.sesion.flush()
        await self.sesion.refresh(transferencia, ["archivos", "usuario", "carpeta", "puerto"])

    async def refrescar(self, transferencia: Transferencia) -> None:
        await self.sesion.refresh(transferencia, ["archivos", "carpeta", "puerto"])

    async def eliminar_archivo(self, archivo: ArchivoTransferencia) -> None:
        await self.sesion.delete(archivo)
        await self.sesion.flush()

    async def listar_por_usuario(self, user_id: int, limit: int = 50, offset: int = 0) -> list[Transferencia]:
        resultado = await self.sesion.execute(
            select(Transferencia)
            .options(
                selectinload(Transferencia.archivos),
                selectinload(Transferencia.carpeta),
                selectinload(Transferencia.puerto),
            )
            .where(Transferencia.user_id == user_id)
            .order_by(Transferencia.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(resultado.scalars().all())

    async def listar_activas(self, limit: int = 500) -> list[Transferencia]:
        """Devuelve TODAS las transferencias activas de todos los usuarios."""
        resultado = await self.sesion.execute(
            select(Transferencia)
            .options(
                selectinload(Transferencia.archivos),
                selectinload(Transferencia.usuario),
                selectinload(Transferencia.carpeta),
                selectinload(Transferencia.puerto),
            )
            .where(Transferencia.status == EstadoTransferencia.ACTIVA)
            .order_by(Transferencia.created_at.desc())
            .limit(limit)
        )
        return list(resultado.scalars().all())

    async def crear(self, transferencia: Transferencia) -> Transferencia:
        self.sesion.add(transferencia)
        await self.sesion.flush()
        await self.sesion.refresh(transferencia, ["archivos", "usuario", "carpeta", "puerto"])
        return transferencia

    async def incrementar_descargas(self, token: str) -> None:
        # UPDATE con expresión SQL (downloads = downloads + 1) es atómico en
        # PostgreSQL: ejecuta en una sola declaración a nivel de fila, sin
        # ventana lectura-modificación-escritura — descartar incrementos
        # concurrentes es imposible aquí.
        await self.sesion.execute(
            update(Transferencia)
            .where(Transferencia.token == token)
            .values(downloads=Transferencia.downloads + 1)
        )

    async def eliminar(self, transferencia: Transferencia) -> None:
        await self.sesion.delete(transferencia)
