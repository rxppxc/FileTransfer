import { useState, useEffect, useCallback } from "react";
import { apiAutenticacion } from "../api/auth";
import { useAutenticacion } from "./useAutenticacion";

/** Permisos del usuario actual (códigos como "T-CREAR-BASICA").
 *  Se cargan del backend al montarse y se cachean en localStorage.
 *  La fuente de verdad es rol_personalizado: admin solo si nombre === "Administrador". */
export function usePermisos() {
  const { estaAutenticado, usuario } = useAutenticacion();
  const esAdmin = usuario?.rol_personalizado?.nombre === "Administrador";

  const [codigos, setCodigos] = useState<string[]>(() => {
    try { return JSON.parse(localStorage.getItem("permisos") ?? "[]"); }
    catch { return []; }
  });
  const [cargando, setCargando] = useState(false);

  const recargar = useCallback(async (signal?: AbortSignal) => {
    if (!estaAutenticado) {
      setCodigos([]);
      localStorage.removeItem("permisos");
      return;
    }
    setCargando(true);
    try {
      const lista = await apiAutenticacion.misPermisos();
      if (signal?.aborted) return;
      setCodigos(lista);
      localStorage.setItem("permisos", JSON.stringify(lista));
    } catch {
      // mantener cache
    } finally {
      if (!signal?.aborted) setCargando(false);
    }
  }, [estaAutenticado]);

  useEffect(() => {
    const ac = new AbortController();
    recargar(ac.signal);
    return () => ac.abort();
  }, [recargar]);

  const tiene = useCallback(
    (codigo: string) => esAdmin || codigos.includes(codigo),
    [codigos, esAdmin],
  );

  const tieneAlguno = useCallback(
    (...lista: string[]) => esAdmin || lista.some(c => codigos.includes(c)),
    [codigos, esAdmin],
  );

  return { codigos, cargando, tiene, tieneAlguno, recargar, esAdmin };
}
