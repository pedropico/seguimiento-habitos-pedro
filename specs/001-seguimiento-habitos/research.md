# Research & Technical Decisions: Seguimiento de Hábitos

**Feature**: `specs/001-seguimiento-habitos`
**Date**: 2026-09-23
**Status**: Completed

---

## 1. Framework Web y Servidor ASGI

- **Decisión**: FastAPI con `uvicorn[standard]`.
- **Razón**: Proporciona validación automática de esquemas con Pydantic v2, generación interactiva de OpenAPI (`/docs`), soporte nativo para `Depends` (DIP) y compatibilidad para montar rutas ASGI auxiliares como el endpoint de MCP.
- **Alternativas consideradas**:
  - *Flask*: Descartado por requerir extensiones separadas para validación, OpenAPI y tipado moderno.
  - *Django*: Descartado por ser excesivamente pesado y desacoplado de las directrices de capas de la constitución.

---

## 2. ORM y Persistencia

- **Decisión**: SQLAlchemy 2.0 (`Mapped`, `mapped_column`, `select`) + Alembic para migraciones.
- **Razón**: Cumple el Artículo III. Permite separar totalmente el modelo ORM en `models/` y las consultas en `repositories/`, devolviendo diccionarios planos (`dict`) para evitar fugas de objetos ORM hacia `services/`.
- **Compatibilidad SQLite/Postgres**: `database.py` usa `connect_args={"check_same_thread": False}` condicionado únicamente a URLs que comiencen con `sqlite`, permitiendo conectar Postgres en producción sin modificar servicios ni enrutadores.
- **Alternativas consideradas**:
  - *SQL crudo*: Prohibido explícitamente por el Artículo III.1.
  - *Tortoise ORM / Peewee*: Menos maduros que SQLAlchemy 2.0 en el ecosistema Python.

---

## 3. Autenticación y Seguridad Criptográfica

- **Decisión**: `passlib[bcrypt]` con versión fijada `bcrypt<4.1` + `pyjwt` (HS256) + `OAuth2PasswordBearer`.
- **Razón**: Cumple el Artículo IV. `passlib 1.7.4` presenta incompatibilidad de runtime con `bcrypt >= 4.1.0`. `pyjwt` se elige de forma única y canónica evitando la biblioteca en desuso `python-jose`.
- **Configuración segura**: Variables críticas (`SECRET_KEY`, `DATABASE_URL`) cargadas vía `pydantic-settings` desde `.env`.
- **Alternativas consideradas**:
  - *python-jose*: Descartado por falta de mantenimiento activo y vulnerabilidades conocidas.
  - *Argon2*: Descartado en favor del estándar `bcrypt` indicado en la constitución.

---

## 4. Arquitectura de Inyección de Dependencias (DIP)

- **Decisión**: Inyección por parámetros por defecto en funciones de `services/` (ej. `def crear_habito(..., repo=habitos_repository)`).
- **Razón**: Cumple el Artículo II.3. Permite sustituir repositorios reales por repositorios falsos en memoria en pruebas unitarias sin requerir `unittest.mock`.
- **Alternativas consideradas**:
  - *Contenedores IoC pesados (dependency_injector)*: Descartados para evitar complejidad accidental y sobreingeniería.

---

## 5. Integración con Model Context Protocol (MCP)

- **Decisión**: SDK oficial `mcp` con transporte `streamable-http` montado en FastAPI (`/mcp`) y soporte fallback para `stdio`.
- **Razón**: Cumple el Artículo VI. Reutiliza el mismo JWT verificado (`JWTTokenVerifier`) en transporte HTTP y documenta explícitamente el usuario demo en `stdio`. Las tools se registran mediante `register(mcp)` evitando ciclos de importación. Confirmación del servidor para `eliminar_habito` vía `ctx.elicit`.
- **Alternativas consideradas**:
  - *Servidor MCP en proceso separado*: Descartado para mantener una sola aplicación desplegable y reutilizar la misma base de datos y configuración.

---

## 6. Estrategia de Pruebas y Cobertura

- **Decisión**: `pytest` + `pytest-cov` + `pytest-asyncio` + `httpx`.
- **Razón**: Cumple el Artículo VII.
  - *Unitarios*: Utilizan `tests/fakes.py` (repositorio falso en memoria) sin mocks.
  - *Integración*: Base SQLite en memoria con `StaticPool`.
  - *API*: `TestClient` con `app.dependency_overrides` y `scope="module"`.
  - *Umbrales*: Reglas R1-R6 cubiertas al 100%, `services/` ≥ 90%, global ≥ 70%.
