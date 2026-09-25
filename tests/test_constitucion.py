"""
Tests de regresión de desviaciones de la constitución detectadas y corregidas.
Cada test lleva el artículo en el nombre (test_VI4_...), igual que las reglas (test_R4_...).
Ver docs/registro-desviaciones.md.
"""

from types import SimpleNamespace

import pytest
from mcp.server.auth.middleware.auth_context import auth_context_var
from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
from mcp.server.auth.provider import AccessToken

from app.mcp.tools import habitos as tools

VICTIMA = "999"


@pytest.fixture
def ctx_con_meta_falsificado():
    """Contexto MCP cuyo `_meta.client_id` lo escribió el cliente: apunta a otro usuario."""
    return SimpleNamespace(client_id=VICTIMA)


@pytest.fixture
def token_verificado_de_usuario_7():
    """Simula lo que deja AuthContextMiddleware tras validar un Bearer JWT de sub=7."""
    access = AccessToken(token="jwt", client_id="7", subject="7", scopes=[])
    marca = auth_context_var.set(AuthenticatedUser(access))
    yield
    auth_context_var.reset(marca)


def test_VI4_con_token_la_identidad_sale_del_token_no_del_meta_del_cliente(
    ctx_con_meta_falsificado, token_verificado_de_usuario_7
):
    assert tools._resolver_usuario_id(ctx_con_meta_falsificado) == 7


def test_VI4_sin_token_el_meta_del_cliente_no_suplanta_identidad(ctx_con_meta_falsificado):
    # Sin token solo vale el usuario demo documentado (stdio), nunca lo que diga el cliente.
    assert tools._resolver_usuario_id(ctx_con_meta_falsificado) != int(VICTIMA)
