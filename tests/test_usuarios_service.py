import pytest
from app.services.errores import CredencialesInvalidasError, EmailDuplicadoError
from app.services import usuarios as usuarios_service
from tests.fakes import RepositorioFalsoUsuarios


def test_registrar_usuario_exitoso_y_duplicado():
    repo = RepositorioFalsoUsuarios()
    db = None

    u = usuarios_service.registrar_usuario(
        db,
        email="test@correo.com",
        password="password123",
        repo=repo,
        hasheador=lambda p: f"hash_{p}",
    )
    assert u["id"] is not None
    assert u["email"] == "test@correo.com"
    assert u["hashed_password"] == "hash_password123"

    with pytest.raises(EmailDuplicadoError):
        usuarios_service.registrar_usuario(
            db,
            email="TEST@correo.com",
            password="otra",
            repo=repo,
            hasheador=lambda p: f"hash_{p}",
        )


def test_autenticar_usuario_exitoso_y_errores():
    repo = RepositorioFalsoUsuarios()
    db = None

    usuarios_service.registrar_usuario(
        db,
        email="user@test.com",
        password="secretpassword",
        repo=repo,
        hasheador=lambda p: f"hashed_{p}",
    )

    # Login correcto
    res = usuarios_service.autenticar_usuario(
        db,
        email="user@test.com",
        password="secretpassword",
        repo=repo,
        verificador=lambda plain, hashed: hashed == f"hashed_{plain}",
    )
    assert "access_token" in res
    assert res["token_type"] == "bearer"

    # Password incorrecta
    with pytest.raises(CredencialesInvalidasError):
        usuarios_service.autenticar_usuario(
            db,
            email="user@test.com",
            password="wrongpassword",
            repo=repo,
            verificador=lambda plain, hashed: hashed == f"hashed_{plain}",
        )

    # Email inexistente
    with pytest.raises(CredencialesInvalidasError):
        usuarios_service.autenticar_usuario(
            db,
            email="noexiste@test.com",
            password="secretpassword",
            repo=repo,
            verificador=lambda plain, hashed: hashed == f"hashed_{plain}",
        )


def test_obtener_usuario_por_id():
    repo = RepositorioFalsoUsuarios()
    db = None

    u = usuarios_service.registrar_usuario(
        db, email="idtest@test.com", password="pw", repo=repo, hasheador=lambda p: p
    )
    encontrado = usuarios_service.obtener_usuario_por_id(db, u["id"], repo=repo)
    assert encontrado["id"] == u["id"]

    from app.services.errores import UsuarioNoEncontradoError

    with pytest.raises(UsuarioNoEncontradoError):
        usuarios_service.obtener_usuario_por_id(db, 99999, repo=repo)
