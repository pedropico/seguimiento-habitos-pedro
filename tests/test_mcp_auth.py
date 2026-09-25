from datetime import timedelta

import pytest

from app.mcp import auth
from app.mcp.auth import SCOPES, JWTTokenVerifier
from app.mcp.server import crear_servidor_mcp
from app.security import crear_token_acceso


@pytest.fixture
def usuario_existente(monkeypatch):
    """Simula que en BD solo existe el usuario id=7."""
    monkeypatch.setattr(
        auth.usuarios_repo,
        "obtener_por_id",
        lambda db, usuario_id: {"id": 7, "email": "u@test.com"} if usuario_id == 7 else None,
    )


@pytest.mark.asyncio
async def test_token_valido_otorga_los_scopes_que_exige_el_servidor(usuario_existente):
    access = await JWTTokenVerifier().verify_token(crear_token_acceso({"sub": "7"}))

    assert access is not None
    assert access.subject == "7"  # las tools leen la identidad de aquí
    requeridos = crear_servidor_mcp().settings.auth.required_scopes
    assert set(requeridos) <= set(access.scopes), "sin estos scopes el servidor responde 403"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "token",
    [
        "no-es-un-jwt",
        crear_token_acceso({"sub": "7"}, expires_delta=timedelta(seconds=-1)),
        crear_token_acceso({"email": "sin-sub@test.com"}),
        crear_token_acceso({"sub": "no-numerico"}),
    ],
    ids=["basura", "expirado", "sin_sub", "sub_no_numerico"],
)
async def test_token_invalido_se_rechaza_sin_lanzar_excepcion(usuario_existente, token):
    assert await JWTTokenVerifier().verify_token(token) is None


@pytest.mark.asyncio
async def test_token_de_usuario_inexistente_se_rechaza(usuario_existente):
    assert await JWTTokenVerifier().verify_token(crear_token_acceso({"sub": "999"})) is None


def test_scopes_del_verificador_coinciden_con_el_servidor():
    assert crear_servidor_mcp().settings.auth.required_scopes == SCOPES
