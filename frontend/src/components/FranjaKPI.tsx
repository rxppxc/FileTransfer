import type { ReactNode } from "react";
import styles from "./FranjaKPI.module.css";

export type ColorKPI = "gold" | "green" | "blue" | "gray" | "purple" | "orange" | "teal";

export interface ItemKPI {
  icono: ReactNode;
  valor: string | number;
  etiqueta: string;
  color: ColorKPI;
}

/** Franja compacta de indicadores clave. Cada ítem es un chip autocontenido
 * (fondo propio) en vez de usar divisores compartidos, para que el wrap en
 * pantallas angostas o con muchos ítems no deje bordes sueltos. */
export default function FranjaKPI({ items }: { items: ItemKPI[] }) {
  return (
    <div className={styles.franja}>
      {items.map((it, i) => (
        <div key={i} className={styles.item}>
          <span className={`${styles.icono} ${styles[it.color]}`}>{it.icono}</span>
          <span className={styles.valor}>{it.valor}</span>
          <span className={styles.etiqueta}>{it.etiqueta}</span>
        </div>
      ))}
    </div>
  );
}
