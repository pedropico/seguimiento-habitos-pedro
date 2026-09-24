import pytest
from fastapi.testclient import TestClient
from app.dependencies import get_db, get_usuarios_repo
from app.main import app
from tests.fakes import RepositorioFalsoUsuarios


@pytest.fixture
def fake_user_repo():
    return RepositorioFalsoUsuarios()


@pytest.fixture
def client_usuarios(fake_user_repo):
    app.dependency_overrides[get_db] = lambda: None
    app.dependency_overrides[get_usuarios_repo] = lambda: fake_user_repo

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


def test_api_registro_y_login_usuario(client_usuarios):
    # Registro
    resp = client_usuarios.post("/usuarios/", json={"email": "nuevo@test.com", "password": "password123"})
    assert resp.status_code == 201
    assert resp.json()["email"] == "nuevo@test.com"

    # Duplicado
    resp_dup = client_usuarios.post("/usuarios/", json={"email": "nuevo@test.com", "password": "password123"})
    assert resp_dup.status_code == 400

    # Token exitoso
    resp_tok = client_usuarios.post(
        "/usuarios/token",
        data={"username": "nuevo@test.com", "password": "password123"},
    )
    assert resp_tok.status_code == 200
    assert "access_token" in resp_tok.json()

    # Token fallido
    resp_bad = client_usuarios.post(
        "/usuarios/token",
        data={"username": "nuevo@test.com", "password": "badpassword"},
    )
    assert resp_bad.status_code == 401
