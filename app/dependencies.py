from typing import Any, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.repositories import habitos as habitos_repo
from app.repositories import usuarios as usuarios_repo
from app.security import decodificar_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/usuarios/token")


def get_db() -> Generator[Session, None, None]:
    """Generador de sesiones de base de datos."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_usuarios_repo() -> Any:
    """Inyección del repositorio de usuarios para permitir overrides en tests."""
    return usuarios_repo


def get_habitos_repo() -> Any:
    """Inyección del repositorio de hábitos para permitir overrides en tests."""
    return habitos_repo


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    repo: Any = Depends(get_usuarios_repo),
) -> dict:
    """
    Artículo IV.4: El usuario_id SIEMPRE sale del token JWT verificado.
    DoD: Un JWT de un usuario eliminado no opera como nadie (valida existencia en BD).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o token expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decodificar_token(token)
    if payload is None:
        raise credentials_exception

    sub = payload.get("sub")
    if sub is None:
        raise credentials_exception

    try:
        usuario_id = int(sub)
    except (ValueError, TypeError):
        raise credentials_exception

    usuario = repo.obtener_por_id(db, usuario_id)
    if usuario is None:
        raise credentials_exception

    return usuario
