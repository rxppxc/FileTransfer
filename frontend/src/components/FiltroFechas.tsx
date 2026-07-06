import { useState } from "react";
import { IconoReloj } from "./Iconos";
import styles from "./FiltroFechas.module.css";

/** Rango de fechas seleccionado. Fechas en formato ISO `YYYY-MM-DD` (o null = sin límite). */
export interface RangoFechas {
  desde: string | null;
  hasta: string | null;
}

type Preset = "todas" | "hoy" | "7d" | "30d" | "rango";

const PRESETS: { id: Preset; etiqueta: string }[] = [
  { id: "todas", etiqueta: "Todas" },
  { id: "hoy",   etiqueta: "Hoy" },
  { id: "7d",    etiqueta: "7 días" },
  { id: "30d",   etiqueta: "30 días" },
  { id: "rango", etiqueta: "Rango…" },
];

/** Fecha local (no UTC) en formato YYYY-MM-DD — evita el desfase de zona horaria de toISOString. */
function fechaLocalISO(d: Date): string {
  const y  = d.getFullYear();
  const m  = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${dd}`;
}

function haceDias(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return fechaLocalISO(d);
}

interface Props {
  valor: RangoFechas;
  onCambio: (r: RangoFechas) => void;
}

export default function FiltroFechas({ valor, onCambio }: Props) {
  const [preset, setPreset] = useState<Preset>("todas");
  const [desde,  setDesde]  = useState("");
  const [hasta,  setHasta]  = useState("");

  function aplicarPreset(p: Preset) {
    setPreset(p);
    const hoy = fechaLocalISO(new Date());
    if (p === "todas")      onCambio({ desde: null, hasta: null });
    else if (p === "hoy")   onCambio({ desde: hoy,          hasta: hoy });
    else if (p === "7d")    onCambio({ desde: haceDias(6),  hasta: hoy });
    else if (p === "30d")   onCambio({ desde: haceDias(29), hasta: hoy });
    else if (p === "rango") onCambio({ desde: desde || null, hasta: hasta || null });
  }

  function cambiarRango(nuevoDesde: string, nuevaHasta: string) {
    setDesde(nuevoDesde);
    setHasta(nuevaHasta);
    onCambio({ desde: nuevoDesde || null, hasta: nuevaHasta || null });
  }

  const hayFiltro = valor.desde !== null || valor.hasta !== null;

  return (
    <div className={styles.barra}>
      <span className={styles.icono}><IconoReloj tamano={15} /></span>
      <span className={styles.rotulo}>Fecha</span>
      <div className={styles.chips}>
        {PRESETS.map((p) => (
          <button
            key={p.id}
            type="button"
            className={`${styles.chip} ${preset === p.id ? styles.chipActivo : ""}`}
            onClick={() => aplicarPreset(p.id)}
          >
            {p.etiqueta}
          </button>
        ))}
      </div>

      {preset === "rango" && (
        <div className={styles.rango}>
          <input
            type="date"
            className={styles.dateInput}
            value={desde}
            max={hasta || undefined}
            onChange={(e) => cambiarRango(e.target.value, hasta)}
            aria-label="Fecha desde"
          />
          <span className={styles.sep}>—</span>
          <input
            type="date"
            className={styles.dateInput}
            value={hasta}
            min={desde || undefined}
            onChange={(e) => cambiarRango(desde, e.target.value)}
            aria-label="Fecha hasta"
          />
        </div>
      )}

      {hayFiltro && (
        <button type="button" className={styles.limpiar} onClick={() => aplicarPreset("todas")}>
          Limpiar
        </button>
      )}
    </div>
  );
}
