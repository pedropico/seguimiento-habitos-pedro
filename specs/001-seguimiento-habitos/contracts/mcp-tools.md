# Contract: MCP Tools — Seguimiento de Hábitos

**Protocolo**: Model Context Protocol (MCP)
**Transportes**: `streamable-http` (vía `/mcp` con token JWT) y `stdio` (con fallback documentado a usuario demo).
**Manejo de Errores**: Todo error de negocio se devuelve como `{"error": "<mensaje>"}` sin excepciones que rompan la sesión.

---

## 1. `crear_habito`

- **Descripción**: Crea un nuevo hábito para el usuario autenticado indicando su nombre y frecuencia semanal objetivo.
- **Parámetros**:
  - `nombre` (`string`): Nombre del hábito (mínimo 3 caracteres limpios).
  - `frecuencia_objetivo` (`integer`): Frecuencia semanal deseada (1 a 7).
- **Retorno exitoso**:
  ```json
  {
    "id": 1,
    "nombre": "Leer libros",
    "frecuencia_objetivo": 5,
    "activo": true,
    "fecha_creacion": "2026-09-23T12:00:00"
  }
  ```
- **Retorno de error de negocio**:
  ```json
  {"error": "El nombre del hábito debe tener al menos 3 caracteres"}
  ```

---

## 2. `listar_habitos`

- **Descripción**: Lista los hábitos pertenecientes al usuario autenticado con soporte de paginación.
- **Parámetros**:
  - `skip` (`integer`, opcional, default 0): Número de registros a omitir.
  - `limit` (`integer`, opcional, default 20): Cantidad máxima de hábitos a retornar.
- **Retorno exitoso**:
  ```json
  [
    {
      "id": 1,
      "nombre": "Leer libros",
      "frecuencia_objetivo": 5,
      "activo": true
    }
  ]
  ```

---

## 3. `marcar_habito`

- **Descripción**: Marca un hábito como cumplido en una fecha concreta (o hoy si se omite).
- **Parámetros**:
  - `habito_id` (`integer`): Identificador del hábito.
  - `fecha` (`string`, opcional): Fecha en formato `YYYY-MM-DD`. Por defecto la fecha actual.
- **Retorno exitoso**:
  ```json
  {
    "id": 1,
    "habito_id": 1,
    "fecha": "2026-09-23",
    "fecha_registro": "2026-09-23T12:30:00"
  }
  ```
- **Retorno de error de negocio**:
  ```json
  {"error": "El hábito ya fue marcado en esta fecha"}
  ```

---

## 4. `eliminar_habito`

- **Descripción**: Elimina un hábito perteneciente al usuario autenticado. Exige confirmación explícita del servidor.
- **Parámetros**:
  - `habito_id` (`integer`): Identificador del hábito a eliminar.
- **Flujo de confirmación**: El servidor ejecuta `ctx.elicit` para requerir aprobación antes de proceder.
- **Retorno exitoso**:
  ```json
  {"mensaje": "Hábito eliminado correctamente"}
  ```
- **Retorno de error de negocio**:
  ```json
  {"error": "No tienes permiso para acceder a este hábito"}
  ```
