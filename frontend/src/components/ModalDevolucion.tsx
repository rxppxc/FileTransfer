/**
 * Modal para devolver una transferencia con un MOTIVO obligatorio.
 *
 * Se usa tanto cuando Sector Pacífico devuelve a la Naviera como cuando el
 * Muelle/Operador devuelve al Sector Pacífico. La UI es la misma; sólo cambian
 * el título y el placeholder según el destinatario.
 *
 * Uso:
 *   const [abierto, setAbierto] = useState(false);
 *   ...
 *   <ModalDevolucion
 *     abierto={abierto}
 *     titulo="Devolver a la Naviera"
 *     placeholder="Explica qué debe corregir..."
 *     onCancelar={() => setAbierto(false)}
 *     onConfirmar={async (motivo) => { await api.devolver(id, motivo); setAbierto(false); }}
 *   />
 */
import { useEffect, useState } from "react";
import { useAtraparFoco } from "../hooks/useAtraparFoco";
import styles from "./ModalConfirmacion.module.css";

interface Props {
  abierto:      boolean;
  titulo:       string;
  descripcion?: string;
  placeholder?: string;
  onCancelar:   () => void;
  onConfirmar:  (motivo: string) => void | Promise<void>;
  textoOk?:     string;
}

export function ModalDevolucion({
  abierto,
  titulo,
  descripcion,
  placeholder = "Describe el motivo de la devolución...",
  onCancelar,
  onConfirmar,
  textoOk = "Devolver",
}: Props) {
  const [motivo, setMotivo] = useState("");
  const [enviando, setEnviando] = useState(false);

  // Limpiar al cerrar
  useEffect(() => {
    if (!abierto) {
      setMotivo("");
      setEnviando(false);
    }
  }, [abierto]);

  useEffect(() => {
    if (!abierto) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onCancelar();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [abierto, onCancelar]);

  const refModal = useAtraparFoco(abierto);

  if (!abierto) return null;

  async function confirmar() {
    const m = motivo.trim();
    if (!m || enviando) return;
    setEnviando(true);
    try {
      await onConfirmar(m);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className={styles.overlay} onClick={onCancelar}>
      <div
        ref={refModal}
        className={styles.modal}
        onClick={e => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="devolucion-titulo"
      >
        <h3 id="devolucion-titulo" className={styles.titulo}>{titulo}</h3>
        {descripcion && <p className={styles.mensaje}>{descripcion}</p>}
        <textarea
          className={styles.mensaje}
          style={{
            width: "100%",
            minHeight: 110,
            padding: "10px 12px",
            border: "1.5px solid var(--input-border)",
            borderRadius: 8,
            background: "var(--input-bg)",
            color: "var(--text, #f4f5f8)",
            fontFamily: "inherit",
            fontSize: ".92rem",
            resize: "vertical",
            marginBottom: 16,
          }}
          placeholder={placeholder}
          value={motivo}
          onChange={e => setMotivo(e.target.value)}
          data-focus-inicial
          maxLength={1000}
        />
        <div className={styles.acciones}>
          <button className={styles.btnCancelar} onClick={onCancelar} disabled={enviando}>
            Cancelar
          </button>
          <button
            className={styles.btnPeligro}
            onClick={confirmar}
            disabled={motivo.trim().length === 0 || enviando}
          >
            {enviando ? "Enviando…" : textoOk}
          </button>
        </div>
      </div>
    </div>
  );
}
