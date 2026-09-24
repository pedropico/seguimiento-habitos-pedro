# Tasks: Seguimiento de Hábitos

**Feature**: `specs/001-seguimiento-habitos`
**Input**: Documentos de diseño desde `specs/001-seguimiento-habitos/` (`spec.md`, `plan.md`, `data-model.md`, `contracts/`, `research.md`, `quickstart.md`)
**Constitution**: `.specify/memory/constitution.md`

> **Definition of Done (DoD) de toda tarea**:
> 1. Código escrito cumpliendo la especificación.
> 2. Test correspondiente escrito y en verde (zero-mock con repositorios falsos para servicios, base real para integración y overrides para API).
> 3. No viola ningún artículo de la constitución aplicable.

---

## Referencia Rápida de Validación por Capa

| Capa | Qué valida esa tarea |
|------|----------------------|
| **Models** | Schemas de entrada/salida separados; relación `usuario_id` declarada con `UniqueConstraint`. |
| **Repositories** | Solo persiste, no valida reglas; recibe sesión por parámetro; devuelve `dict` planos. |
| **Services** | DIP con repo por defecto (`repo=habitos_repository`); una excepción propia por regla; sin importar SQLAlchemy/Session. |
| **Routers** | `usuario_id` siempre desde `get_current_user`; traduce excepción → código HTTP usando diccionario `_CODIGOS`; captura solo `ErrorDeDominio`. |
| **MCP/Tools** | Reutiliza `services/`, nunca reimplementa; error estructurado `{"error": ...}`; descripciones accionables de 3 partes. |

---

## Phase 1: Setup & Cimientos (Shared Infrastructure)

**Purpose**: Inicialización del proyecto, configuración de dependencias, variables de entorno y utilidades puras.

- [x] T001 Crear `pyproject.toml` con dependencias fijadas (incluye `bcrypt<4.1`, `fastapi`, `uvicorn[standard]`, `sqlalchemy>=2.0`, `alembic`, `pyjwt`, `pydantic-settings`, `python-multipart`, `email-validator`, `mcp`, `pytest`, `pytest-cov`, `pytest-asyncio`, `httpx`) y sección `[tool.coverage.run] omit` para exclusiones del Artículo VII.3.
- [x] T002 Crear `.env.example` versionado con todas las variables requeridas (`SECRET_KEY`, `DATABASE_URL`, `ACCESS_TOKEN_EXPIRE_MINUTES`) sin valores reales y configurar `.gitignore` para omitir `.env`.
- [x] T003 [P] Implementar `app/config.py` con `pydantic-settings` para cargar y validar variables desde `.env`.
- [x] T004 [P] Implementar `app/database.py` con `connect_args={"check_same_thread": False}` condicional exclusivo a SQLite (Artículo III.2).
- [x] T005 [P] Implementar funciones puras de normalización y fechas en `app/utils/texto.py` y `app/utils/fechas.py` (Artículo I.4).

---

## Phase 2: Foundational (Modelos, Schemas y Migraciones)

**Purpose**: Modelos SQLAlchemy 2.0, esquemas Pydantic y migraciones Alembic compartidas.

- [x] T006 Implementar modelo `Usuario` en `app/models/usuario.py` con `email` indexado y único, y `hashed_password` (Artículo III.3, IV.1).
- [x] T007 Implementar modelos `Habito` y `RegistroHabito` en `app/models/habito.py` con `FK usuario_id`, `UniqueConstraint(usuario_id, nombre_normalizado)` y `UniqueConstraint(habito_id, fecha)` (Artículo III.3).
- [x] T008 [P] Implementar esquemas Pydantic de entrada y salida diferenciados en `app/schemas/usuario.py` y `app/schemas/habito.py` (`HabitoCreate` no acepta `usuario_id`) (Artículo IV.4, V.3).
- [x] T009 Configurar Alembic (`alembic.ini`, `alembic/env.py` leyendo URL de `app.config.settings`) y generar migración inicial para tablas `usuarios`, `habitos` y `registros_habitos`.
- [x] T010 [P] Implementar repositorio de persistencia `app/repositories/usuarios.py` con funciones que devuelven `dict` (Artículo I.3).
- [x] T011 Implementar repositorio de persistencia `app/repositories/habitos.py` (`crear`, `listar`, `obtener`, `actualizar`, `eliminar`, `buscar_por_nombre`, `existe_registro`, `guardar_registro`, `listar_registros`) donde `listar` siempre filtra por `usuario_id` y `obtener` permite inspección de pertenencia (Artículo I.3, III.3) → test en `tests/test_integracion_habitos.py`.

---

## Phase 3: User Story 1 - Gestión del Ciclo de Vida de Hábitos (Priority: P1) 🎯 MVP

**Goal**: Permitir a usuarios autenticados crear, consultar, actualizar y eliminar sus propios hábitos personales con reglas R1, R2, R3 y R6.

**Independent Test**: Se inyecta `RepositorioFalsoHabitos` en `services/habitos.py` y se ejecutan pruebas unitarias para creación, duplicados, actualización y aislamiento entre usuarios sin usar mocks.

### Tests e Implementación para User Story 1

- [x] T012 [P] [US1] Definir jerarquía de excepciones de dominio en `app/services/errores.py` (`ErrorDeDominio`, `NombreInvalidoError`, `FrecuenciaInvalidaError`, `HabitoDuplicadoError`, `HabitoAjenoError`, `HabitoNoEncontradoError`).
- [x] T013 [P] [US1] Implementar validación atómica `_validar_nombre` (R1) en `app/services/habitos.py` → test unitario `test_R1_nombre_demasiado_corto_es_rechazado` en `tests/test_habitos_service.py`.
- [x] T014 [P] [US1] Implementar validación atómica `_validar_frecuencia` (R2) en `app/services/habitos.py` → tests unitarios `test_R2_frecuencia_fuera_de_rango_es_rechazada` y `test_R2_frecuencia_no_entera_es_rechazada` en `tests/test_habitos_service.py`.
- [x] T015 [US1] Implementar función de orquestación `crear_habito` con control de duplicados normalizados por usuario (R3) en `app/services/habitos.py` → tests unitarios `test_R3_nombre_duplicado_para_el_mismo_usuario_es_rechazado` y `test_R3_el_mismo_nombre_en_otro_usuario_si_se_permite` en `tests/test_habitos_service.py`.
- [x] T016 [US1] Implementar verificación de pertenencia `_habito_propio` (R6) y funciones `actualizar_habito`, `eliminar_habito`, `listar_habitos` y `obtener_habito` en `app/services/habitos.py` → tests unitarios `test_R6_no_se_puede_eliminar_el_habito_de_otro_usuario`, `test_R6_habito_inexistente_se_distingue_de_habito_ajeno` y `test_R6_listar_solo_devuelve_los_habitos_propios` en `tests/test_habitos_service.py`.
- [x] T017 [US1] Implementar lógica de autenticación y registro de usuarios en `app/services/usuarios.py` con hashing seguro de contraseñas → tests unitarios de registro y login.

---

## Phase 4: User Story 2 - Registro de Cumplimiento Diario (Priority: P1)

**Goal**: Permitir a usuarios marcar hábitos como cumplidos en la fecha actual o pasada, validando R4, R5 y R6.

**Independent Test**: Se prueba `marcar_habito` con fechas válidas, prevención de duplicados diarios (R4), rechazo de fechas futuras (R5) y pertenencia estricta (R6).

### Tests e Implementación para User Story 2

- [x] T018 [US2] Agregar excepciones `YaMarcadoHoyError` y `FechaFuturaError` en `app/services/errores.py`.
- [x] T019 [US2] Implementar validación de fecha no futura `_validar_fecha` (R5) en `app/services/habitos.py` → test unitario `test_R5_marcar_en_fecha_futura_es_rechazado` en `tests/test_habitos_service.py`.
- [x] T020 [US2] Implementar orquestación de `marcar_habito` en `app/services/habitos.py` aplicando la secuencia completa (R6 pertenencia → R5 fecha no futura → R4 no duplicado en fecha → persistencia) → tests unitarios `test_R4_marcar_dos_veces_el_mismo_dia_es_rechazado`, `test_R4_marcar_el_mismo_habito_en_dias_distintos_si_se_permite`, `test_R4_sin_fecha_explicita_se_usa_hoy` y `test_R6_no_se_puede_marcar_el_habito_de_otro_usuario` en `tests/test_habitos_service.py`.
- [x] T021 [US2] Implementar `listar_registros` en `app/services/habitos.py` con verificación de pertenencia R6 y paginación → test de listado ordenado cronológicamente.

---

## Phase 5: Seguridad, Routers HTTP y Exposición de API

**Purpose**: Integración HTTP FastAPI, autenticación JWT y enrutadores REST.

- [x] T022 Implementar funciones de seguridad en `app/security.py` (`pwd_context.hash`, `pwd_context.verify`, `crear_token_acceso`, `decodificar_token`).
- [x] T023 Implementar dependencias inyectables en `app/dependencies.py` (`get_db`, `get_current_user` como única fuente de `usuario_id`, `get_habitos_repo`, `get_usuarios_repo`).
- [x] T024 [P] Implementar enrutador de usuarios en `app/routers/usuarios.py` (`POST /usuarios/`, `POST /usuarios/token`).
- [x] T025 Implementar enrutador de hábitos en `app/routers/habitos.py` con diccionario `_CODIGOS` traduciendo exclusivamente `ErrorDeDominio` a códigos HTTP (201, 200, 204, 400, 403, 404, 409, 422).
- [x] T026 Implementar `app/main.py` con configuración de logging, manejador global de excepciones genéricas (`500 {"detail": "Error interno del servidor"}`), inclusión de routers y montaje de `/mcp` → tests de API en `tests/test_api_habitos.py` (9 tests con `dependency_overrides`, incluyendo validación de token ausente `401`).

---

## Phase 6: User Story 3 - Integración MCP Tools (Priority: P2)

**Goal**: Exponer herramientas MCP (`crear_habito`, `listar_habitos`, `marcar_habito`, `eliminar_habito`) que reutilizan `services/` y aplican confirmación para operaciones destructivas.

**Independent Test**: Se ejecutan pruebas sobre las tools de MCP verificando descripciones de 3 partes, resolución de identidad de usuario y manejo de confirmaciones `ctx.elicit`.

### Tests e Implementación para User Story 3

- [x] T027 [P] [US3] Implementar `app/mcp/auth.py` con `JWTTokenVerifier` sobre el mismo JWT emitido por la API REST.
- [x] T028 [P] [US3] Implementar `app/mcp/server.py` inicializando `FastMCP` con `token_verifier` y registro modular de herramientas.
- [x] T029 [US3] Implementar herramientas `crear_habito`, `listar_habitos`, `marcar_habito` en `app/mcp/tools/habitos.py` delegando directamente a `services/habitos.py` y retornando errores estructurados `{"error": "..."}`.
- [x] T030 [US3] Implementar `eliminar_habito` en `app/mcp/tools/habitos.py` incorporando confirmación del servidor con `ctx.elicit` y anotación destructiva → tests en `tests/test_mcp_habitos.py`.

---

## Phase 7: Verificación Final & Calidad

**Purpose**: Verificación de umbrales de cobertura, auditoría contra la constitución y validación end-to-end.

- [x] T031 Ejecutar suite completa con cobertura `pytest --cov=app --cov-report=term-missing` y validar que se cumplen los umbrales del Artículo VII.3: `services/` ≥ 90% y global ≥ 70%.
- [x] T032 Recorrer checklist de requisitos mínimos en `docs/checklist-requisitos.md` verificando archivo y línea de cumplimiento para cada artículo constitucional.
- [x] T033 Ejecutar validación interactiva con MCP Inspector comprobando descubrimiento de tools, caso de éxito, error de negocio, prevención de duplicados diarios y confirmación destructiva.

---

## Desviación Detectada y Corregida Durante el Diseño

Queda documentada para cumplimiento de la gobernanza constitucional:

- **Desviación**: Captura genérica `except Exception as exc: raise _a_http(exc)` en enrutadores.
- **Riesgo**: Ocultaba errores de servidor (ej. `AttributeError`) devolviéndolos al cliente como `400` con detalles internos, violando el Artículo IV.5.
- **Solución implementada**: Captura acotada a `except ErrorDeDominio as exc` en `routers/habitos.py` y función `_a_http` tipada estrictamente. Las excepciones genéricas suben al manejador global de `main.py` retornando `500 {"detail": "Error interno del servidor"}`.
