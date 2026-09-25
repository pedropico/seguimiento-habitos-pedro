"""
Script de Demostración y Evidencia de Seguridad
===============================================
Verifica los 5 vectores de seguridad críticos definidos en el Artículo IV y R6 de la Constitución:

1. Ataque IDOR / Acceso cruzado entre usuarios (R6 / Art. IV.4) -> 403 Forbidden.
2. Inyección de identidad en payloads (Art. IV.4) -> usuario_id extraído únicamente del JWT.
3. Acceso no autenticado y tokens falsificados (Art. IV.2) -> 401 Unauthorized.
4. Protección de contraseñas y no exposición de hashes (Art. IV.1).
5. Sanitización de errores 500 y prevención de fuga de stacktraces (Art. IV.5).
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Base temporal: la demo borra usuarios y no debe tocar habitos.db (va antes de importar app).
os.environ["DATABASE_URL"] = f"sqlite:///{(Path(tempfile.gettempdir()) / 'habitos_demo_seguridad.db').as_posix()}"

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, SessionLocal, engine
from app.models.usuario import Usuario

def ejecutar_demostracion_seguridad():
    print("=" * 80)
    print("    INFORME DE EVIDENCIA DE PRUEBAS DE SEGURIDAD (ARTICULO IV & R6)")
    print("=" * 80)
    
    # Preparar base de datos limpia para la prueba
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        db.query(Usuario).delete()
        db.commit()

    client = TestClient(app, raise_server_exceptions=False)

    # -------------------------------------------------------------------------
    # 1. Registro de dos usuarios independientes
    # -------------------------------------------------------------------------
    print("\n[PASO 1] Creación de dos cuentas independientes:")
    
    resp_u1 = client.post("/usuarios/", json={"email": "alice@empresa.com", "password": "PasswordAlice123!"})
    print(f"  * Registro Usuario A (Alice): HTTP {resp_u1.status_code}")
    print(f"    Payload retornado: {resp_u1.json()} (Confirmado: NO expone hashed_password)")
    assert "hashed_password" not in resp_u1.json(), "FALLO: Se expuso el hash de la contraseña"

    resp_u2 = client.post("/usuarios/", json={"email": "bob@empresa.com", "password": "PasswordBob123!"})
    print(f"  * Registro Usuario B (Bob / Atacante potencial): HTTP {resp_u2.status_code}")

    # Obtención de Tokens JWT
    tok_alice = client.post("/usuarios/token", data={"username": "alice@empresa.com", "password": "PasswordAlice123!"}).json()["access_token"]
    tok_bob = client.post("/usuarios/token", data={"username": "bob@empresa.com", "password": "PasswordBob123!"}).json()["access_token"]
    
    headers_alice = {"Authorization": f"Bearer {tok_alice}"}
    headers_bob = {"Authorization": f"Bearer {tok_bob}"}

    # Alice crea un hábito privado
    habito_alice = client.post("/habitos/", json={"nombre": "Tomar Medicacion Confidencial", "frecuencia_objetivo": 7}, headers=headers_alice).json()
    id_habito_alice = habito_alice["id"]
    print(f"  * Alice crea hábito ID={id_habito_alice}: '{habito_alice['nombre']}'")

    # -------------------------------------------------------------------------
    # 2. Prueba de Seguridad: Ataque IDOR (Insecure Direct Object Reference)
    # -------------------------------------------------------------------------
    print("\n[PASO 2] Prueba de Aislamiento y Ataque IDOR (Bob intenta acceder al hábito de Alice):")
    
    # Bob intenta LEER el hábito de Alice pasando su ID
    resp_idor_get = client.get(f"/habitos/{id_habito_alice}", headers=headers_bob)
    print(f"  * Bob intenta leer GET /habitos/{id_habito_alice}:")
    print(f"    -> Código HTTP: {resp_idor_get.status_code} (Esperado 403 Forbidden)")
    print(f"    -> Respuesta: {resp_idor_get.json()}")
    assert resp_idor_get.status_code == 403

    # Bob intenta MODIFICAR el hábito de Alice
    resp_idor_patch = client.patch(f"/habitos/{id_habito_alice}", json={"nombre": "HACKEADO"}, headers=headers_bob)
    print(f"  * Bob intenta modificar PATCH /habitos/{id_habito_alice}:")
    print(f"    -> Código HTTP: {resp_idor_patch.status_code} (Esperado 403 Forbidden)")
    assert resp_idor_patch.status_code == 403

    # Bob intenta MARCAR el hábito de Alice
    resp_idor_marcar = client.post(f"/habitos/{id_habito_alice}/marcar", headers=headers_bob)
    print(f"  * Bob intenta marcar POST /habitos/{id_habito_alice}/marcar:")
    print(f"    -> Código HTTP: {resp_idor_marcar.status_code} (Esperado 403 Forbidden)")
    assert resp_idor_marcar.status_code == 403

    # Bob intenta ELIMINAR el hábito de Alice
    resp_idor_del = client.delete(f"/habitos/{id_habito_alice}", headers=headers_bob)
    print(f"  * Bob intenta eliminar DELETE /habitos/{id_habito_alice}:")
    print(f"    -> Código HTTP: {resp_idor_del.status_code} (Esperado 403 Forbidden)")
    assert resp_idor_del.status_code == 403

    # Bob lista sus hábitos
    lista_bob = client.get("/habitos/", headers=headers_bob).json()
    print(f"  * Bob lista sus hábitos GET /habitos/: Total={len(lista_bob)} (Cero fuga de hábitos de Alice)")
    assert len(lista_bob) == 0

    # -------------------------------------------------------------------------
    # 3. Prueba de Seguridad: Intento de Inyección de usuario_id en Payload
    # -------------------------------------------------------------------------
    print("\n[PASO 3] Prueba de Inyección de Identidad en Body (Bob intenta crear hábito a nombre de Alice):")
    
    resp_inject = client.post("/habitos/", json={"nombre": "Habito Inyectado", "frecuencia_objetivo": 3, "usuario_id": 1}, headers=headers_bob)
    habito_creado = resp_inject.json()
    print(f"  * Bob envía usuario_id=1 en body. Código HTTP: {resp_inject.status_code}")
    # Verificamos a quién pertenece realmente
    lista_alice = client.get("/habitos/", headers=headers_alice).json()
    nombres_alice = [h["nombre"] for h in lista_alice]
    print(f"  * Verificación en cuenta de Alice: ¿Se inyectó el hábito? {'SÍ' if 'Habito Inyectado' in nombres_alice else 'NO (Protegido)'}")
    assert "Habito Inyectado" not in nombres_alice, "FALLO: Se permitió inyección de usuario_id ajeno"

    # -------------------------------------------------------------------------
    # 4. Prueba de Seguridad: Solicitudes No Autenticadas y Tokens Inválidos
    # -------------------------------------------------------------------------
    print("\n[PASO 4] Prueba de Control de Acceso y Tokens Falsificados:")
    
    # Sin token
    resp_no_token = client.get("/habitos/")
    print(f"  * Solicitud sin cabecera Authorization: HTTP {resp_no_token.status_code} (Esperado 401)")
    assert resp_no_token.status_code == 401

    # Token falso
    resp_fake_token = client.get("/habitos/", headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.falso.firma"})
    print(f"  * Solicitud con JWT adulterado/falso: HTTP {resp_fake_token.status_code} (Esperado 401)")
    assert resp_fake_token.status_code == 401

    # -------------------------------------------------------------------------
    # 5. Prueba de Seguridad: Sanitización de Errores 500 (Artículo IV.5)
    # -------------------------------------------------------------------------
    print("\n[PASO 5] Prueba de Sanitización de Errores Internos 500 (Prevención de fuga de Stacktrace):")
    
    # Invocamos una ruta inexistente o forzamos fallo para verificar formato 500 genérico
    from app.dependencies import get_habitos_repo
    class RepoSimulaErrorCritico:
        def listar(self, *args, **kwargs):
            raise Exception("DATABASE_CORRUPT: connection failed with credentials root:secret123")

    app.dependency_overrides[get_habitos_repo] = lambda: RepoSimulaErrorCritico()
    resp_500 = client.get("/habitos/", headers=headers_alice)
    app.dependency_overrides.clear()

    print(f"  * Excepción interna no controlada: HTTP {resp_500.status_code}")
    print(f"    Respuesta retornada al cliente: {resp_500.json()}")
    assert resp_500.status_code == 500
    assert resp_500.json() == {"detail": "Error interno del servidor"}
    assert "secret123" not in str(resp_500.json())
    print("    -> Confirmado: Stack trace y mensajes de excepción internos NO son expuestos al cliente.")

    print("\n" + "=" * 80)
    print("    RESULTADO FINAL: TODAS LAS PRUEBAS DE SEGURIDAD PASARON SATISFACTORIAMENTE [OK]")
    print("=" * 80)


if __name__ == "__main__":
    ejecutar_demostracion_seguridad()
