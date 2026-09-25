from mcp.server.auth.provider import AccessToken, TokenVerifier

from app.database import SessionLocal
from app.repositories import usuarios as usuarios_repo
from app.security import decodificar_token

SCOPES = ["habitos:read", "habitos:write"]


class JWTTokenVerifier(TokenVerifier):
    """
    Verificador de tokens para MCP reutilizando la misma infraestructura JWT de REST (Artículo VI.4).
    """

    async def verify_token(self, token: str) -> AccessToken | None:
        payload = decodificar_token(token)
        if not payload or "sub" not in payload:
            return None

        # Igual que get_current_user: un JWT de un usuario eliminado no opera como nadie.
        try:
            usuario_id = int(payload["sub"])
        except (ValueError, TypeError):
            return None
        with SessionLocal() as db:
            if usuarios_repo.obtener_por_id(db, usuario_id) is None:
                return None

        # Retorna AccessToken válido para el servidor MCP
        return AccessToken(
            token=token,
            client_id=str(usuario_id),
            subject=str(usuario_id),
            scopes=SCOPES,
            expires_at=payload.get("exp"),
            claims=payload,
        )