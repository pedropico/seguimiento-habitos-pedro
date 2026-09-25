from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP

from app.config import settings
from app.mcp.auth import SCOPES, JWTTokenVerifier
from app.mcp.tools.habitos import registrar_tools


def crear_servidor_mcp() -> FastMCP:
    """
    Crea una instancia nueva del servidor MCP.
    Es una fábrica porque el session manager de streamable-http solo puede
    arrancarse una vez por instancia, y FastAPI ejecuta el lifespan en cada
    arranque (también en cada `with TestClient(app)` de los tests).
    """
    servidor = FastMCP(
        name="SeguimientoHabitosMCP",
        instructions="Servidor MCP para la gestión y seguimiento personal de hábitos.",
        # Artículo VI.4: mismo JWT que la API REST; sin token válido -> 401.
        token_verifier=JWTTokenVerifier(),
        auth=AuthSettings(
            issuer_url=settings.MCP_ISSUER_URL,
            resource_server_url=f"{settings.MCP_ISSUER_URL}/mcp",
            required_scopes=SCOPES,
        ),
        # Se monta en /mcp desde app/main.py, por eso la ruta interna es "/".
        streamable_http_path="/",
    )
    # Registrar herramientas desacopladas (Artículo VI.1)
    registrar_tools(servidor)
    return servidor


# Instancia para uso standalone (p. ej. `mcp dev` o transporte stdio).
mcp = crear_servidor_mcp()
