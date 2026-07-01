from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.domain.models.user import Usuario, EstadoUsuario


class RepositorioUsuario:
    def __init__(self, sesion: AsyncSession):
        self.sesion = sesion

    async def buscar_por_id(self, user_id: int) -> Usuario | None:
        resultado = await self.sesion.execute(select(Usuario).where(Usuario.id == user_id))
        return resultado.scalar_one_or_none()

    async def buscar_por_nombre_usuario(self, nombre_usuario: str) -> Usuario | None:
        resultado = await self.sesion.execute(select(Usuario).where(Usuario.username == nombre_usuario))
        return resultado.scalar_one_or_none()

    async def listar_todos(self) -> list[Usuario]:
        resultado = await self.sesion.execute(
            select(Usuario).order_by(Usuario.name, Usuario.last_name, Usuario.username)
        )
        return list(resultado.scalars().all())

    async def crear_desde_ldap(self, datos_ldap: dict) -> Usuario:
        usuario = Usuario(
            username  = datos_ldap["username"],
            name      = datos_ldap.get("name")      or None,
            last_name = datos_ldap.get("last_name") or None,
            email     = datos_ldap.get("email")     or None,
            guid      = datos_ldap.get("guid")      or None,
        )
        self.sesion.add(usuario)
        await self.sesion.flush()
        await self.sesion.refresh(usuario)
        return usuario

    async def actualizar_desde_ldap(self, datos_ldap: dict) -> Usuario | None:
        """Actualiza info LDAP de un usuario existente. Retorna None si no está en el sistema."""
        usuario = await self.buscar_por_nombre_usuario(datos_ldap["username"])
        if not usuario:
            return None
        usuario.name      = datos_ldap.get("name")      or usuario.name
        usuario.last_name = datos_ldap.get("last_name") or usuario.last_name
        usuario.email     = datos_ldap.get("email")     or usuario.email
        usuario.guid      = datos_ldap.get("guid")      or usuario.guid
        await self.sesion.flush()
        await self.sesion.refresh(usuario)
        return usuario
