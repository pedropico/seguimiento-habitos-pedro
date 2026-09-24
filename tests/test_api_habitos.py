from datetime import date
import pytest
from fastapi.testclient import TestClient
from app.dependencies import get_current_user, get_db, get_habitos_repo
from app.main import app
from tests.fakes import RepositorioFalsoHabitos


@pytest.fixture
def fake_repo():
    return RepositorioFalsoHabitos()


@pytest.fixture
def client_autenticado(fake_repo):
    usuario_mock = {"id": 1, "email": "usuario@test.com"}

    app.dependency_overrides[get_db] = lambda: None
    app.dependency_overrides[get_habitos_repo] = lambda: fake_repo
    app.dependency_overrides[get_current_user] = lambda: usuario_mock

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def client_sin_auth(fake_repo):
    app.dependency_overrides[get_db] = lambda: None
    app.dependency_overrides[get_habitos_repo] = lambda: fake_repo
    # No override de get_current_user

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


# 1. Test sin token devuelve 401
def test_sin_token_devuelve_401(client_sin_auth):
    resp = client_sin_auth.get("/habitos/")
    assert resp.status_code == 401


# 2. Test crear hábito exitoso 201
def test_crear_habito_exitoso_201(client_autenticado):
    resp = client_autenticado.post("/habitos/", json={"nombre": "Leer libros", "frecuencia_objetivo": 5})
    assert resp.status_code == 201
    data = resp.json()
    assert data["nombre"] == "Leer libros"
    assert data["frecuencia_objetivo"] == 5
    assert data["id"] is not None


# 3. Test crear hábito inválido 400 (R1, R2)
def test_crear_habito_invalido_400(client_autenticado):
    # R1 nombre corto
    resp1 = client_autenticado.post("/habitos/", json={"nombre": "ab", "frecuencia_objetivo": 3})
    assert resp1.status_code == 400

    # R2 frecuencia fuera de rango
    resp2 = client_autenticado.post("/habitos/", json={"nombre": "Correr", "frecuencia_objetivo": 9})
    assert resp2.status_code == 400


# 4. Test crear hábito duplicado 409 (R3)
def test_crear_habito_duplicado_409(client_autenticado):
    client_autenticado.post("/habitos/", json={"nombre": "Meditación", "frecuencia_objetivo": 7})
    resp_dup = client_autenticado.post("/habitos/", json={"nombre": "  meditación  ", "frecuencia_objetivo": 3})
    assert resp_dup.status_code == 409


# 5. Test listar hábitos 200
def test_listar_habitos_200(client_autenticado):
    client_autenticado.post("/habitos/", json={"nombre": "Caminar", "frecuencia_objetivo": 4})
    resp = client_autenticado.get("/habitos/")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


# 6. Test marcar hábito exitoso 201
def test_marcar_habito_exitoso_201(client_autenticado):
    h = client_autenticado.post("/habitos/", json={"nombre": "Agua", "frecuencia_objetivo": 7}).json()
    resp = client_autenticado.post(f"/habitos/{h['id']}/marcar")
    assert resp.status_code == 201
    assert resp.json()["habito_id"] == h["id"]


# 7. Test marcar hábito duplicado hoy 409 (R4)
def test_marcar_habito_duplicado_hoy_409(client_autenticado):
    h = client_autenticado.post("/habitos/", json={"nombre": "Piano", "frecuencia_objetivo": 2}).json()
    client_autenticado.post(f"/habitos/{h['id']}/marcar")
    resp_dup = client_autenticado.post(f"/habitos/{h['id']}/marcar")
    assert resp_dup.status_code == 409


# 8. Test operación hábito ajeno 403 (R6)
def test_operacion_habito_ajeno_403(fake_repo):
    # Hábito creado por usuario 1
    h = fake_repo.crear(None, usuario_id=1, nombre="Secreto", nombre_normalizado="secreto", frecuencia_objetivo=1)

    # Cliente autenticado como usuario 2
    app.dependency_overrides[get_db] = lambda: None
    app.dependency_overrides[get_habitos_repo] = lambda: fake_repo
    app.dependency_overrides[get_current_user] = lambda: {"id": 2, "email": "otro@test.com"}

    with TestClient(app) as client_u2:
        resp = client_u2.get(f"/habitos/{h['id']}")
        assert resp.status_code == 403

        resp_marcar = client_u2.post(f"/habitos/{h['id']}/marcar")
        assert resp_marcar.status_code == 403

        resp_act = client_u2.patch(f"/habitos/{h['id']}", json={"nombre": "Nuevo"})
        assert resp_act.status_code == 403

        resp_del = client_u2.delete(f"/habitos/{h['id']}")
        assert resp_del.status_code == 403

    app.dependency_overrides.clear()


# 9. Test actualizar, eliminar y listar registros (API)
def test_actualizar_eliminar_y_listar_registros_api(client_autenticado):
    h = client_autenticado.post("/habitos/", json={"nombre": "Tocar Guitarra", "frecuencia_objetivo": 3}).json()

    # Actualizar
    resp_act = client_autenticado.patch(f"/habitos/{h['id']}", json={"nombre": "Guitarra Clasica", "frecuencia_objetivo": 4})
    assert resp_act.status_code == 200
    assert resp_act.json()["nombre"] == "Guitarra Clasica"

    # Marcar y listar registros
    client_autenticado.post(f"/habitos/{h['id']}/marcar")
    resp_regs = client_autenticado.get(f"/habitos/{h['id']}/registros")
    assert resp_regs.status_code == 200
    assert len(resp_regs.json()) == 1

    # Eliminar
    resp_del = client_autenticado.delete(f"/habitos/{h['id']}")
    assert resp_del.status_code == 204


# 10. Test error no controlado devuelve 500 genérico (Artículo IV.5)
def test_error_no_controlado_devuelve_500_generico():
    class RepositorioRoto:
        def listar(self, *args, **kwargs):
            raise RuntimeError("Fallo inesperado del sistema")

    app.dependency_overrides[get_db] = lambda: None
    app.dependency_overrides[get_habitos_repo] = lambda: RepositorioRoto()
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "email": "u@test.com"}

    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.get("/habitos/")
        assert resp.status_code == 500
        assert resp.json() == {"detail": "Error interno del servidor"}

    app.dependency_overrides.clear()
