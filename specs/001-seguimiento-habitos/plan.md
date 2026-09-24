# Implementation Plan: Seguimiento de Hábitos

**Feature Directory**: `specs/001-seguimiento-habitos` | **Date**: 2026-09-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-seguimiento-habitos/spec.md`

---

## Summary

Implementación de un sistema backend personal de seguimiento de hábitos con arquitectura en capas estricta en FastAPI, persistencia SQLAlchemy 2.0 + Alembic, autenticación OAuth2 + JWT (pyjwt), hashing seguro con passlib/bcrypt (`bcrypt<4.1`), interfaz dual REST y herramientas MCP (Model Context Protocol) vía streamable-http, y una suite completa de pruebas unitarias (con repositorios falsos sin mocks), integración y API.

---

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, uvicorn[standard], SQLAlchemy 2.0, Alembic, pyjwt, passlib[bcrypt] con `bcrypt<4.1`, pydantic-settings, python-multipart, email-validator, mcp SDK (oficial).
**Storage**: SQLite en desarrollo (`check_same_thread: False`), compatible directamente con PostgreSQL en producción.
**Testing**: pytest, pytest-cov, pytest-asyncio, httpx.
**Target Platform**: Linux / Windows / Docker (ASGI web service + MCP endpoint).
**Project Type**: Web service REST API + MCP Server.
**Performance Goals**: < 100ms de latencia en operaciones de negocio estándar.
**Constraints**: Zero-mock en tests unitarios de servicios (inyección de dependencias pura con fakes), 100% de cobertura en reglas explícitas R1-R6, ≥ 90% cobertura de líneas en `services/`, ≥ 70% cobertura global.
**Scale/Scope**: 3 entidades principales (`Usuario`, `Habito`, `RegistroHabito`), 9 endpoints REST, 4 MCP tools.

---

## Constitution Check

| Artículo | Principio | Estado de Cumplimiento en el Diseño |
|---|---|:---:|
| **I. Arquitectura en capas** | Separación estricta: `routers/` solo traducen HTTP; `services/` contienen toda la lógica y no importan SQLAlchemy/Session; `repositories/` son la única capa que accede a BD y devuelven `dict`; `utils/` son funciones puras; `mcp/tools/` llaman a `services/`. | ✅ PASA |
| **II. SOLID aplicado** | SRP en validación vs orquestación; OCP mediante constantes configurables; DIP mediante inyección de repositorios por parámetro por defecto (`repo=habitos_repository`); no se añade complejidad artificial. | ✅ PASA |
| **III. Persistencia** | SQLAlchemy 2.0 con `Mapped`/`mapped_column` y Alembic; soporte dual SQLite/Postgres en `database.py`; filtro obligatorio por `usuario_id` en todas las consultas de hábitos. | ✅ PASA |
| **IV. Seguridad** | Passwords con bcrypt (`bcrypt<4.1`); JWT con HS256 y expiración; credenciales solo en `.env`; autorización estricta donde `usuario_id` sale únicamente del JWT verificado; excepciones no controladas capturadas globalmente como 500 genérico. | ✅ PASA |
| **V. Diseño REST** | Verbos y códigos HTTP estándar (201, 200, 204, 400, 401, 403, 404, 409, 422); traducción centralizada en diccionario `_CODIGOS`; paginación con `skip` y `limit`; schemas Pydantic diferenciados (`HabitoCreate`, `HabitoOut`). | ✅ PASA |
| **VI. MCP: tools y reutilización** | Tools reutilizan `services/`; descripciones accionables; errores de negocio retornan `{"error": "..."}`; transporte `streamable-http` propaga JWT; `eliminar_habito` requiere confirmación del servidor vía `ctx.elicit`. | ✅ PASA |
| **VII. Testing y cobertura** | Repositorios falsos (`fakes.py`) sin `unittest.mock`; 100% cobertura de reglas R1-R6 con nombres `test_R[N]_...`; ≥ 90% en `services/`; ≥ 70% global en `pytest-cov`; fixtures con `StaticPool` en memoria; overrides de FastAPI para API. | ✅ PASA |

---

## Trazabilidad Plan → Constitución

- **Artículo I (capas)** se implementa como paquetes Python separados bajo `app/`, sin imports cruzados que violen la dirección de dependencia. `services/` recibe `db` pero lo trata como identificador opaco — no importa `Session` ni ningún símbolo de SQLAlchemy (`grep -r "sqlalchemy" app/services/` no devuelve nada).
- **Artículo II.3 (DIP)** se implementa con parámetros por defecto en las funciones de `services/` (`def crear_habito(..., repo=habitos_repository)`). En la capa HTTP, `Depends(get_habitos_repo)` permite a los tests de API sustituir el repositorio.
- **Artículo III (persistencia)**: SQLAlchemy 2.0 con `Mapped`/`mapped_column`. Las reglas R3 y R4 se respaldan además con `UniqueConstraint` en las tablas como red de seguridad. `connect_args` se aplica solo cuando la URL es SQLite.
- **Artículo IV (seguridad)**: `pyjwt` como única biblioteca JWT. `passlib.CryptContext` con `bcrypt<4.1`. `pydantic-settings` para `.env`. Toda ruta depende de `get_current_user` y la pertenencia se verifica en `services/habitos.py::_habito_propio`.
- **Artículo V (REST)**: Diccionario `_CODIGOS` en `routers/habitos.py` capturando solo `ErrorDeDominio`. Manejador global en `main.py` para errores 500.
- **Artículo VI (MCP)**: Montado en FastAPI (`app.mount("/mcp", ...)`), compartiendo el JWT vía `JWTTokenVerifier` y registro desacoplado `register(mcp)`.
- **Artículo VII (testing)**: Fixtures de pytest para SQLite en memoria con `StaticPool`, `app.dependency_overrides` y `pytest-cov` con umbrales configurados en `pyproject.toml`.

---

## Orden de Implementación

```
utils → models → repositories → services → routers → mcp/tools
```

`config.py`, `database.py` y `security.py` son transversales y se construyen antes que `repositories/`.

---

## Arquitectura de una Operación

```text
POST /habitos/{id}/marcar          tool marcar_habito
            ↓                              ↓
   routers/habitos.py              mcp/tools/habitos.py
            └──────────────┬───────────────┘
                           ↓
            services/habitos.py::marcar_habito     ← R4, R5, R6 viven aquí
                           ↓
           repositories/habitos.py::guardar_registro
                           ↓
                models/habito.py::RegistroHabito
```

---

## Estructura del Proyecto

### Documentación de la Feature

```text
specs/001-seguimiento-habitos/
├── spec.md              # Especificación funcional
├── plan.md              # Este plan de implementación
├── research.md          # Investigación técnica y decisiones de arquitectura
├── data-model.md        # Modelo de datos, relaciones y contratos de repo
├── quickstart.md        # Guía de validación y comandos
├── contracts/           # Contratos REST y MCP
│   ├── rest-api.md
│   └── mcp-tools.md
├── checklists/
│   └── requirements.md  # Checklist de validación de requisitos
└── tasks.md             # Tareas ejecutables (generado por /speckit-tasks)
```

### Código Fuente

```text
app/
├── __init__.py
├── main.py                     # Instancia FastAPI, middleware de errores, montaje /mcp
├── config.py                   # Pydantic Settings (.env)
├── database.py                 # Engine SQLAlchemy, SessionLocal, connect_args SQLite
├── security.py                 # passlib bcrypt, pyjwt create/decode token
├── dependencies.py             # get_db, get_current_user, repos inyectables
├── models/
│   ├── __init__.py
│   ├── usuario.py              # Modelo SQLAlchemy Usuario
│   └── habito.py               # Modelos SQLAlchemy Habito y RegistroHabito
├── schemas/
│   ├── __init__.py
│   ├── usuario.py              # UsuarioCreate, UsuarioOut, Token
│   └── habito.py               # HabitoCreate, HabitoUpdate, HabitoOut, RegistroOut
├── repositories/
│   ├── __init__.py
│   ├── usuarios.py             # CRUD de usuarios (retorna dicts)
│   └── habitos.py              # CRUD de hábitos y registros (retorna dicts)
├── services/
│   ├── __init__.py
│   ├── excepciones.py          # Excepciones de dominio (R1-R6)
│   ├── usuarios.py             # Lógica de registro y autenticación
│   └── habitos.py              # Lógica central R1-R6, orquestación, verificación R6
├── routers/
│   ├── __init__.py
│   ├── usuarios.py             # Endpoints /usuarios/ y /usuarios/token
│   └── habitos.py              # Endpoints /habitos/, mapeo _CODIGOS
├── utils/
│   ├── __init__.py
│   └── texto.py                # Funciones puras de normalización de cadenas
└── mcp/
    ├── __init__.py
    ├── server.py               # Configuración servidor MCP y autenticación JWT
    └── tools/
        ├── __init__.py
        └── habitos.py          # Tools MCP delegando a services/

tests/
├── conftest.py                 # Fixtures de BD SQLite StaticPool, cliente API
├── fakes.py                    # Repositorios falsos en memoria para unit tests
├── test_habitos_service.py     # Tests unitarios de reglas R1-R6 (sin mocks)
├── test_integracion_habitos.py # Tests de persistencia real SQLAlchemy
├── test_api_habitos.py         # Tests de endpoints HTTP con TestClient
└── test_mcp_habitos.py         # Tests de tools MCP
```

---

## Corrección Validada de `/speckit-analyze`

En la operación `marcar_habito`:
1. Recibir `habito_id`, `fecha` y `usuario_id` (del JWT).
2. Verificar que el hábito existe y pertenece al usuario autenticado (R6) → `_habito_propio()`.
3. Validar que la fecha no sea futura (R5) → `_validar_fecha()`.
4. Verificar que no exista ya un registro para ese día en ese hábito (R4) → `_validar_no_marcado_hoy()`.
5. Guardar el registro a través del repositorio (`repo.guardar_registro`).
