import BarraProgreso, { type ColorBarra } from "./BarraProgreso";
import styles from "./RankingBarras.module.css";

export interface ItemRanking {
  id: number | string;
  nombre: string;
  valor: number;
}

interface Props {
  items:  ItemRanking[];
  color?: ColorBarra;
  sufijo?: string;
}

/** Lista ranking con barra de magnitud — un solo tono para todo el conjunto
 * (la comparación es entre ítems, no entre categorías distintas). */
export default function RankingBarras({ items, color = "gold", sufijo = "" }: Props) {
  const max = Math.max(...items.map(i => i.valor), 1);
  return (
    <div className={styles.lista}>
      {items.map(it => (
        <div key={it.id} className={styles.fila}>
          <span className={styles.nombre} title={it.nombre}>{it.nombre}</span>
          <BarraProgreso valor={it.valor} max={max} color={color} />
          <span className={styles.valor}>{it.valor}{sufijo}</span>
        </div>
      ))}
    </div>
  );
}
