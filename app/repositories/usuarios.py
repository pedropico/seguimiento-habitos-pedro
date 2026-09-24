from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.usuario import Usuario


def _usuario_a_dict(usuario: Usuario | None) -> dict | None:
    """Convierte modelo Usuario a diccionario plano (Artículo I.3)."""
    if usuario is None:
        return None
    return {
        "id": usuario.id,
        "email": usuario.email,
        "hashed_password": usuario.hashed_password,
        "fecha_creacion": usuario.fecha_creacion,
    }


def crear_usuario(db: Session, email: str, hashed_password: str) -> dict:
    """Guarda un nuevo usuario en base de datos y retorna dict."""
    usuario = Usuario(
        email=email,
        hashed_password=hashed_password,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return _usuario_a_dict(usuario)  # type: ignore


def obtener_por_email(db: Session, email: str) -> dict | None:
    """Busca un usuario por su email."""
    stmt = select(Usuario).where(Usuario.email == email)
    usuario = db.scalar(stmt)
    return _usuario_a_dict(usuario)


def obtener_por_id(db: Session, usuario_id: int) -> dict | None:
    """Busca un usuario por su ID."""
    stmt = select(Usuario).where(Usuario.id == usuario_id)
    usuario = db.scalar(stmt)
    return _usuario_a_dict(usuario)
