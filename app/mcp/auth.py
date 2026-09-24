from typing import Any
from mcp.server.auth.provider import AccessToken, TokenVerifier
from app.security import decodificar_token


class JWTTokenVerifier(TokenVerifier):
    """
    Verificador de tokens para MCP reutilizando la misma infraestructura JWT de REST (Artículo VI.4).
    """

    async def verify_token(self, token: str) -> AccessToken | None:
        payload = decodificar_token(token)
        if not payload or "sub" not in payload:
            return None

        # Retorna AccessToken válido para el servidor MCP
        return AccessToken(
            token=token,
            client_id=str(payload["sub"]),
            scopes=["habitos:read", "habitos:write"],
            claims=payload,
        )
