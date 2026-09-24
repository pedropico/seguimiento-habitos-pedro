<!--
Sync Impact Report:
- Version change: template -> 1.0.0
- Added sections:
  - Core Principles:
    - Artículo I — Arquitectura en capas
    - Artículo II — SOLID aplicado (no teórico)
    - Artículo III — Persistencia
    - Artículo IV — Seguridad (no negociable)
    - Artículo V — Diseño de endpoints REST
    - Artículo VI — MCP: tools y reutilización
    - Artículo VII — Testing y cobertura
  - Gobernanza
- Removed sections: None (placeholder template populated)
- Follow-up TODOs: None
-->

# Constitución — Proyecto Seguimiento de Hábitos

> Generada con `/speckit-constitution`. Tiene prioridad sobre cualquier decisión
> tomada durante `/speckit-implement`. Cada artículo es **verificable**: para
> cada uno se puede señalar el archivo y la línea donde se cumple.

## Core Principles

### Artículo I — Arquitectura en capas

1. `routers/` reciben la solicitud HTTP, delegan al service correspondiente y
   traducen su resultado (o excepción) a una respuesta HTTP. Un router NUNCA
   valida reglas de negocio — esa lógica vive en `services/`.
2. `services/` contienen toda la lógica de negocio. Un service NUNCA importa
   SQLAlchemy, `Session`, ni ningún detalle de persistencia directamente. El
   parámetro `db` viaja como un identificador opaco que el service solo devuelve
   al repositorio que recibió.
3. `repositories/` son la única capa autorizada a leer o escribir en la base de
   datos. Un repository no contiene reglas de negocio, solo operaciones de
   persistencia (guardar, listar, buscar, eliminar), y devuelve `dict`, nunca
   objetos ORM.
4. `utils/` son funciones puras (mismo input → mismo output, sin efectos
   secundarios), sin importar nada de `services/`, `routers/` ni `repositories/`.
5. `mcp/tools/` NUNCA reimplementan lógica de `services/`. Si una tool de MCP y
   un router necesitan la misma regla, ambos llaman al mismo service.

**Dónde se cumple:** `app/routers/habitos.py` (solo traduce, ver `_a_http`),
`app/services/habitos.py` (sin un solo `import sqlalchemy`),
`app/repositories/habitos.py` (`_habito_a_dict`), `app/utils/texto.py`,
`app/mcp/tools/habitos.py`.

### Artículo II — SOLID aplicado (no teórico)

1. **SRP**: cada función de `services/` hace una sola cosa. La validación
   (`_validar_nombre`, `_validar_frecuencia`, `_habito_propio`) está separada de
   la orquestación (`crear_habito`, `marcar_habito`).
2. **OCP**: cambiar el rango de frecuencia permitido o la longitud mínima del
   nombre se hace tocando una constante (`FRECUENCIA_MINIMA`,
   `FRECUENCIA_MAXIMA`, `NOMBRE_MIN_LONGITUD`), nunca reescribiendo un `if` ya
   existente.
3. **DIP**: todo service que necesite un repository lo recibe como parámetro con
   un valor por defecto (`def crear_habito(..., repo=habitos_repository)`), nunca
   lo importa fijo dentro del cuerpo de la función. Esto es innegociable: es lo
   que permite testear sin `unittest.mock`.
4. No se fuerzan LSP ni ISP: este proyecto no tiene jerarquías de clases ni
   interfaces formales, y añadirlas solo para cumplir un principio sería
   complejidad artificial.

**Dónde se cumple:** `app/services/habitos.py`, líneas de `_validar_*` y las
firmas con `repo=habitos_repository`.

### Artículo III — Persistencia

1. SQLAlchemy como ORM, Alembic para migraciones. Ninguna sentencia SQL cruda
   concatenada con strings.
2. SQLite en desarrollo; `app/database.py` debe funcionar contra Postgres sin
   tocar `services/` ni `routers/` (`connect_args` condicional solo para SQLite).
3. Cada modelo con datos de usuario incluye `usuario_id` como FK. **Ninguna
   consulta de hábitos puede omitir el filtro por `usuario_id`.** El acceso por
   `id` (`repositories.obtener`) es la única excepción, y existe precisamente
   para que `services/` pueda verificar la pertenencia y distinguir 404 de 403.

**Dónde se cumple:** `app/database.py` (`connect_args` condicional),
`app/models/habito.py` (FK `usuario_id`), `app/repositories/habitos.py::listar`.

### Artículo IV — Seguridad (no negociable)

1. Contraseñas: hash con `passlib[bcrypt]`. Nunca se guarda ni se loguea una
   contraseña en texto plano, y `hashed_password` nunca aparece en un schema de
   salida.
2. Autenticación: OAuth2 password flow + JWT firmado con HS256.
   `ACCESS_TOKEN_EXPIRE_MINUTES` configurable, nunca infinito.
3. `SECRET_KEY` y `DATABASE_URL` viven solo en `.env` (nunca versionado).
   `.env.example` documenta las variables necesarias sin valores reales.
   `SECRET_KEY` se genera con un generador criptográficamente seguro, nunca se
   escribe a mano.
4. **Autorización**: el `usuario_id` para filtrar, crear o modificar un hábito
   SIEMPRE sale del token JWT decodificado (`get_current_user`), NUNCA de un
   parámetro de la URL, del body ni de un query param. Esto aplica también a
   recursos ya existentes: cualquier operación sobre un hábito por `id` (leer,
   actualizar, marcar, eliminar) primero verifica que ese hábito pertenece al
   usuario autenticado, antes de tocarlo.
5. Un error no controlado (`Exception` genérica) devuelve `500` con
   `{"detail": "Error interno del servidor"}` — nunca un stack trace ni el
   mensaje de la excepción original al cliente. El detalle sí se loguea
   internamente.
6. Toda entrada de usuario se valida con schemas Pydantic antes de llegar a
   `services/`.

**Dónde se cumple:** `app/security.py`, `app/dependencies.py::get_current_user`,
`app/services/habitos.py::_habito_propio`, `app/main.py::error_no_controlado`,
`app/schemas/habito.py` (`HabitoCreate` no acepta `usuario_id`).

### Artículo V — Diseño de endpoints REST

1. Convención de verbos y códigos: `POST` crea (`201`), `GET` lista/lee (`200`),
   `PATCH` actualiza (`200`), `DELETE` elimina (`204`). Fallo de autenticación
   (`401`), recurso ajeno identificado por `id` en la ruta (`403`), recurso
   inexistente (`404`), error de validación de schema (`422`), error de regla de
   negocio conocido (`400`), **conflicto con el estado actual del recurso
   (`409`)** — este último es el que corresponde a "el hábito ya fue marcado hoy"
   y a "ya tienes un hábito con ese nombre". Un listado (`GET /habitos/`) NUNCA
   devuelve `403`: filtra por el `usuario_id` del JWT.
2. Toda lista paginada expone `skip` y `limit` como query params con valores por
   defecto razonables; valores inválidos son error de schema (`422`).
3. Los schemas de entrada y salida son distintos (`HabitoCreate` vs `HabitoOut`)
   — nunca se expone el modelo de SQLAlchemy directamente.

**Dónde se cumple:** `app/routers/habitos.py` (diccionario `_CODIGOS`),
`app/schemas/habito.py`.

### Artículo VI — MCP: tools y reutilización

1. Cada tool de MCP llama a una función de `services/`, punto. Ejemplo:
   `crear_habito` (tool) y `POST /habitos/` (router) llaman a la misma función
   `services/habitos.py::crear_habito()`. Si una tool necesita lógica que no
   existe en `services/`, esa lógica se agrega en `services/` primero.
2. La descripción de cada tool es específica y accionable: dice **qué hace**,
   **cuándo usarla** y **cuándo no usarla**. Nunca genérica ("maneja hábitos").
3. Errores de negocio se devuelven como una estructura clara
   (`{"error": "..."}`), nunca como una excepción sin controlar que rompa la
   sesión del cliente MCP.
4. Si el transporte es `stdio` y no hay forma de propagar identidad real de
   usuario, se documenta explícitamente en el código como simplificación
   consciente, nunca como un olvido silencioso. Si el transporte es
   `streamable-http` y hay un token verificado, la tool **debe** usar la
   identidad de ese token; el usuario demo es solo el respaldo legítimo cuando no
   hay ningún token disponible.
5. Cualquier tool con efecto destructivo (`eliminar_habito`) debe pedir
   confirmación explícita gestionada por el servidor, nunca depender de que el
   modelo decida preguntar por su cuenta.

**Dónde se cumple:** `app/mcp/tools/habitos.py` — `_resolver_usuario_id` (VI.4,
con el comentario de la simplificación), `ctx.elicit` en `eliminar_habito`
(VI.5), los docstrings de los cuatro tools (VI.2).

### Artículo VII — Testing y cobertura

1. Pirámide de pruebas obligatoria: unitarias (mayoría) → integración → API/E2E
   (minoría).
2. Los tests unitarios de `services/` inyectan un repositorio falso (que cumple
   el mismo contrato que el real) como parámetro. Está **PROHIBIDO** usar
   `unittest.mock` para esto, porque el diseño con DIP ya lo hace innecesario.
3. Cobertura mínima exigida:
   - 100% de las reglas de negocio explícitas de `spec.md` cubiertas por al
     menos un test unitario cada una — cobertura de *reglas*, no solo de líneas.
     Cada test lleva el identificador de su regla en el nombre (`test_R4_...`).
   - Cobertura de líneas de `services/` ≥ **90%**.
   - Cobertura global ≥ **70%**, medida con
     `pytest --cov=app --cov-report=term-missing`. Este umbral no exige cubrir el
     arranque de la app (`main.py`), el servidor MCP en sí (`mcp/server.py`,
     `mcp/auth.py`), `database.py` ni `logging_config.py`: son infraestructura de
     arranque, y su exclusión se declara en `[tool.coverage.run] omit` de
     `pyproject.toml`, nunca como una omisión silenciosa.
4. Tests de integración corren contra una base de datos real (SQLite en memoria
   como mínimo), nunca contra el repositorio falso.
5. Tests de API usan `app.dependency_overrides` de FastAPI para sustituir
   `get_db`, `get_habitos_repo` y `get_current_user` — nunca levantan un servidor
   real ni golpean la base de datos de desarrollo.
6. Toda tool de MCP tiene al menos un caso exitoso y un caso de error de negocio
   verificados.
7. Ninguna tarea de `tasks.md` se considera terminada sin su test
   correspondiente en verde.

**Dónde se cumple:** `tests/fakes.py`, `tests/test_habitos_service.py`,
`tests/test_integracion_habitos.py`, `tests/test_api_habitos.py`,
`tests/test_mcp_habitos.py`, `pyproject.toml`.

## Gobernanza

Esta constitución tiene prioridad sobre cualquier decisión tomada durante
`/speckit-implement`. **Si el agente necesita desviarse de un artículo, debe
señalarlo explícitamente y esperar aprobación antes de continuar, no decidir en
silencio.** Una desviación aceptada se documenta en el código con un comentario
que nombre el artículo afectado (ver `_resolver_usuario_id`, Artículo VI.4).

**Version**: 1.0.0 | **Ratified**: 2026-09-23 | **Last Amended**: 2026-09-23
