export type EstadoTransferencia =
  | "draft"      // creada por Naviera, esperando revisión de SP
  | "active"     // SP ya la procesó y asignó puerto → visible por Muelle
  | "expired"    // venció por fecha o descargas
  | "deleted"    // borrada
  | "returned"   // SP la devolvió a la Naviera con motivo
  | "review"     // Muelle la devolvió a SP con motivo (queda en cola SP con badge)
  | "processed"; // Muelle marcó como procesada — fin del flujo
export type EstadoUsuario       = "active" | "inactive";
export type TipoUsuario         = "ad" | "local";

export interface RolPersonalizadoMini {
  id:         number;
  nombre:     string;
  es_sistema: boolean;
}

export interface Usuario {
  id:        number;
  username:  string;
  name:      string | null;
  last_name: string | null;
  email:     string | null;
  user_type: TipoUsuario;
  status:    EstadoUsuario;
  rol_id:    number | null;
  rol_personalizado: RolPersonalizadoMini | null;
  full_name: string;
  puertos_asignados?: { id: number; nombre: string }[];
}

export interface ArchivoTransferencia {
  id:            number;
  original_name: string;
  mime_type:     string | null;
  size:          number;
  es_original?:  boolean;
  subido_por_id?: number | null;
}

export interface Puerto {
  id:          number;
  nombre:      string;
  descripcion: string | null;
  created_at:  string;
  total:       number;
}

export interface Carpeta {
  id:          number;
  nombre:      string;
  descripcion: string | null;
  created_at:  string;
  total:       number;
  puerto_id:   number | null;
  puerto:      { id: number; nombre: string } | null;
}

export interface Transferencia {
  id:            number;
  token:         string;
  title:         string | null;
  message:       string | null;
  recipient:     string | null;
  expires_at:    string | null;
  downloads:     number;
  max_downloads: number | null;
  status:        EstadoTransferencia;
  created_at:    string;
  files:         ArchivoTransferencia[];
  total_size:    number;
  is_expired:    boolean;
  carpeta_id:    number | null;
  carpeta:       { id: number; nombre: string } | null;
  puerto_id:     number | null;
  puerto:        { id: number; nombre: string } | null;
  marino:        string | null;
  user_id?:      number;
  titulo_original?:       string | null;
  mensaje_original?:      string | null;
  destinatario_original?: string | null;
  observaciones?:         string | null;
}

export interface TransferenciaPublica {
  id:            number;
  token:         string;
  title:         string | null;
  message:       string | null;
  expires_at:    string | null;
  downloads:     number;
  max_downloads: number | null;
  is_expired:    boolean;
  files:         ArchivoTransferencia[];
  total_size:    number;
  sender:        string;
}

export interface RespuestaToken {
  access_token: string;
  token_type:   string;
  user:         Usuario;
}

export interface ErrorApi {
  detail: string;
}

