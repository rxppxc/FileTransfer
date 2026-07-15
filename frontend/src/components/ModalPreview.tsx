/**
 * Modal de previsualización de un archivo de una transferencia.
 *
 * Imágenes y PDF se muestran inline (img / iframe) contra el endpoint público
 * `/transfers/preview/{token}/{fileId}`. Los tipos que el navegador no puede
 * renderizar (Word, Excel, etc.) muestran un fallback con botón para abrir/
 * descargar ese archivo individual — sin obligar a bajar el ZIP completo.
 */
import { useEffect } from "react";
import { apiTransferencias } from "../api/transfers";
import { infoTipo } from "../utils/tipoArchivo";
import { useAtraparFoco } from "../hooks/useAtraparFoco";
import { IconoX, IconoDescargar, IconoArchivo } from "./Iconos";
import styles from "./ModalPreview.module.css";

interface Props {
  token:    string;
  archivo:  { id: number; original_name: string; mime_type: string | null };
  onCerrar: () => void;
}

export function ModalPreview({ token, archivo, onCerrar }: Props) {
  const refModal = useAtraparFoco(true);
  const { categoria } = infoTipo(archivo.mime_type, archivo.original_name);
  const url = apiTransferencias.urlPreview(token, archivo.id);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onCerrar();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onCerrar]);

  return (
    <div className={styles.backdrop} onClick={onCerrar}>
      <div
        ref={refModal}
        className={styles.box}
        onClick={e => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={`Previsualización de ${archivo.original_name}`}
      >
        <div className={styles.header}>
          <span className={styles.titulo}>{archivo.original_name}</span>
          <button className={styles.cerrar} onClick={onCerrar} aria-label="Cerrar" data-focus-inicial>
            <IconoX tamano={16} />
          </button>
        </div>
        <div className={styles.body}>
          {categoria === "imagen" ? (
            <img src={url} alt={archivo.original_name} className={styles.img} />
          ) : categoria === "pdf" ? (
            <iframe src={url} title={archivo.original_name} className={styles.pdf} />
          ) : (
            <div className={styles.fallback}>
              <div className={styles.fallbackIcono}><IconoArchivo tamano={30} /></div>
              <div className={styles.fallbackTexto}>
                El archivo <span className={styles.fallbackNombre}>{archivo.original_name}</span> no
                se puede previsualizar en el navegador. Ábrelo o descárgalo para revisarlo.
              </div>
              <a className={styles.btnDescargar} href={url} target="_blank" rel="noopener noreferrer">
                <IconoDescargar tamano={16} />
                Abrir archivo
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
