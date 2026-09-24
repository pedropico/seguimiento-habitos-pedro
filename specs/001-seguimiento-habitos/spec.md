# Feature Specification: Seguimiento de Hábitos

**Feature Directory**: `specs/001-seguimiento-habitos`

**Created**: 2026-09-23

**Status**: Ready for Planning

**Input**: User description: "Sistema personal de seguimiento de hábitos. Cada persona registra los hábitos que quiere sostener, indica cuántas veces por semana se los propone, y va marcando los días en que efectivamente los cumplió."

## Resumen y Contexto

Sistema personal de seguimiento de hábitos. Cada persona registra los hábitos que quiere sostener, indica cuántas veces por semana se los propone, y va marcando los días en que efectivamente los cumplió. Operable de forma equivalente tanto por API REST como por herramientas de MCP (Model Context Protocol).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Gestión del Ciclo de Vida de Hábitos (Priority: P1)

Como usuario registrado, quiero crear, consultar, actualizar y dar de baja mis hábitos personales con su frecuencia semanal objetivo, para poder organizar los hábitos que deseo sostener.

**Why this priority**: Es el núcleo del valor funcional; sin hábitos definidos no es posible registrar progresos ni calcular metas.

**Independent Test**: Puede probarse creando un usuario y autenticándolo, creando hábitos válidos y verificando su persistencia y listado.

**Acceptance Scenarios**:
1. **Given** un usuario autenticado, **When** solicita crear un hábito con nombre `"Leer libros"` y frecuencia objetivo `5`, **Then** el hábito se crea exitosamente (código 201) asociado exclusivamente a ese usuario.
2. **Given** un usuario autenticado con hábitos registrados, **When** solicita listar sus hábitos, **Then** recibe únicamente la lista de sus propios hábitos con soporte de paginación (`skip`, `limit`).
3. **Given** un usuario autenticado con un hábito existente, **When** actualiza el nombre o frecuencia o estado `activo` de dicho hábito, **Then** se aplican las modificaciones y se retorna el hábito actualizado.
4. **Given** un usuario autenticado con un hábito existente, **When** solicita eliminarlo, **Then** el hábito es eliminado (código 204) tras la debida validación/confirmación.

---

### User Story 2 - Registro de Cumplimiento Diario (Priority: P1)

Como usuario con hábitos activos, quiero marcar un hábito como cumplido en el día actual o en una fecha pasada específica, para mantener el historial verídico de mi constancia.

**Why this priority**: Representa la acción recurrente principal del usuario para dar seguimiento a sus hábitos.

**Independent Test**: Puede probarse marcando un hábito existente en la fecha actual y en fechas pasadas válidas, verificando el historial y la prevención de duplicados diarios.

**Acceptance Scenarios**:
1. **Given** un usuario con un hábito activo, **When** solicita marcar el hábito sin especificar fecha, **Then** se registra el cumplimiento con la fecha de hoy (código 201).
2. **Given** un usuario con un hábito ya marcado en la fecha `YYYY-MM-DD`, **When** intenta marcarlo nuevamente en la misma fecha, **Then** el sistema rechaza la operación con conflicto (código 409, `YaMarcadoHoyError`).
3. **Given** un usuario con un hábito activo, **When** intenta marcar el hábito en una fecha posterior a hoy, **Then** el sistema rechaza la operación (código 400, `FechaFuturaError`).
4. **Given** un usuario con registros previos, **When** consulta el historial de registros de un hábito, **Then** obtiene la lista cronológica paginada de marcas de cumplimiento.

---

### User Story 3 - Interacción Unificada vía MCP Tools (Priority: P2)

Como usuario o agente que interactúa vía Model Context Protocol (MCP), quiero disponer de herramientas (`crear_habito`, `listar_habitos`, `marcar_habito`, `eliminar_habito`) que apliquen exactamente las mismas reglas de negocio y seguridad que la API REST.

**Why this priority**: Permite la integración agentica natural con el mismo backend de negocio sin duplicidad de reglas.

**Independent Test**: Se invocan los tools MCP autenticados verificando que devuelven resultados estructurados y manejan errores de negocio como `{"error": "..."}` sin interrumpir la sesión.

**Acceptance Scenarios**:
1. **Given** una sesión MCP activa autenticada, **When** el cliente invoca `crear_habito` o `marcar_habito`, **Then** se ejecuta la regla en el servicio de negocio y retorna el resultado estructurado.
2. **Given** una invocación destructiva (`eliminar_habito`), **When** se solicita la ejecución, **Then** se requiere y verifica confirmación explícita antes de proceder.

---

### Edge Cases

- **Nombres con espacios sobrantes o mayúsculas**: `"  Leer   LIBROS "` y `"leer libros"` se consideran el mismo hábito para un mismo usuario (R3).
- **Mismo nombre en usuarios distintos**: Dos usuarios distintos pueden tener hábitos con el mismo nombre (ej. ambos tienen "Ejercicio").
- **Acceso cruzado a recursos (R6)**: Intentar operar sobre un hábito perteneciente a otro usuario debe retornar error de autorización (403 `HabitoAjenoError`), distinguiéndose claramente de un hábito que no existe (404 `HabitoNoEncontradoError`).
- **Límite de frecuencia semanal**: Valores de frecuencia `< 1` o `> 7` se rechazan estrictamente con código 400 (`FrecuenciaInvalidaError`).
- **Nombres cortos**: Nombres con menos de 3 caracteres útiles se rechazan con código 400 (`NombreInvalidoError`).

---

## Reglas de Negocio

Cada regla tiene un identificador que se usa en el nombre de su test (`test_R4_...`):

| ID | Regla | Excepción de dominio | Código HTTP |
|----|-------|----------------------|-------------|
| **R1** | El nombre de un hábito no puede estar vacío ni tener menos de 3 caracteres, una vez descartados los espacios sobrantes. | `NombreInvalidoError` | 400 |
| **R2** | `frecuencia_objetivo` debe ser un entero entre 1 y 7 (veces por semana). | `FrecuenciaInvalidaError` | 400 |
| **R3** | Un usuario no puede tener dos hábitos con el mismo nombre. La comparación ignora mayúsculas y espacios sobrantes: "  Leer   LIBROS " y "leer libros" son el mismo hábito. Dos usuarios distintos sí pueden tener hábitos con el mismo nombre. | `HabitoDuplicadoError` | 409 |
| **R4** | **Regla central.** Un hábito no puede marcarse como cumplido dos veces el mismo día. El mismo hábito en días distintos sí se permite, y dos hábitos distintos el mismo día también. | `YaMarcadoHoyError` | 409 |
| **R5** | No se puede marcar un hábito en una fecha futura. El día de hoy sí se permite. | `FechaFuturaError` | 400 |
| **R6** | Un usuario solo opera sobre sus propios hábitos. Cualquier operación sobre un hábito por `id` —leer, actualizar, marcar, eliminar, listar su historial— verifica la pertenencia **antes** de tocarlo, sin importar qué identificador se pase en la solicitud. | `HabitoAjenoError` / `HabitoNoEncontradoError` | 403 / 404 |

---

## Contrato de la API (REST)

| Método | Ruta | Auth | Request | Éxito | Errores esperados |
|--------|------|------|---------|-------|-------------------|
| POST | `/usuarios/` | No | email, password | 201 Usuario | 400 email duplicado, 422 |
| POST | `/usuarios/token` | No | username, password (form) | 200 token JWT | 401 credenciales inválidas |
| POST | `/habitos/` | Sí | nombre, frecuencia_objetivo | 201 Habito | 400 (R1, R2), 409 (R3), 401, 422 |
| GET | `/habitos/` | Sí | query: skip, limit | 200 lista | 401, 422 |
| GET | `/habitos/{id}` | Sí | — | 200 Habito | 401, 403 (R6), 404 |
| PATCH | `/habitos/{id}` | Sí | nombre?, frecuencia_objetivo?, activo? | 200 Habito | 400 (R1, R2), 409 (R3), 401, 403, 404, 422 |
| DELETE | `/habitos/{id}` | Sí | — | 204 | 401, 403 (R6), 404 |
| POST | `/habitos/{id}/marcar` | Sí | fecha? (por defecto hoy) | 201 Registro | 400 (R5), 409 (R4), 401, 403, 404 |
| GET | `/habitos/{id}/registros` | Sí | query: skip, limit | 200 lista | 401, 403, 404, 422 |

*Nota:* `usuario_id` **no aparece en ningún request**: sale siempre del JWT.

---

## Contrato Equivalente por MCP

- **`crear_habito(nombre, frecuencia_objetivo)`** — Mismas reglas que `POST /habitos/`, operando sobre el usuario autenticado de la sesión MCP.
- **`listar_habitos(skip, limit)`** — Mismo comportamiento que `GET /habitos/`.
- **`marcar_habito(habito_id, fecha)`** — Mismas reglas que `POST /habitos/{id}/marcar`, incluida R4 y R5.
- **`eliminar_habito(habito_id)`** — Exige confirmación gestionada por el servidor antes de ejecutar, y verifica que el hábito pertenece al usuario.

---

## Casos de Error Explícitos que Deben Tener Test

1. Crear un hábito con nombre vacío o de menos de 3 caracteres (R1).
2. Crear un hábito con frecuencia fuera del rango 1–7 (R2).
3. Crear un hábito con un nombre que el usuario ya tiene (R3).
4. Marcar el mismo hábito dos veces el mismo día (R4).
5. Marcar un hábito en una fecha futura (R5).
6. Operar sobre el hábito de otro usuario pasando su ID manualmente (R6) → 403.
7. Operar sobre un hábito inexistente (R6) → 404.
8. Listar o crear hábitos sin token → 401.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE permitir registrar nuevos usuarios con email único y contraseña segura hasheada.
- **FR-002**: El sistema DEBE autenticar usuarios mediante credenciales válidas y emitir tokens de acceso JWT.
- **FR-003**: El sistema DEBE extraer la identidad del usuario (`usuario_id`) exclusivamente del token de autenticación.
- **FR-004**: El sistema DEBE validar que el nombre de un hábito tenga al menos 3 caracteres útiles sin contar espacios redundantes (R1).
- **FR-005**: El sistema DEBE validar que la frecuencia objetivo semanal se encuentre entre 1 y 7 inclusive (R2).
- **FR-006**: El sistema DEBE impedir que un mismo usuario registre hábitos con nombres duplicados normalizados (R3).
- **FR-007**: El sistema DEBE registrar el cumplimiento diario de un hábito y prevenir registros duplicados en una misma fecha (R4).
- **FR-008**: El sistema DEBE rechazar registros de cumplimiento con fechas futuras (R5).
- **FR-009**: El sistema DEBE validar la titularidad de los hábitos antes de permitir lectura, modificación, marcado o eliminación (R6).
- **FR-010**: El sistema DEBE proveer endpoints paginados con `skip` y `limit` para listados de hábitos y registros.
- **FR-011**: El sistema DEBE exponer herramientas MCP equivalentes (`crear_habito`, `listar_habitos`, `marcar_habito`, `eliminar_habito`) que reutilicen la lógica central.
- **FR-012**: El sistema DEBE solicitar confirmación del servidor para acciones destructivas en MCP (`eliminar_habito`).

### Key Entities

- **Usuario**: Representa una cuenta de usuario con credenciales (email único y contraseña segura hasheada).
- **Habito**: Representa un hábito individual con nombre, frecuencia objetivo semanal (1-7), estado activo y vinculación a un usuario propietario.
- **RegistroHabito**: Representa la constancia de cumplimiento de un hábito en una fecha determinada.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% de las 6 reglas de negocio explícitas (R1–R6) verificadas con tests unitarios automatizados que llevan el identificador `test_R[N]_...`.
- **SC-002**: Cobertura de tests en la capa de servicios ≥ 90% y cobertura global de la aplicación ≥ 70%.
- **SC-003**: Todas las operaciones de API REST y tools MCP operan con aislamiento total entre usuarios (cero fuga de datos entre cuentas).
- **SC-004**: Las operaciones de creación, consulta y marcado responden consistentemente según las convenciones de códigos de estado HTTP (200, 201, 204, 400, 401, 403, 404, 409, 422).

---

## Assumptions

- Se asume uso de huso horario estándar para la evaluación de la fecha de "hoy" en caso de no especificarse zona horaria.
- Las solicitudes sin fecha explícita en el marcado de hábito asumen la fecha del día en curso.
- La normalización de nombres descarta espacios iniciales, finales y repetidos consecutivos y es insensible a mayúsculas/minúsculas.

---

## Clarificaciones Resueltas

1. **¿Marcar hoy cuenta como fecha futura?**: No. R5 rechaza estrictamente fechas posteriores a hoy; el día de hoy es el caso estándar.
2. **¿Dos usuarios distintos pueden tener un hábito con el mismo nombre?**: Sí. R3 es única por `(usuario, nombre normalizado)`, no global.
3. **¿"Leer" y "leer  " son el mismo hábito?**: Sí. La comparación de R3 usa el nombre normalizado, aunque se conserva el nombre formateado para visualización.

---

## Fuera de Alcance

- Interfaz visual de frontend (el sistema se opera y verifica vía OpenAPI `/docs` y MCP Inspector).
- Rachas, estadísticas acumulativas, gamificación o recordatorios automáticos (reservados para futuras especificaciones).
- Gestión de roles de administración o permisos multi-nivel (todos los usuarios son estándar y aislados).
