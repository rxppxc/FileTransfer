import { useTema } from "../context/ContextoTema";
import { IconoSol, IconoLuna } from "./Iconos";
import styles from "./AlternadorTema.module.css";

export function AlternadorTema() {
  const { tema, alternar } = useTema();
  const oscuro = tema === "dark";

  return (
    <button
      className={styles.btn}
      onClick={alternar}
      aria-label={oscuro ? "Cambiar a modo claro" : "Cambiar a modo oscuro"}
    >
      <span className={styles.iconWrap}>
        {oscuro ? <IconoSol tamano={16} /> : <IconoLuna tamano={15} />}
      </span>
      <span className={styles.label}>{oscuro ? "Claro" : "Oscuro"}</span>
    </button>
  );
}
