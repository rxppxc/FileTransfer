from pydantic import BaseModel
from app.domain.models.user import TipoUsuario, EstadoUsuario
from app.domain.schemas.rol import RolMini
from app.domain.schemas.puerto import SalidaPuertoMini


class SalidaUsuario(BaseModel):
    id:        int
    username:  str
    name:      str | None
    last_name: str | None
    email:     str | None
    user_type: TipoUsuario
    status:    EstadoUsuario
    rol_id:    int | None = None
    rol_personalizado: RolMini | None = None
    full_name: str
    puertos_asignados: list[SalidaPuertoMini] = []

    model_config = {"from_attributes": True}


class RespuestaToken(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user:         SalidaUsuario


class SolicitudLogin(BaseModel):
    username: str
    password: str
