# Checklist de Requisitos Constitucionales y Trazabilidad

Cada artículo de la constitución es **verificable**: a continuación se señala el archivo y las líneas exactas donde se cumple en el código fuente implementado.

| Artículo | Regla / Principio | Archivo | Líneas / Símbolos |
|---|---|---|---|
| **Artículo I.1** | Routers solo traducen HTTP y no validan reglas de negocio. | `app/routers/habitos.py` | `_a_http`, endpoints delegando a `habitos_service` |
| **Artículo I.2** | Services contienen toda la lógica y no importan SQLAlchemy/Session. | `app/services/habitos.py` | 0 imports de sqlalchemy (`grep` limpio) |
| **Artículo I.3** | Repositories devuelven diccionarios planos `dict`, nunca modelos ORM. | `app/repositories/habitos.py` | `_habito_a_dict`, `_registro_a_dict` |
| **Artículo I.4** | Utils son funciones puras sin dependencias circulares. | `app/utils/texto.py`, `app/utils/fechas.py` | `normalizar_nombre`, `es_fecha_futura` |
| **Artículo I.5 / VI.1** | MCP tools reutilizan la lógica de `services/`. | `app/mcp/tools/habitos.py` | `crear_habito`, `marcar_habito` delegando a `habitos_service` |
| **Artículo II.1** | SRP: validaciones atómicas separadas de orquestación. | `app/services/habitos.py` | `_validar_nombre`, `_validar_frecuencia`, `_habito_propio` |
| **Artículo II.2** | OCP: constantes modificables sin alterar la lógica de control. | `app/services/habitos.py` | `NOMBRE_MIN_LONGITUD`, `FRECUENCIA_MINIMA`, `FRECUENCIA_MAXIMA` |
| **Artículo II.3** | DIP: repositorios inyectados por parámetro por defecto. | `app/services/habitos.py` | Firmas con `repo=habitos_repository` |
| **Artículo III.1** | SQLAlchemy 2.0 + Alembic sin SQL crudo concatenado. | `app/models/`, `alembic/` | `Mapped`, `mapped_column`, migraciones generadas |
| **Artículo III.2** | SQLite en dev con `connect_args` condicional. | `app/database.py` | `connect_args={"check_same_thread": False}` si SQLite |
| **Artículo III.3** | Filtrado obligatorio por `usuario_id` en consultas de listado. | `app/repositories/habitos.py` | `listar()` con `where(Habito.usuario_id == usuario_id)` |
| **Artículo IV.1** | Contraseñas hasheadas con bcrypt (`bcrypt<4.1`). | `app/security.py` | `CryptContext(schemes=["bcrypt"])` |
| **Artículo IV.2** | Autenticación JWT con algoritmo HS256 y expiración. | `app/security.py` | `crear_token_acceso`, `decodificar_token` |
| **Artículo IV.3** | Secretos y configuración leídos exclusivamente de `.env`. | `app/config.py` | `Settings` con `pydantic-settings` |
| **Artículo IV.4** | Autorización estricta: `usuario_id` sale únicamente del JWT verificado. | `app/dependencies.py` | `get_current_user` |
| **Artículo IV.5** | Errores no controlados retornan 500 con detalle genérico y log interno. | `app/main.py` | `@app.exception_handler(Exception)` |
| **Artículo V.1** | Convención de códigos REST y mapeo centralizado `_CODIGOS`. | `app/routers/habitos.py` | Diccionario `_CODIGOS` traduciendo solo `ErrorDeDominio` |
| **Artículo VI.2** | Descripciones de MCP tools con 3 partes (qué hace / cuándo / cuándo no). | `app/mcp/tools/habitos.py` | Docstrings y descriptions de cada tool |
| **Artículo VI.4** | Resolución de identidad JWT en MCP con usuario demo documentado en stdio. | `app/mcp/tools/habitos.py` | `_resolver_usuario_id` |
| **Artículo VI.5** | Acción destructiva (`eliminar_habito`) con confirmación explícita. | `app/mcp/tools/habitos.py` | `eliminar_habito` con `ctx.elicit` y flag de confirmación |
| **Artículo VII.2** | Tests unitarios con repositorios falsos sin `unittest.mock`. | `tests/fakes.py`, `tests/test_habitos_service.py` | `RepositorioFalsoHabitos` |
| **Artículo VII.3** | Cobertura ≥90% en services y ≥70% global con `pytest-cov`. | `pyproject.toml` | `[tool.coverage.run] omit` |
