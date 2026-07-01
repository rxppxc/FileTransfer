# Guía para asistentes IA — FileTransfer SNM

Este archivo se carga automáticamente al iniciar un asistente Claude Code en este repositorio. Contiene contexto que NO está obvio leyendo el código.

## Resumen en una frase

App interna del Servicio Nacional de Migración (Panamá) para que las navieras envíen documentación de buques y marinos al Sector Pacífico; éste valida y emite enlaces públicos de descarga.

## Stack
- Backend: FastAPI + SQLAlchemy 2 async + PostgreSQL + LDAP/AD + JWT (`python-jose`)
- Frontend: React 19 + TypeScript estricto + Vite + CSS Modules + React Router v7
- Rate limit: `slowapi` (almacenamiento en memoria — para multi-worker mover a Redis)
- MIME real: `python-magic` (binario `libmagic` en Windows via `python-magic-bin`)

## Convenciones críticas

### Idioma
Todo el código nuevo va en **español** (variables, funciones, clases, componentes, archivos, carpetas). Excepciones que se mantienen en inglés:

| Caso | Por qué |
|---|---|
| `useState`, `useEffect`, `useNavigate`, etc. | API de React/React Router |
| `title`, `message`, `recipient`, `status`, `expires_at`, etc. | Columnas SQL con datos en producción — renombrar requiere migración con downtime |
| `access_token`, `token_type`, claves JSON de la API | Contrato HTTP con el frontend; ver "Por qué no renombrar" en README |
| `username`, `password` en `SolicitudLogin` | Convención HTTP estándar |
| Prefijo `use*` de hooks | Convención React no negociable |
| `logger`, `Exception`, `dict`, etc. | Símbolos de la librería estándar Python |

Cuando agregues nombres nuevos, hazlo en español. Cuando toques nombres existentes, no los renombres "porque sí" — verifica primero si son de los inamovibles arriba.

### Naming
- Backend Python: `snake_case` funciones/variables, `PascalCase` clases, `UPPER_SNAKE` constantes.
- Frontend: `camelCase` variables/funciones, `PascalCase` componentes/tipos, `UPPER_SNAKE` constantes.
- Repositorios: `Repositorio<Agregado>` (ej. `RepositorioTransferencia`).
- Servicios: `Servicio<Dominio>` (ej. `ServicioTransferencia`).
- Schemas Pydantic: `Datos<Accion>` para entrada (request body), `Salida<Modelo>` o `Respuesta<X>` para respuesta.
- Páginas React: `Pagina<X>` (ej. `PaginaPanel`, `PaginaSubida`).
- Hooks: `use<Cosa>` (`useAutenticacion`, `usePermisos`, `useNotificacion`).
- Componentes utilitarios: nombre descriptivo en español (`BotonVolver`, `ModalConfirmacion`).

### Estructura

**Backend (DDD ligero)**:
```
api/v1/          → endpoints (router). Solo orquestan, no llevan lógica.
domain/services/ → reglas de negocio. Aquí van validaciones, FK checks, etc.
domain/repositories/ → único punto de acceso a la BD por agregado.
domain/models/   → ORM (SQLAlchemy 2). Tablas + relaciones.
domain/schemas/  → contratos (Pydantic). Entrada/salida HTTP.
core/            → cosas transversales: config, JWT, LDAP, email, rate limit.
infrastructure/  → engine BD, migraciones runtime, init.
```

**Frontend (módulos por dominio)**:
```
modulos/<dominio>/  → páginas + CSS modules de ese dominio.
components/         → UI reutilizable entre módulos.
context/            → providers globales (tema).
hooks/              → hooks compartidos.
api/                → cliente HTTP + módulos por dominio.
constants/          → números mágicos.
```

### Seguridad — reglas no negociables
1. **Nunca** usar f-string para construir filtros LDAP. Usar `escape_filter_chars()`.
2. **Nunca** servir archivos sin validar que la ruta resuelta esté dentro de la raíz permitida (`.resolve().relative_to(raiz)`).
3. **Nunca** confiar en el `content_type` que envía el cliente — usar `python-magic` sobre el contenido.
4. **Nunca** loguear tokens, contraseñas ni el DN LDAP completo.
5. **Nunca** loguear queries SQL en producción (`echo=False` cuando `APP_ENV=production`).
6. **Nunca** versionar `.env`. Está en `.gitignore`. Si el usuario lo va a versionar, avisar.
7. **Nunca** usar `--no-verify`, `--no-gpg-sign`, ni saltarse hooks de git sin permiso explícito.
8. JWT se verifica contra BD en cada request — esto es **a propósito** para revocación inmediata. No lo conviertas en caché sin pensar el trade-off.
9. Rate limit en `/login`, `/download`, `/preview` — si agregas otro endpoint público, agrégalo.

### Errores
- Backend: `HTTPException` con código y `detail` descriptivo. Nunca `except: pass`. Loggear con `logger.warning/.error` con contexto.
- Frontend: `useNotificacion()` (toast) para errores, `useConfirmar()` (modal) para acciones destructivas. **Nunca** `alert()` ni `window.confirm()`.

### Async correcto
- Backend: SQLAlchemy async siempre. No mezclar `Session` sincrónica.
- Si necesitas ejecutar CPU-bound (zip, hashing), usar `asyncio.to_thread()`.
- `obtener_sesion_bd()` ya hace `commit` en éxito y `rollback` en excepción — no hacerlo manualmente en endpoints.

### Frontend strict
- `tsconfig` con `strict: true`. Si necesitas `any`, justifica el `// any` con un comentario.
- TS quita `noUnusedLocals` y `noUnusedParameters`. Si una variable sale, eliminarla.
- `eslint-plugin-react-hooks` en exhaustive deps. Si quitas una dep, deja `// eslint-disable-next-line` con el porqué.

## Estado actual (snapshot 2026-06-30)

### Lo que se hizo en el último gran refactor
- Hispanizado masivo de carpetas (`features/` → `modulos/`) y páginas (`LoginPage` → `PaginaLogin`).
- Hispanizado de componentes (`ErrorBoundary` → `CapturadorErrores`, `HeaderMenu` → `MenuCabecera`, `Toast` → `Notificaciones`, `ConfirmModal` → `ModalConfirmacion`, `BackButton` → `BotonVolver`, `ThemeContext` → `ContextoTema`, etc.).
- Catálogo único de iconos (49 exports) en `components/Iconos.tsx` — antes había 104 SVG duplicados.
- Auditoría de seguridad aplicada: path traversal cerrado, CORS estricto, LDAP escape, rate limit, JWT con revocación, MIME real, sanitización de nombres, FK validation previa.
- TS `strict: true` activado (con `noImplicitAny: false` por código legacy).
- Sistema de toast + modal de confirmación para reemplazar `alert()` y `confirm()`.

### Lo que sigue pendiente (no urgente)
1. **JWT en cookie httpOnly** — actualmente en localStorage. Plan en README → "Decisiones documentadas".
2. **Renombrar columnas BD** (`title` → `titulo`, etc.) — requiere migración Alembic + cambios coordinados.
3. **Renombrar campos JSON de la API** — depende del punto anterior; rompería contrato.
4. **Redis para rate limit** si se escala a multi-worker.
5. **ZIP streaming real** con `zipstream-ng` para descargas multi-archivo gigantes.
6. **Refactor de componentes >300 líneas** (`PaginaPanel`, `PaginaEditarTransferencia`) extrayendo subcomponentes y hooks.
7. **Backup automático de BD** — no configurado.

### Roles y estados actuales (post-flujo Muelle)

**Roles operativos:**
- **Naviera** (permiso `T-CREAR-BASICA`) — crea borradores, corrige devoluciones.
- **Sector Pacífico** (permiso `T-PROCESAR-PACIFICO`) — cola de revisión unificada (borradores + devueltos por muelle). Aprobar = asignar puerto → `active`.
- **Muelle/Operador** (permiso `T-PROCESAR-MUELLE`) — ve la jerarquía Puerto → Naviera → Marino **solo de los puertos que tiene asignados** (tabla `usuarios_puertos`). Puede marcar procesada o devolver a SP.
- **Administrador** — ve todo.

**Estados de `transfers.status`:**
`draft`, `returned` (SP devolvió a Naviera), `review` (Muelle devolvió a SP), `active`, `processed` (fin), `expired`, `deleted`.

**El permiso `T-PROCESAR-MUELLE` y el rol "Muelle/Operador" NO se siembran automáticamente.** El admin los crea manualmente en `/admin/roles` — es una decisión explícita del dueño del sistema para conservar el patrón de que solo los tres roles originales del flujo se sembren. Si los endpoints `/transfers/cola-muelle`, `/procesada`, `/devolver-muelle` se llaman antes de crear el permiso, devuelven 403 sin efectos colaterales.

**Correo de devoluciones (`enviar_notificacion_devolucion` en `core/email.py`):**
- Cuando SP devuelve a Naviera → correo a la Naviera dueña con enlace a `/transfers/{id}/corregir`.
- Cuando Muelle devuelve a SP → correo al `MAIL_FROM` con enlace a `/dashboard`. El motivo se muestra destacado con franja roja.

### Lo que no debe romperse
- El flujo Naviera → borrador → Pacífico → activa → destinatario.
- El proxy de Vite (`/api` → backend) en dev.
- La verificación de admin via `rol_personalizado.nombre === "Administrador"` (única fuente de verdad).
- Las migraciones runtime en `infrastructure/migraciones.py` deben ser **idempotentes** (siempre con `IF NOT EXISTS` / `IF EXISTS`).

## Cómo trabajar acá

### Antes de cambiar código
1. Lee el módulo completo antes de editar. La estructura DDD no es opcional.
2. Si vas a tocar el contrato HTTP (schemas o endpoints), busca primero quién los consume en el frontend con Grep.
3. Si vas a tocar la BD, revisa `infrastructure/migraciones.py` para ver si tu cambio necesita una migración nueva (idempotente).

### Antes de proponer un cambio grande
Hacé una pregunta corta primero. El proyecto está en producción de un organismo gubernamental, los cambios silenciosos no son gratis.

### Comandos útiles
```bat
:: Backend: validar imports rápido
cd backend && venv\Scripts\python -c "from app.main import aplicacion"

:: Frontend: typecheck
cd frontend && node node_modules/typescript/bin/tsc -b --noEmit

:: Arranque dev (dos terminales separadas)
start-backend.bat
start-frontend.bat

:: Health check
curl http://localhost:8000/api/health
```

### Estilo de respuesta esperado
- Hablar español al usuario (es panameño, comunicación informal "vos/tú" ok).
- Resúmenes cortos al final, no parrafadas.
- Si modificás varios archivos, listar los paths al final con `path:linea`.
- Si una decisión rompe contrato (BD/API), avisar **antes** de hacerlo.
