import styles from "./ModalExpiracionSesion.module.css";

interface Props {
  segundos: number;
  onContinuar: () => void;
  onCerrarSesion: () => void;
}

export function ModalExpiracionSesion({ segundos, onContinuar, onCerrarSesion }: Props) {
  const min = Math.floor(segundos / 60);
  const seg = segundos % 60;
  const cuenta = min > 0
    ? `${min}:${seg.toString().padStart(2, "0")}`
    : `${segundos}s`;

  return (
    <div className={styles.overlay}>
      <div className={styles.modal}>
        <div className={styles.icono}>⏱</div>
        <h2 className={styles.titulo}>Sesión por expirar</h2>
        <p className={styles.texto}>
          Su sesión cerrará automáticamente por inactividad en:
        </p>
        <div className={styles.cuenta}>{cuenta}</div>
        <div className={styles.botones}>
          <button className={styles.btnContinuar} onClick={onContinuar}>
            Continuar sesión
          </button>
          <button className={styles.btnSalir} onClick={onCerrarSesion}>
            Cerrar sesión
          </button>
        </div>
      </div>
    </div>
  );
}
