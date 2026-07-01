import { useState, useCallback } from "react";
import { apiAutenticacion } from "../api/auth";
import type { Usuario } from "../types";

export function useAutenticacion() {
  const [usuario, setUsuario] = useState<Usuario | null>(() => {
    try { return JSON.parse(localStorage.getItem("user") ?? "null"); }
    catch { return null; }
  });

  const iniciarSesion = useCallback(async (nombreUsuario: string, contrasena: string) => {
    const datos = await apiAutenticacion.iniciarSesion(nombreUsuario, contrasena);
    localStorage.setItem("access_token", datos.access_token);
    localStorage.setItem("user", JSON.stringify(datos.user));
    setUsuario(datos.user);
    return datos.user;
  }, []);

  const cerrarSesion = useCallback(async (reportar = true, expirada = false) => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    setUsuario(null);
    if (reportar) {
      if (expirada) await apiAutenticacion.notificarExpiracion();
      else await apiAutenticacion.cerrarSesion();
    }
  }, []);

  const extenderSesion = useCallback(async () => {
    const datos = await apiAutenticacion.refrescarSesion();
    localStorage.setItem("access_token", datos.access_token);
    localStorage.setItem("user", JSON.stringify(datos.user));
    setUsuario(datos.user);
  }, []);

  return { usuario, iniciarSesion, cerrarSesion, extenderSesion, estaAutenticado: !!usuario };
}
