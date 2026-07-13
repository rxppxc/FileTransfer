import { useEffect, useRef } from "react";

const SELECTOR_FOCUSABLE =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

/**
 * Atrapa el foco (Tab/Shift+Tab) dentro de un modal mientras está abierto, y
 * restaura el foco al elemento que lo abrió al cerrarse. Devuelve el ref que
 * hay que poner en el contenedor del modal (no en el overlay).
 *
 * Al abrir, mueve el foco al elemento marcado con `data-focus-inicial` dentro
 * del contenedor, o si no hay ninguno, al primer elemento enfocable. Hace esto
 * en vez de usar la prop `autoFocus` de React porque `autoFocus` se aplica en
 * el mismo commit que este efecto — si ambos compitieran, el orden no está
 * garantizado y `previoRef` podría terminar capturando el propio elemento del
 * modal en lugar de lo que tenía el foco antes de abrirlo.
 */
export function useAtraparFoco(activo: boolean) {
  const ref = useRef<HTMLDivElement>(null);
  const previoRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!activo) return;
    previoRef.current = document.activeElement as HTMLElement | null;

    const contenedor = ref.current;
    if (contenedor) {
      const preferido = contenedor.querySelector<HTMLElement>("[data-focus-inicial]");
      const objetivo   = preferido ?? contenedor.querySelector<HTMLElement>(SELECTOR_FOCUSABLE);
      objetivo?.focus();
    }

    function onKeyDown(e: KeyboardEvent) {
      if (e.key !== "Tab" || !ref.current) return;
      const focusables = Array.from(ref.current.querySelectorAll<HTMLElement>(SELECTOR_FOCUSABLE))
        .filter(el => el.offsetParent !== null);
      if (focusables.length === 0) return;
      const primero = focusables[0];
      const ultimo  = focusables[focusables.length - 1];
      if (e.shiftKey && document.activeElement === primero) {
        e.preventDefault();
        ultimo.focus();
      } else if (!e.shiftKey && document.activeElement === ultimo) {
        e.preventDefault();
        primero.focus();
      }
    }

    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      previoRef.current?.focus?.();
    };
  }, [activo]);

  return ref;
}
