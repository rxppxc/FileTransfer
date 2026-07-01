import { useState, useEffect, useCallback } from "react";
import { apiAdmin, type StatsAdmin } from "../../api/admin";
import { useNotificacion } from "../../components/Notificaciones";
import { formatBytes } from "../../utils/format";
import { MenuCabecera } from "../../components/MenuCabecera";
import { BotonVolver } from "../../components/BotonVolver";
import {
  IconoUsuario, IconoGrafico, IconoActividad, IconoDescargar,
  IconoDisco, IconoCarpeta, IconoAncla, IconoMas, IconoBasura,
  IconoReloj, IconoTrofeo,
} from "../../components/Iconos";
import styles from "./PaginaEstadisticas.module.css";

function EntityPanel({
  title, icon, items, addLabel,
  formFields, onAdd, onDelete, addLoading, deleteId, confirmId, setConfirmId, formError,
}: {
  title: string;
  icon: React.ReactNode;
  items: { id: number; nombre: string; extra?: string }[];
  addLabel: string;
  formFields: React.ReactNode;
  onAdd: (e: React.FormEvent) => void;
  onDelete: (id: number) => void;
  addLoading: boolean;
  deleteId: number | null;
  confirmId: number | null;
  setConfirmId: (id: number | null) => void;
  formError: string | null;
}) {
  const [mostrar, setMostrar] = useState(false);
  return (
    <section className={styles.panel}>
      <div className={styles.panelHeader}>
        {icon}
        {title}
        <span className={styles.count}>{items.length}</span>
        <button className={styles.btnAddCarpeta} onClick={() => { setMostrar(v => !v); }}>
          <IconoMas /> {addLabel}
        </button>
      </div>
      <div className={styles.panelBody}>
        {mostrar && (
          <form onSubmit={onAdd} className={styles.carpetaForm}>
            {formFields}
            {formError && <p className={styles.errText}>{formError}</p>}
            <div className={styles.formBtns}>
              <button type="submit" className={styles.btnGuardar} disabled={addLoading}>
                {addLoading ? <span className={styles.spinner} /> : <IconoMas />}
                {addLoading ? "Guardando…" : "Guardar"}
              </button>
              <button type="button" className={styles.btnCancelar} onClick={() => setMostrar(false)}>
                Cancelar
              </button>
            </div>
          </form>
        )}
        {items.length === 0 ? (
          <p className={styles.empty}>No hay {title.toLowerCase()} creados aún.</p>
        ) : (
          <div className={styles.carpetaList}>
            {items.map(item => (
              <div key={item.id} className={styles.carpetaRow}>
                <div className={styles.carpetaIcon}>{icon}</div>
                <div className={styles.carpetaInfo}>
                  <div className={styles.carpetaNombre}>{item.nombre}</div>
                  {item.extra && <div className={styles.carpetaTotal}>{item.extra}</div>}
                </div>
                {confirmId === item.id ? (
                  <div className={styles.confirmRow}>
                    <span className={styles.confirmText}>¿Eliminar?</span>
                    <button
                      className={`${styles.actionBtn} ${styles.btnElimConfirm}`}
                      onClick={() => onDelete(item.id)}
                      disabled={deleteId === item.id}
                    >
                      {deleteId === item.id ? <span className={styles.spinnerSm} /> : null}
                      Sí
                    </button>
                    <button className={`${styles.actionBtn} ${styles.btnNo}`} onClick={() => setConfirmId(null)}>
                      No
                    </button>
                  </div>
                ) : (
                  <button
                    className={styles.btnElimCarpeta}
                    onClick={() => setConfirmId(item.id)}
                    title="Eliminar"
                  >
                    <IconoBasura />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

export default function PaginaEstadisticas() {
  const { mostrar: mostrarToast } = useNotificacion();

  const [stats,    setStats]    = useState<StatsAdmin | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error,    setError]    = useState<string | null>(null);

  // Puerto form
  const [nuevoPuertoNombre, setNuevoPuertoNombre] = useState("");
  const [nuevoPuertoDesc,   setNuevoPuertoDesc]   = useState("");
  const [creandoPuerto,     setCreandoPuerto]     = useState(false);
  const [elimPuertoId,      setElimPuertoId]      = useState<number | null>(null);
  const [confirmarPuerto,   setConfirmarPuerto]   = useState<number | null>(null);
  const [errPuerto,         setErrPuerto]         = useState<string | null>(null);

  // Carpeta form
  const [nuevaNombre,    setNuevaNombre]    = useState("");
  const [nuevaDesc,      setNuevaDesc]      = useState("");
  const [nuevaPuertoId,  setNuevaPuertoId]  = useState<number | "">("");
  const [creando,        setCreando]        = useState(false);
  const [eliminandoId,   setEliminandoId]   = useState<number | null>(null);
  const [confirmarId,    setConfirmarId]    = useState<number | null>(null);
  const [errCarpeta,     setErrCarpeta]     = useState<string | null>(null);

  const cargar = useCallback(async () => {
    try {
      const { data } = await apiAdmin.obtenerStats();
      setStats(data);
    } catch {
      setError("No se pudieron cargar las estadísticas.");
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => { cargar(); }, [cargar]);

  async function alCrearPuerto(e: React.FormEvent) {
    e.preventDefault();
    const nombre = nuevoPuertoNombre.trim();
    if (!nombre) return;
    setCreandoPuerto(true);
    setErrPuerto(null);
    try {
      await apiAdmin.crearPuerto(nombre, nuevoPuertoDesc.trim() || undefined);
      setNuevoPuertoNombre("");
      setNuevoPuertoDesc("");
      await cargar();
    } catch (err: any) {
      setErrPuerto(err?.response?.data?.detail ?? "Error al crear el puerto.");
    } finally {
      setCreandoPuerto(false);
    }
  }

  async function alEliminarPuerto(id: number) {
    setElimPuertoId(id);
    try {
      await apiAdmin.eliminarPuerto(id);
      await cargar();
    } catch (err: any) {
      mostrarToast(err?.response?.data?.detail ?? "Error al eliminar el puerto.", "error");
    } finally {
      setElimPuertoId(null);
      setConfirmarPuerto(null);
    }
  }

  async function alCrearCarpeta(e: React.FormEvent) {
    e.preventDefault();
    const nombre = nuevaNombre.trim();
    if (!nombre) return;
    setCreando(true);
    setErrCarpeta(null);
    try {
      await apiAdmin.crearCarpeta(nombre, nuevaDesc.trim() || undefined, nuevaPuertoId !== "" ? nuevaPuertoId : undefined);
      setNuevaNombre("");
      setNuevaDesc("");
      setNuevaPuertoId("");
      await cargar();
    } catch (err: any) {
      setErrCarpeta(err?.response?.data?.detail ?? "Error al crear la naviera.");
    } finally {
      setCreando(false);
    }
  }

  async function alEliminarCarpeta(id: number) {
    setEliminandoId(id);
    try {
      await apiAdmin.eliminarCarpeta(id);
      await cargar();
    } catch (err: any) {
      mostrarToast(err?.response?.data?.detail ?? "Error al eliminar la naviera.", "error");
    } finally {
      setEliminandoId(null);
      setConfirmarId(null);
    }
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <BotonVolver to="/dashboard" />
          <div className={styles.headerCenter}>
            <img src="/images/logo-snm.png" alt="SNM" className={styles.logo} />
            <div className={styles.headerText}>
              <div className={styles.org}>Servicio Nacional de Migración</div>
              <div className={styles.app}>FileTransfer - SNM</div>
            </div>
          </div>
          <div className={styles.headerRight}>
            <MenuCabecera />
          </div>
        </div>
      </header>

      <main className={styles.body}>
        <div className={styles.container}>
          <div className={styles.pageTitle}>
            <span className={styles.titleIcon}><IconoGrafico tamano={22} /></span>
            <div>
              <h1>Estadísticas del sistema</h1>
              <p>Métricas globales de uso del sistema FileTransfer.</p>
            </div>
          </div>

          {error && <div className={styles.errorMsg}>{error}</div>}

          {cargando ? (
            <div className={styles.loading}><span className={styles.spinner} /> Cargando estadísticas…</div>
          ) : stats && (
            <>
              {/* ── Métricas ── */}
              <div className={styles.statGrid}>
                <div className={styles.statCard}>
                  <div className={`${styles.statIcon} ${styles.yellow}`}><IconoUsuario /></div>
                  <div className={styles.statNum}>{stats.usuarios}</div>
                  <div className={styles.statLabel}>Usuarios registrados</div>
                </div>
                <div className={styles.statCard}>
                  <div className={`${styles.statIcon} ${styles.green}`}><IconoActividad tamano={22} /></div>
                  <div className={styles.statNum}>{stats.activas}</div>
                  <div className={styles.statLabel}>Transferencias activas</div>
                </div>
                <div className={styles.statCard}>
                  <div className={`${styles.statIcon} ${styles.gray}`}><IconoReloj tamano={22} /></div>
                  <div className={styles.statNum}>{stats.expiradas}</div>
                  <div className={styles.statLabel}>Transferencias expiradas</div>
                </div>
                <div className={styles.statCard}>
                  <div className={`${styles.statIcon} ${styles.blue}`}><IconoDescargar tamano={22} /></div>
                  <div className={styles.statNum}>{stats.total_descargas}</div>
                  <div className={styles.statLabel}>Descargas totales</div>
                </div>
                <div className={styles.statCard}>
                  <div className={`${styles.statIcon} ${styles.purple}`}><IconoDisco /></div>
                  <div className={styles.statNum}>{formatBytes(stats.storage_bytes)}</div>
                  <div className={styles.statLabel}>Almacenamiento usado</div>
                </div>
                <div className={styles.statCard}>
                  <div className={`${styles.statIcon} ${styles.orange}`}><IconoAncla tamano={16} /></div>
                  <div className={styles.statNum}>{stats.puertos.length}</div>
                  <div className={styles.statLabel}>Puertos</div>
                </div>
              </div>

              {/* ── Puertos + Navieras ── */}
              <div className={styles.twoCol}>
                {/* Puertos */}
                <EntityPanel
                  title="Puertos"
                  icon={<IconoAncla tamano={16} />}
                  items={stats.puertos.map(p => ({
                    id: p.id,
                    nombre: p.nombre,
                    extra: `${p.total} naviera${p.total !== 1 ? "s" : ""}`,
                  }))}
                  addLabel="Nuevo puerto"
                  addLoading={creandoPuerto}
                  deleteId={elimPuertoId}
                  confirmId={confirmarPuerto}
                  setConfirmId={setConfirmarPuerto}
                  formError={errPuerto}
                  onAdd={alCrearPuerto}
                  onDelete={alEliminarPuerto}
                  formFields={
                    <>
                      <input
                        className={styles.inputField}
                        placeholder="Nombre del puerto *"
                        value={nuevoPuertoNombre}
                        onChange={e => setNuevoPuertoNombre(e.target.value)}
                        required autoFocus
                      />
                      <input
                        className={styles.inputField}
                        placeholder="Descripción (opcional)"
                        value={nuevoPuertoDesc}
                        onChange={e => setNuevoPuertoDesc(e.target.value)}
                      />
                    </>
                  }
                />

                {/* Navieras */}
                <EntityPanel
                  title="Navieras"
                  icon={<IconoCarpeta />}
                  items={stats.carpetas.map(c => {
                    const puerto = stats.puertos.find(p => p.id === c.puerto_id);
                    return {
                      id: c.id,
                      nombre: c.nombre,
                      extra: [
                        puerto ? `Puerto: ${puerto.nombre}` : null,
                        `${c.total} transferencia${c.total !== 1 ? "s" : ""}`,
                      ].filter(Boolean).join(" · "),
                    };
                  })}
                  addLabel="Nueva naviera"
                  addLoading={creando}
                  deleteId={eliminandoId}
                  confirmId={confirmarId}
                  setConfirmId={setConfirmarId}
                  formError={errCarpeta}
                  onAdd={alCrearCarpeta}
                  onDelete={alEliminarCarpeta}
                  formFields={
                    <>
                      <input
                        className={styles.inputField}
                        placeholder="Nombre de la naviera *"
                        value={nuevaNombre}
                        onChange={e => setNuevaNombre(e.target.value)}
                        required autoFocus
                      />
                      <select
                        className={styles.inputField}
                        value={nuevaPuertoId}
                        onChange={e => setNuevaPuertoId(e.target.value === "" ? "" : Number(e.target.value))}
                      >
                        <option value="">— Sin puerto —</option>
                        {stats.puertos.map(p => (
                          <option key={p.id} value={p.id}>{p.nombre}</option>
                        ))}
                      </select>
                      <input
                        className={styles.inputField}
                        placeholder="Descripción (opcional)"
                        value={nuevaDesc}
                        onChange={e => setNuevaDesc(e.target.value)}
                      />
                    </>
                  }
                />
              </div>

              {/* ── Top subidores ── */}
              <section className={styles.panel} style={{ marginTop: 20 }}>
                <div className={styles.panelHeader}>
                  <IconoTrofeo />
                  Top subidores
                </div>
                <div className={styles.panelBody}>
                  {stats.top_uploaders.length === 0 ? (
                    <p className={styles.empty}>Sin datos aún.</p>
                  ) : (
                    <div className={styles.uploaderList}>
                      {stats.top_uploaders.map((u, i) => (
                        <div key={u.id} className={styles.uploaderRow}>
                          <div className={`${styles.rankBadge} ${i === 0 ? styles.rankGold : i === 1 ? styles.rankSilver : i === 2 ? styles.rankBronze : ""}`}>
                            {i + 1}
                          </div>
                          <div className={styles.uploaderAvatar}>
                            {(u.full_name?.[0] ?? "?").toUpperCase()}
                          </div>
                          <div className={styles.uploaderInfo}>
                            <div className={styles.uploaderName}>{u.full_name}</div>
                          </div>
                          <div className={styles.uploaderCount}>
                            <span className={styles.uploaderNum}>{u.total}</span>
                            <span className={styles.uploaderLabel}>transfer{u.total !== 1 ? "encias" : "encia"}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </section>
            </>
          )}
        </div>
      </main>

      <footer className={styles.footer}>
        Servicio Nacional de Migración &copy; {new Date().getFullYear()} &mdash; Todos los derechos reservados
      </footer>
    </div>
  );
}
