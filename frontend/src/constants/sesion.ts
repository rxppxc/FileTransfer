/**
 * Constantes de gestión de sesión.
 *
 * El backend emite tokens con `ACCESS_TOKEN_EXPIRE_MINUTES` (60 por defecto).
 * Aquí cerramos la sesión por inactividad 15 minutos antes, con un aviso de
 * 2 minutos para que el usuario pueda extenderla.
 */

export const AVISO_INACTIVIDAD_MS = 13 * 60 * 1000;  // mostrar modal a los 13 min de inactividad
export const LOGOUT_INACTIVIDAD_MS = 15 * 60 * 1000; // cerrar sesión a los 15 min de inactividad
export const CUENTA_REGRESIVA_SEG  = 2 * 60;         // duración del contador del modal (segundos)
