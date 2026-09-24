import pytest
from fastapi import HTTPException
from app.dependencies import get_current_user, get_db, get_habitos_repo, get_usuarios_repo
from app.security import crear_token_acceso
from tests.fakes import RepositorioFalsoUsuarios


def test_get_db_yields_session():
    gen = get_db()
    db = next(gen)
    assert db is not None
    try:
        next(gen)
    except StopIteration:
        pass


def test_get_repos_helpers():
    assert get_usuarios_repo() is not None
    assert get_habitos_repo() is not None


def test_get_current_user_valid_and_invalid():
    repo = RepositorioFalsoUsuarios()
    user = repo.crear_usuario(None, "valido@test.com", "hash")

    # Token válido
    token_valido = crear_token_acceso({"sub": str(user["id"]), "email": user["email"]})
    res_user = get_current_user(token=token_valido, db=None, repo=repo)
    assert res_user["id"] == user["id"]

    # Token con usuario inexistente / eliminado
    token_fantasma = crear_token_acceso({"sub": "9999", "email": "fantasma@test.com"})
    with pytest.raises(HTTPException) as exc1:
        get_current_user(token=token_fantasma, db=None, repo=repo)
    assert exc1.value.status_code == 401

    # Token inválido
    with pytest.raises(HTTPException) as exc2:
        get_current_user(token="token_invalido", db=None, repo=repo)
    assert exc2.value.status_code == 401

    # Token sin sub
    token_sin_sub = crear_token_acceso({"email": "nosub@test.com"})
    with pytest.raises(HTTPException) as exc3:
        get_current_user(token=token_sin_sub, db=None, repo=repo)
    assert exc3.value.status_code == 401
