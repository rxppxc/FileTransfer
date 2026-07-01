from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import obtener_configuracion

configuracion = obtener_configuracion()

motor_bd = create_async_engine(
    configuracion.DATABASE_URL,
    # echo SQL solo en desarrollo. En producción evita exponer queries con
    # datos sensibles en los logs y mejora rendimiento.
    echo=not configuracion.es_produccion and configuracion.APP_ENV == "development",
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,  # recicla conexiones cada hora (previene conn cerradas por idle)
)

SesionLocal = async_sessionmaker(
    motor_bd,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def obtener_sesion_bd() -> AsyncSession:
    async with SesionLocal() as sesion:
        try:
            yield sesion
            await sesion.commit()
        except Exception:
            await sesion.rollback()
            raise
