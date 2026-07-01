import { Link, useNavigate } from "react-router-dom";
import { IconoAtras } from "./Iconos";
import styles from "./BotonVolver.module.css";

export function BotonVolver({ to, onClick }: { to?: string; onClick?: () => void }) {
  const navegar = useNavigate();
  if (to)      return <Link to={to} className={styles.btn}><IconoAtras />Volver</Link>;
  if (onClick) return <button className={styles.btn} onClick={onClick}><IconoAtras />Volver</button>;
  return        <button className={styles.btn} onClick={() => navegar(-1)}><IconoAtras />Volver</button>;
}
