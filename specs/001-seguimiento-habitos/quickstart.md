# Quickstart & Validation Guide: Seguimiento de Hábitos

**Feature**: `specs/001-seguimiento-habitos`
**Date**: 2026-09-23

---

## 1. Configuración y Entorno

```bash
# Crear entorno virtual e instalar dependencias
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env

# Ejecutar migraciones o inicialización de base de datos
alembic upgrade head
```

---

## 2. Ejecución de la Suite de Pruebas y Cobertura

```bash
# Ejecutar todas las pruebas con reporte de cobertura
pytest --cov=app --cov-report=term-missing

# Ejecutar únicamente pruebas unitarias de reglas de negocio
pytest tests/test_habitos_service.py -v

# Ejecutar pruebas de integración y de API
pytest tests/test_integracion_habitos.py tests/test_api_habitos.py -v

# Ejecutar pruebas de MCP tools
pytest tests/test_mcp_habitos.py -v
```

---

## 3. Escenarios de Validación End-to-End

### Escenario 1: Registro y Autenticación
1. Registrar un usuario nuevo: `POST /usuarios/` con email y contraseña.
2. Obtener token JWT: `POST /usuarios/token` con `username` y `password`.

### Escenario 2: Gestión de Hábitos (R1, R2, R3)
1. Crear un hábito válido: `POST /habitos/` con `{"nombre": "Lectura", "frecuencia_objetivo": 5}` → Recibir `201 Created`.
2. Probar duplicado R3: `POST /habitos/` con `{"nombre": "  lectura  ", "frecuencia_objetivo": 3}` → Recibir `409 Conflict`.
3. Probar nombre inválido R1: `POST /habitos/` con `{"nombre": "  ab  "}` → Recibir `400 Bad Request`.
4. Probar frecuencia inválida R2: `POST /habitos/` con `{"frecuencia_objetivo": 8}` → Recibir `400 Bad Request`.

### Escenario 3: Marcado de Cumplimiento (R4, R5, R6)
1. Marcar hábito en el día de hoy: `POST /habitos/{id}/marcar` → Recibir `201 Created`.
2. Intentar duplicar marca en el mismo día (R4): `POST /habitos/{id}/marcar` → Recibir `409 Conflict`.
3. Intentar marcar con fecha futura (R5): `POST /habitos/{id}/marcar` con `{"fecha": "2099-01-01"}` → Recibir `400 Bad Request`.
4. Intentar marcar el hábito con otro usuario (R6): Usar token de Usuario B sobre ID de Usuario A → Recibir `403 Forbidden`.

### Escenario 4: MCP Inspector
1. Conectar MCP Inspector al endpoint streamable-http `/mcp`.
2. Ejecutar `listar_habitos` y verificar que solo retorna los hábitos del usuario del token.
3. Ejecutar `marcar_habito` y `eliminar_habito` (con confirmación de elicitación).
