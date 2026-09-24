# Contract: REST API — Seguimiento de Hábitos

**Base URL**: `/`
**Autenticación**: `Bearer <JWT_TOKEN>` en header `Authorization: Bearer <token>` para rutas protegidas.

---

## 1. Endpoints de Usuarios y Autenticación

### `POST /usuarios/`
- **Público**: Sí
- **Request Body**:
  ```json
  {
    "email": "usuario@ejemplo.com",
    "password": "Password123!"
  }
  ```
- **Respuestas**:
  - `201 Created`:
    ```json
    {
      "id": 1,
      "email": "usuario@ejemplo.com",
      "fecha_creacion": "2026-09-23T12:00:00"
    }
    ```
  - `400 Bad Request`: `{"detail": "El email ya está registrado"}`
  - `422 Unprocessable Entity`: Error de validación en email o contraseña.

### `POST /usuarios/token`
- **Público**: Sí (Form data `OAuth2PasswordRequestForm`)
- **Request**: `username=usuario@ejemplo.com&password=Password123!`
- **Respuestas**:
  - `200 OK`:
    ```json
    {
      "access_token": "eyJhbGciOi...",
      "token_type": "bearer"
    }
    ```
  - `401 Unauthorized`: `{"detail": "Credenciales inválidas"}`

---

## 2. Endpoints de Hábitos

### `POST /habitos/`
- **Auth**: Requerido
- **Request Body**:
  ```json
  {
    "nombre": "Leer libros",
    "frecuencia_objetivo": 5
  }
  ```
- **Respuestas**:
  - `201 Created`:
    ```json
    {
      "id": 1,
      "nombre": "Leer libros",
      "frecuencia_objetivo": 5,
      "activo": true,
      "fecha_creacion": "2026-09-23T12:00:00"
    }
    ```
  - `400 Bad Request`: `{"detail": "El nombre del hábito debe tener al menos 3 caracteres"}` (R1) o `{"detail": "La frecuencia objetivo debe ser un entero entre 1 y 7"}` (R2)
  - `409 Conflict`: `{"detail": "Ya existe un hábito con este nombre"}` (R3)
  - `401 Unauthorized`: Token ausente o expirado.

### `GET /habitos/`
- **Auth**: Requerido
- **Query Params**: `skip` (default 0), `limit` (default 20, max 100)
- **Respuestas**:
  - `200 OK`: Lista de hábitos del usuario autenticado.

### `GET /habitos/{id}`
- **Auth**: Requerido
- **Respuestas**:
  - `200 OK`: Datos del hábito.
  - `403 Forbidden`: `{"detail": "No tienes permiso para acceder a este hábito"}` (R6).
  - `404 Not Found`: `{"detail": "Hábito no encontrado"}` (R6).

### `PATCH /habitos/{id}`
- **Auth**: Requerido
- **Request Body**: Campos opcionales `nombre`, `frecuencia_objetivo`, `activo`.
- **Respuestas**:
  - `200 OK`: Hábito actualizado.
  - `400 / 403 / 404 / 409 / 422`.

### `DELETE /habitos/{id}`
- **Auth**: Requerido
- **Respuestas**:
  - `204 No Content`.
  - `403 / 404`.

---

## 3. Endpoints de Registros de Cumplimiento

### `POST /habitos/{id}/marcar`
- **Auth**: Requerido
- **Request Body** (opcional):
  ```json
  {
    "fecha": "2026-09-23"
  }
  ```
  *(Si se omite el body o la fecha, se usa la fecha actual).*
- **Respuestas**:
  - `201 Created`:
    ```json
    {
      "id": 1,
      "habito_id": 1,
      "fecha": "2026-09-23",
      "fecha_registro": "2026-09-23T12:30:00"
    }
    ```
  - `400 Bad Request`: `{"detail": "No se puede marcar un hábito en una fecha futura"}` (R5).
  - `409 Conflict`: `{"detail": "El hábito ya fue marcado en esta fecha"}` (R4).
  - `403 Forbidden` (R6) / `404 Not Found` (R6).

### `GET /habitos/{id}/registros`
- **Auth**: Requerido
- **Query Params**: `skip` (default 0), `limit` (default 50)
- **Respuestas**:
  - `200 OK`: Lista de registros ordenados cronológicamente descendente.
  - `403 / 404`.
