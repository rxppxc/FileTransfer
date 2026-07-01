import axios from "axios";

export const URL_BASE_API: string =
  import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

// 30s para peticiones normales (GET/POST/PATCH/DELETE). Las subidas y
// descargas grandes definen su propio timeout via la opción `timeout` de cada
// llamada, así que esto solo afecta a los JSON.
const TIMEOUT_MS = 30_000;

export const clienteApi = axios.create({
  baseURL: URL_BASE_API,
  timeout: TIMEOUT_MS,
  headers: { "Content-Type": "application/json" },
});

clienteApi.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

clienteApi.interceptors.response.use(
  (respuesta) => respuesta,
  (error) => {
    // Cualquier 401 implica token inválido/revocado → forzar re-login.
    if (error?.response?.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);
