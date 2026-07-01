/**
 * Constantes del módulo de subida de archivos.
 * Mantener alineado con `MAX_FILE_SIZE_MB` del backend.
 */

export const TAMANIO_MAX_BYTES = 100 * 1024 * 1024;  // 100 MB por archivo
export const TAMANIO_MAX_MB    = 100;

export const EXTENSION_PDF = ".pdf";
export const TIPOS_ACEPTADOS_AMPLIO = [
  ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
  ".odt", ".ods", ".odp", ".txt", ".rtf", ".csv",
  ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".tiff",
  ".zip", ".rar", ".7z",
].join(",");
