# FileTransfer SNM

Sistema interno de transferencia de archivos del **Servicio Nacional de Migración (SNM) de Panamá**.

Permite a las navieras enviar documentación al Sector Pacífico, que valida y procesa la información antes de generar enlaces públicos de descarga para los destinatarios.

---

## Tecnologías

| Capa | Stack |
|---|---|
| **Backend** | Python 3.12 · FastAPI · SQLAlchemy 2 async · PostgreSQL · LDAP (Active Directory) · JWT |
| **Frontend** | React 19 · TypeScript estricto · Vite · CSS Modules · React Router v7 |
| **Infraestructura** | Uvicorn · WAMP (Windows) · PostgreSQL local · Slowapi (rate limit) |

---

## Arranque rápido

### Requisitos
- Python 3.12+
- Node.js 22+
- PostgreSQL con base `migradrop` creada
- Acceso a un servidor LDAP / Active Directory

### Primera vez
```bat
:: Copiar plantilla de entorno y editarla con valores reales
copy backend\.env.example backend\.env
:: Editar backend\.env con SECRET_KEY, DATABASE_URL, LDAP_*, etc.

:: Instalar dependencias del backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

:: Instalar dependencias del frontend
cd ..\frontend
npm install
```

### Desarrollo (dos terminales)
```bat
:: Terminal 1 (backend con --reload)
start-backend.bat

:: Terminal 2 (Vite dev server)
start-frontend.bat
```
Frontend en `http://localhost:5173`, backend en `http://localhost:8000`, docs API en `http://localhost:8000/api/docs` (solo si `APP_ENV=development`).

### Producción
```bat
:: APP_ENV=production en backend\.env, FRONTEND_URL apuntando al dominio real
:: Compilar frontend
cd frontend && npm run build

:: Servir el backend (sirve también el dist/ del frontend)
start-backend-prod.bat
```

---

## Estructura

```
migradrop/
├─ backend/
│  ├─ app/
│  │  ├─ main.py                # arranque FastAPI + lifespan + CORS + rutas
│  │  ├─ api/v1/                # endpoints HTTP (auth, transfers, admin)
│  │  ├─ core/                  # config, JWT, LDAP, email, rate-limit, http utils
│  │  ├─ domain/
│  │  │  ├─ models/             # ORM (SQLAlchemy 2)
│  │  │  ├─ schemas/            # contratos Pydantic (request/response)
│  │  │  ├─ repositories/       # acceso a BD (un repo por agregado)
│  │  │  └─ services/           # lógica de negocio (orquesta repos + reglas)
│  │  └─ infrastructure/
│  │     ├─ database.py         # engine async + sesión + Base
│  │     └─ migraciones.py      # ALTER/CREATE idempotentes ejecutados al arranque
│  ├─ alembic/                  # migraciones formales (reservado para esquemas nuevos)
│  └─ storage/transfers/        # archivos subidos (NO versionar)
│
└─ frontend/
   └─ src/
      ├─ App.tsx                # rutas + providers (tema, notificaciones, sesión)
      ├─ api/                   # cliente axios + módulos por dominio
      ├─ components/            # UI reutilizable (Iconos, modales, menús)
      ├─ context/               # ContextoTema (claro/oscuro)
      ├─ hooks/                 # useAutenticacion, usePermisos
      ├─ modulos/
      │  ├─ autenticacion/      # login
      │  ├─ transferencias/     # panel, subida, edición, corrección, vista pública
      │  └─ administracion/     # usuarios, roles, estadísticas
      ├─ constants/             # números mágicos centralizados
      ├─ types/                 # tipos compartidos
      └─ utils/                 # helpers (formato, fechas)
```

---

## Flujos clave

### Autenticación
1. Usuario envía credenciales de dominio AD a `POST /api/v1/auth/login`.
2. Backend hace bind contra LDAP; si pasa, busca/crea el `Usuario` en la BD.
3. Devuelve `access_token` (JWT) que el frontend guarda en `localStorage`.
4. **Cada request verifica en BD que el usuario sigue activo** (revocación inmediata si se desactiva).
5. Token vive `ACCESS_TOKEN_EXPIRE_MINUTES` minutos; el frontend lo refresca con `POST /api/v1/auth/refresh`.

### Transferencia — flujo completo

Tres roles operativos se relevan en cadena:

| Rol | Permiso | Qué hace |
|---|---|---|
| **Naviera** | `T-CREAR-BASICA` | Sube archivos + comentarios + selecciona destinatarios. Queda como borrador esperando revisión. |
| **Sector Pacífico** | `T-PROCESAR-PACIFICO` | Revisa el borrador. Si algo falta lo devuelve con motivo (se envía correo a la Naviera). Si está bien, edita la info y asigna el **puerto/muelle destino** → estado `active`. |
| **Muelle/Operador** | `T-PROCESAR-MUELLE` | Ve solo las transferencias de los **puertos que tiene asignados** en la vista jerárquica Puerto → Naviera → Marino. Puede: descargar, copiar enlace público, marcar como procesada (fin del flujo) o devolver al Sector Pacífico con motivo. |

**Estados de una transferencia:**
- `draft` — Naviera la creó, esperando revisión.
- `returned` — SP la devolvió a la Naviera con motivo. La Naviera recibe correo con enlace directo a corrección.
- `active` — SP la procesó. Visible por el Muelle/Operador del puerto asignado.
- `review` — Muelle la devolvió a SP con motivo (badge naranja "Devuelto por Muelle").
- `processed` — Muelle la marcó como procesada. Estado final.
- `expired` / `deleted` — venció o fue eliminada.

El destinatario final recibe correo con enlace `/t/{token}` y descarga sin autenticación (rate-limited a 30/min por IP).

**Configurar el rol Muelle/Operador (manual, sola vez):**
1. `/admin/roles` → panel Permisos → **Nuevo permiso**: código `T-PROCESAR-MUELLE`, nombre "Operar muelle", descripción libre.
2. Panel Roles → **Nuevo rol**: nombre "Muelle/Operador", asígnale ese permiso.
3. `/admin` → seleccionar el usuario, elegir el rol "Muelle/Operador" y hacer clic en **Puertos (N)** para marcar los puertos que va a operar.

### Permisos
- `Rol` agrupa `Permiso`s. Cada usuario tiene un `rol_id` opcional.
- `rol_personalizado.nombre === "Administrador"` es la **única** verificación de admin en frontend y backend (ver [usePermisos.ts](frontend/src/hooks/usePermisos.ts) y `core/permisos.py`).
- Permisos clave: `T-CREAR-BASICA`, `T-CREAR-COMPLETA`, `T-PROCESAR-PACIFICO`.

---

## Convenciones del proyecto

### Idioma del código
- **Español**: variables, funciones, clases, componentes React, archivos, carpetas, contextos, hooks creados aquí, mensajes de usuario.
- **Inglés (conservado)**: nombres de librerías importadas, métodos de SQLAlchemy/FastAPI/React, columnas SQL existentes (`title`, `message`, `status`, etc.), claves del payload JSON de la API (`access_token`, `expires_at`, etc.) y prefijo `use*` de hooks React.

Renombrar columnas BD o claves de API rompería contratos en uso, por eso se documenta en lugar de cambiarse. Ver sección "Decisiones documentadas" abajo.

### Naming
- Backend Python: `snake_case` para funciones/variables, `PascalCase` para clases, `UPPER_SNAKE_CASE` para constantes.
- Frontend TS/React: `camelCase` para variables/funciones, `PascalCase` para componentes/tipos, `UPPER_SNAKE_CASE` para constantes.
- Hooks React siempre comienzan con `use` (`useAutenticacion`, `usePermisos`, `useNotificacion`, `useConfirmar`, `useTema`).

### Organización
- Backend sigue patrón Repository + Service. Endpoints HTTP solo orquestan, la lógica vive en `domain/services/`.
- Frontend agrupa por **módulo de negocio** (`modulos/transferencias/`), no por tipo (`components/`, `pages/`). Un módulo contiene sus páginas y CSS Modules.
- Constantes mágicas centralizadas en `frontend/src/constants/` y `backend/app/core/config.py`.

### Seguridad
- `SECRET_KEY` rota cada 90 días.
- LDAP injection: usar `ldap3.utils.conv.escape_filter_chars()` siempre.
- Path traversal: validar `resolve().relative_to(raiz)` antes de servir archivos.
- Rate limit en `/login`, `/download`, `/preview`.
- MIME real con `python-magic` (no confiar en el header del cliente).
- Nombre de archivo sanitizado para evitar XSS en `Content-Disposition`.

### Errores
- Backend: lanzar `HTTPException` con código y `detail` claro; nunca `except: pass`. Loggear con `logger.warning/.error`.
- Frontend: usar `useNotificacion()` para errores visibles, `useConfirmar()` para acciones destructivas. Nunca `alert()` ni `confirm()`.

---

## Decisiones documentadas

### Por qué `title`, `message`, `status`, etc. siguen en inglés
Son **columnas SQL existentes** con datos en producción. Renombrarlas requeriría:
1. `ALTER TABLE ... RENAME COLUMN` en migración Alembic con downtime.
2. Actualizar `domain/models/transfer.py`.
3. Actualizar `domain/schemas/transfer.py` (rompe API).
4. Actualizar TODOS los lugares del frontend que consumen esos campos.
5. Versionar la API (`/api/v2/`) o coordinar despliegue atómico front+back.

Pendiente para una migración planificada con downtime controlado, no urgente.

### Por qué `useToast` se renombró pero `useNavigate` no
Lo nuestro lo controlamos; las librerías externas no. `useNavigate`, `useState`, `useEffect`, etc. son API estable de React Router / React y cambiar sus identificadores rompería con cada actualización de la librería.

### Por qué JWT vive en `localStorage`
Decisión heredada. Para migrar a cookie `httpOnly` se requiere:
1. Backend devolver `Set-Cookie` además del JSON.
2. Implementar CSRF token.
3. Cambiar interceptor axios para usar `withCredentials`.
4. Coordinar despliegue.

Mitigación actual: revocación inmediata via verificación de BD en cada request, sin `console.log` de tokens, rate-limit de login.

---

## Variables de entorno

Ver [backend/.env.example](backend/.env.example) — incluye todas las variables con documentación inline.

Frontend acepta opcionalmente:
- `VITE_API_URL` — base de la API (default: `http://localhost:8000/api/v1`)
- `VITE_PROXY_TARGET` — target del proxy de Vite en dev (default: `http://localhost:8000`)

---

## Scripts útiles

```bat
:: Frontend
npm run dev          # Vite dev server
npm run build        # tsc -b + vite build → dist/
npm run lint         # eslint

:: Backend (con venv activado)
python -m uvicorn app.main:aplicacion --reload --port 8000
alembic upgrade head  # aplicar migraciones formales
```

---

## Reportar problemas

Las decisiones técnicas y guía detallada para asistentes IA están en [CLAUDE.md](CLAUDE.md).
