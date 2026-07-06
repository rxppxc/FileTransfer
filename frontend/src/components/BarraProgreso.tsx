import styles from "./BarraProgreso.module.css";

export type ColorBarra = "gold" | "green" | "blue" | "gray" | "purple" | "orange" | "teal";

interface Props {
  valor: number;
  max: number;
  color?: ColorBarra;
}

/** Barra de magnitud de un solo tono. `max` define el 100% — pasar el mayor
 * valor del conjunto que se está comparando, no un límite fijo. */
export default function BarraProgreso({ valor, max, color = "gold" }: Props) {
  const pct = max > 0 ? Math.min(100, (valor / max) * 100) : 0;
  return (
    <div className={styles.pista}>
      <div className={`${styles.relleno} ${styles[color]}`} style={{ width: `${pct}%` }} />
    </div>
  );
}
