import { clienteApi, URL_BASE_API } from "./client";
import type { Transferencia, TransferenciaPublica, Carpeta } from "../types";

interface PuertoPublico { id: number; nombre: string; }

export const apiTransferencias = {
  listar: () =>
    clienteApi.get<Transferencia[]>("/transfers/").then((r) => r.data),

  listarCarpetas: () =>
    clienteApi.get<Carpeta[]>("/transfers/carpetas").then((r) => r.data),

  listarPuertos: () =>
    clienteApi.get<PuertoPublico[]>("/transfers/puertos").then((r) => r.data),

  crear: (formulario: FormData) =>
    clienteApi.post<Transferencia>("/transfers/", formulario, {
      headers: { "Content-Type": "multipart/form-data" },
    }).then((r) => r.data),

  obtenerPublica: (token: string) =>
    clienteApi.get<TransferenciaPublica>(`/transfers/public/${token}`).then((r) => r.data),

  urlDescarga: (token: string) =>
    `${URL_BASE_API}/transfers/download/${token}`,

  urlPreview: (token: string, fileId: number) =>
    `${URL_BASE_API}/transfers/preview/${token}/${fileId}`,

  eliminar: (token: string) =>
    clienteApi.delete(`/transfers/${token}`),

  // ── Flujo Naviera / Sector Pacifico ──
  crearBorrador: (formulario: FormData) =>
    clienteApi.post<Transferencia>("/transfers/borrador", formulario, {
      headers: { "Content-Type": "multipart/form-data" },
    }).then((r) => r.data),

  listarTodasActivas: () =>
    clienteApi.get<Transferencia[]>("/transfers/todas-activas").then((r) => r.data),

  colaPacifico: () =>
    clienteApi.get<Transferencia[]>("/transfers/cola-pacifico").then((r) => r.data),

  obtenerPorId: (id: number) =>
    clienteApi.get<Transferencia>(`/transfers/by-id/${id}`).then((r) => r.data),

  procesar: (id: number, datos: {
    title?: string; message?: string; recipient?: string;
    expiry_days?: number; max_downloads?: number;
    carpeta_id?: number | null; puerto_id?: number | null; marino?: string | null;
    observaciones?: string | null;
  }) =>
    clienteApi.patch<Transferencia>(`/transfers/by-id/${id}/procesar`, datos).then((r) => r.data),

  agregarArchivos: (id: number, formulario: FormData) =>
    clienteApi.post<Transferencia>(`/transfers/by-id/${id}/archivos`, formulario, {
      headers: { "Content-Type": "multipart/form-data" },
    }).then((r) => r.data),

  quitarArchivo: (id: number, archivoId: number) =>
    clienteApi.delete<Transferencia>(`/transfers/by-id/${id}/archivos/${archivoId}`).then((r) => r.data),

  reenviar: (id: number, datos: { message?: string; expiry_days?: number }) =>
    clienteApi.post<Transferencia>(`/transfers/by-id/${id}/reenviar`, datos).then((r) => r.data),

  devolver: (id: number, motivo: string) =>
    clienteApi.post<Transferencia>(`/transfers/by-id/${id}/devolver`, { motivo }).then((r) => r.data),

  resubmit: (id: number) =>
    clienteApi.post<Transferencia>(`/transfers/by-id/${id}/resubmit`).then((r) => r.data),

  corregirAgregarArchivos: (id: number, formulario: FormData) =>
    clienteApi.post<Transferencia>(`/transfers/by-id/${id}/corregir/archivos`, formulario, {
      headers: { "Content-Type": "multipart/form-data" },
    }).then((r) => r.data),

  corregirQuitarArchivo: (id: number, archivoId: number) =>
    clienteApi.delete<Transferencia>(`/transfers/by-id/${id}/corregir/archivos/${archivoId}`).then((r) => r.data),

  // ── Flujo Muelle / Operador ──
  colaMuelle: () =>
    clienteApi.get<Transferencia[]>("/transfers/cola-muelle").then((r) => r.data),

  marcarProcesada: (id: number) =>
    clienteApi.post<Transferencia>(`/transfers/by-id/${id}/procesada`).then((r) => r.data),

  devolverMuelle: (id: number, motivo: string) =>
    clienteApi.post<Transferencia>(`/transfers/by-id/${id}/devolver-muelle`, { motivo }).then((r) => r.data),
};
