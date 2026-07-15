import logging
from ldap3 import Server, Connection, ALL, AUTO_BIND_NO_TLS, SUBTREE, SIMPLE
from ldap3.core.exceptions import LDAPBindError, LDAPException
from ldap3.utils.conv import escape_filter_chars
from app.core.config import obtener_configuracion

logger        = logging.getLogger(__name__)
configuracion = obtener_configuracion()


class ServicioLDAP:
    def __init__(self):
        self.servidor = Server(
            configuracion.LDAP_HOST,
            port=configuracion.LDAP_PORT,
            get_info=ALL,
            connect_timeout=configuracion.LDAP_TIMEOUT,
        )

    def _conectar_cuenta_servicio(self) -> Connection:
        conexion = Connection(
            self.servidor,
            user=configuracion.LDAP_BIND_USER,
            password=configuracion.LDAP_BIND_PASSWORD,
            auto_bind=AUTO_BIND_NO_TLS,
            receive_timeout=configuracion.LDAP_TIMEOUT,
        )
        if not conexion.bound:
            raise LDAPBindError("No se pudo conectar con la cuenta de servicio LDAP.")
        return conexion

    def buscar_usuario(self, nombre_usuario: str) -> dict | None:
        try:
            base = configuracion.LDAP_ALLOWED_OU or configuracion.LDAP_BASE_DN
            conexion = self._conectar_cuenta_servicio()
            # Escapa todos los caracteres reservados de filtros LDAP (RFC 4515)
            usuario_seguro = escape_filter_chars(nombre_usuario)
            conexion.search(
                search_base   = base,
                search_filter = f"(&(objectClass=user)(sAMAccountName={usuario_seguro}))",
                search_scope  = SUBTREE,
                attributes    = ["cn", "givenName", "sn", "mail", "sAMAccountName",
                                 "distinguishedName", "objectGUID", "department"],
            )
            if not conexion.entries:
                return None

            entrada = conexion.entries[0]
            return {
                "dn":        str(entrada.entry_dn),
                "username":  str(entrada.sAMAccountName),
                "name":      str(entrada.givenName) if entrada.givenName else "",
                "last_name": str(entrada.sn)        if entrada.sn        else "",
                "email":     str(entrada.mail)      if entrada.mail      else "",
                "guid":      str(entrada.objectGUID) if entrada.objectGUID else "",
            }
        except LDAPException as e:
            logger.error(f"Error al buscar usuario en LDAP: {e}")
            raise

    def autenticar(self, dn: str, contrasena: str) -> bool:
        # Defensa explícita contra el "unauthenticated bind" de LDAP: un bind
        # con usuario y contraseña vacía puede resolverse como bind anónimo
        # exitoso en algunos servidores, lo que sería un bypass de login.
        # ldap3 ya lanza LDAPPasswordIsMandatoryError, pero no dependemos de eso.
        if not contrasena or not contrasena.strip():
            logger.warning("[LDAP] Intento de autenticación con contraseña vacía — rechazado.")
            return False
        try:
            conexion = Connection(
                self.servidor,
                user=dn,
                password=contrasena,
                auto_bind=AUTO_BIND_NO_TLS,
                receive_timeout=configuracion.LDAP_TIMEOUT,
            )
            # No logueamos el DN completo (revela estructura del AD)
            logger.info("[LDAP] Autenticación exitosa")
            try:
                conexion.unbind()
            except Exception:
                pass
            return True
        except LDAPBindError as e:
            msg = str(e)
            # No incluir el DN en el log — revela la estructura del AD (regla #4).
            logger.warning("[LDAP] Autenticación fallida (bind rechazado).")
            if "data 773" in msg or "data 532" in msg:
                logger.warning("[LDAP] La cuenta requiere cambio de contraseña o está expirada.")
            elif "data 533" in msg:
                logger.warning("[LDAP] La cuenta está deshabilitada en Active Directory.")
            elif "data 775" in msg:
                logger.warning("[LDAP] La cuenta está bloqueada en Active Directory.")
            return False
        except LDAPException as e:
            logger.error(f"[LDAP] Error LDAP durante la autenticación: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"[LDAP] Error inesperado durante la autenticación: {e}", exc_info=True)
            return False


    def buscar_usuarios_ad(self, termino: str) -> list[dict]:
        """Búsqueda parcial en AD por usuario, nombre o email (máx. 20 resultados)."""
        try:
            base = configuracion.LDAP_ALLOWED_OU or configuracion.LDAP_BASE_DN
            conexion = self._conectar_cuenta_servicio()
            # Escape RFC 4515 para evitar LDAP injection (admin)(&(|...) etc.
            t = escape_filter_chars(termino)
            if not t:
                return []
            filtro = (
                f"(&(objectClass=user)(objectCategory=person)"
                f"(!(userAccountControl:1.2.840.113556.1.4.803:=2))"
                f"(|(sAMAccountName=*{t}*)(cn=*{t}*)(mail=*{t}*)))"
            )
            conexion.search(
                search_base  = base,
                search_filter= filtro,
                search_scope = SUBTREE,
                attributes   = ["cn", "givenName", "sn", "mail", "sAMAccountName",
                                 "distinguishedName", "objectGUID", "department"],
                size_limit   = 20,
            )
            resultados = []
            for entrada in conexion.entries:
                sam = str(entrada.sAMAccountName) if entrada.sAMAccountName else ""
                if not sam:
                    continue
                resultados.append({
                    "dn":         str(entrada.entry_dn),
                    "username":   sam,
                    "name":       str(entrada.givenName)  if entrada.givenName  else "",
                    "last_name":  str(entrada.sn)         if entrada.sn         else "",
                    "email":      str(entrada.mail)       if entrada.mail       else "",
                    "guid":       str(entrada.objectGUID) if entrada.objectGUID else "",
                    "department": str(entrada.department) if entrada.department else "",
                })
            conexion.unbind()
            return resultados
        except LDAPException as e:
            logger.error(f"Error al buscar usuarios en AD: {e}")
            raise


servicio_ldap = ServicioLDAP()
