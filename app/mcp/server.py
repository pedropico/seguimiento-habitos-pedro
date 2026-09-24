from mcp.server.fastmcp import FastMCP
from app.mcp.auth import JWTTokenVerifier
from app.mcp.tools.habitos import registrar_tools

# Crear servidor FastMCP
mcp = FastMCP(
    name="SeguimientoHabitosMCP",
    instructions="Servidor MCP para la gestión y seguimiento personal de hábitos.",
    token_verifier=JWTTokenVerifier(),
)

# Registrar herramientas desacopladas (Artículo VI.1)
registrar_tools(mcp)
