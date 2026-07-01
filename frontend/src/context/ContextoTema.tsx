/**
 * Tema visual (claro/oscuro) compartido por toda la aplicación.
 *
 * El valor se persiste en localStorage para conservar la preferencia entre
 * recargas; al primer arranque se respeta la preferencia del sistema
 * operativo (`prefers-color-scheme`).
 *
 * Uso:
 *   const { tema, alternar } = useTema();
 */
import { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";

type Tema = "dark" | "light";
interface CtxTema { tema: Tema; alternar: () => void; }

const ContextoTema = createContext<CtxTema>({ tema: "dark", alternar: () => {} });

function temaInicial(): Tema {
  const guardado = localStorage.getItem("tema") as Tema | null;
  if (guardado === "dark" || guardado === "light") return guardado;
  return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
}

export function ProveedorTema({ children }: { children: ReactNode }) {
  const [tema, setTema] = useState<Tema>(() => {
    const t = temaInicial();
    document.documentElement.setAttribute("data-theme", t);
    return t;
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", tema);
    localStorage.setItem("tema", tema);
  }, [tema]);

  const alternar = () => setTema(t => (t === "dark" ? "light" : "dark"));

  return (
    <ContextoTema.Provider value={{ tema, alternar }}>
      {children}
    </ContextoTema.Provider>
  );
}

export const useTema = () => useContext(ContextoTema);
