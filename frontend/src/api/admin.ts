import { clienteApi } from "./client";
import type { Puerto } from "../types";

export interface UsuarioAD {
  dn: string;
  username: string;
  name: string;
  last_name: string;
  email: string;
  guid: string;
  department: string;
}

export interface RolMini {
  id: number;
  nombre: string;
  es_sistema: boolean;
}

export interface UsuarioSistema {
  id: number;
  username: string;
  name: string | null;
  last_name: string | null;
  email: string | null;
  user_type: "ad" | "local";
  status: "active" | "inactive";
  rol_id: number | null;
  rol_personalizado: RolMini | null;
  full_name: string;
  puertos_asignados?: { id: number; nombre: string }[];
}

export interface Permiso {
  id: number;
  codigo: string;
  nombre: string;
  descripcion: string | null;
  created_at: string;
}

export interface Rol {
  id: number;
  nombre: string;
  descripcion: string | null;
  es_sistema: boolean;
  created_at: string;
  permisos: Permiso[];
  total_usuarios: number;
}

export interface StatsAdmin {
  usuarios:        number;
  transferencias:  number;
  activas:         number;
  expiradas:       number;
  total_descargas: number;
  storage_bytes:   number;
  puertos:         { id: number; nombre: string; total: number }[];
  top_uploaders:   { id: number; full_name: string; total: number }[];
}

export const apiAdmin = {
  buscarEnAD: (q: string) =>
    clienteApi.get<UsuarioAD[]>(`/admin/usuarios/buscar-ad`, { params: { q } }),

  listarUsuarios: () =>
    clienteApi.get<UsuarioSistema[]>("/admin/usuarios"),

  crearUsuario: (username: string) =>
    clienteApi.post<UsuarioSistema>("/admin/usuarios", { username }),

  cambiarEstado: (id: number, status: "active" | "inactive") =>
    clienteApi.patch<UsuarioSistema>(`/admin/usuarios/${id}/estado`, { status }),

  eliminarUsuario: (id: number) =>
    clienteApi.delete(`/admin/usuarios/${id}`),

  // Puertos
  listarPuertos: () =>
    clienteApi.get<Puerto[]>("/admin/puertos"),

  crearPuerto: (nombre: string, descripcion?: string) =>
    clienteApi.post<Puerto>("/admin/puertos", { nombre, descripcion }),

  eliminarPuerto: (id: number) =>
    clienteApi.delete(`/admin/puertos/${id}`),

  // Stats
  obtenerStats: () =>
    clienteApi.get<StatsAdmin>("/admin/stats"),

  // Permisos
  listarPermisos: () =>
    clienteApi.get<Permiso[]>("/admin/permisos"),

  crearPermiso: (codigo: string, nombre: string, descripcion?: string) =>
    clienteApi.post<Permiso>("/admin/permisos", { codigo, nombre, descripcion }),

  actualizarPermiso: (id: number, datos: { nombre?: string; descripcion?: string }) =>
    clienteApi.patch<Permiso>(`/admin/permisos/${id}`, datos),

  eliminarPermiso: (id: number) =>
    clienteApi.delete(`/admin/permisos/${id}`),

  // Roles
  listarRoles: () =>
    clienteApi.get<Rol[]>("/admin/roles"),

  crearRol: (nombre: string, descripcion?: string) =>
    clienteApi.post<Rol>("/admin/roles", { nombre, descripcion }),

  actualizarRol: (id: number, datos: { nombre?: string; descripcion?: string }) =>
    clienteApi.patch<Rol>(`/admin/roles/${id}`, datos),

  eliminarRol: (id: number) =>
    clienteApi.delete(`/admin/roles/${id}`),

  asignarPermisosARol: (id: number, permiso_ids: number[]) =>
    clienteApi.put<Rol>(`/admin/roles/${id}/permisos`, { permiso_ids }),

  asignarRolAUsuario: (user_id: number, rol_id: number | null) =>
    clienteApi.patch<UsuarioSistema>(`/admin/usuarios/${user_id}/rol-personalizado`, { rol_id }),

  // ── Asignación de puertos a operadores del muelle ──
  obtenerPuertosUsuario: (user_id: number) =>
    clienteApi.get<{ id: number; nombre: string }[]>(`/admin/usuarios/${user_id}/puertos`),

  asignarPuertosAUsuario: (user_id: number, puerto_ids: number[]) =>
    clienteApi.put<{ id: number; nombre: string }[]>(
      `/admin/usuarios/${user_id}/puertos`,
      { puerto_ids },
    ),
};
