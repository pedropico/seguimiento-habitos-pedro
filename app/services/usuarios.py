from typing import Any

from app.repositories import usuarios as usuarios_repository
from app.security import crear_token_acceso, hashear_password, verificar_password
from app.services.errores import CredencialesInvalidasError, EmailDuplicadoError, UsuarioNoEncontradoError


def registrar_usuario(
    db: Any,
    email: str,
    password: str,
    repo: Any = usuarios_repository,
    hasheador: Any = hashear_password,
) -> dict:
    """Registra un nuevo usuario en el sistema con contraseña hasheada."""
    existente = repo.obtener_por_email(db, email.lower().strip())
    if existente:
        raise EmailDuplicadoError("El email ya se encuentra registrado")

    hash_pw = hasheador(password)
    usuario = repo.crear_usuario(db, email=email.lower().strip(), hashed_password=hash_pw)
    return usuario


def autenticar_usuario(
    db: Any,
    email: str,
    password: str,
    repo: Any = usuarios_repository,
    verificador: Any = verificar_password,
) -> dict:
    """
    Autentica un usuario y emite token JWT.
    Mensaje de error indistinguible para email no encontrado y password incorrecta (Artículo IV).
    """
    usuario = repo.obtener_por_email(db, email.lower().strip())
    if not usuario:
        raise CredencialesInvalidasError("Credenciales inválidas")

    if not verificador(password, usuario["hashed_password"]):
        raise CredencialesInvalidasError("Credenciales inválidas")

    # Generar token con payload estándar
    token_data = {
        "sub": str(usuario["id"]),
        "email": usuario["email"],
    }
    access_token = crear_token_acceso(token_data)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "usuario": usuario,
    }


def obtener_usuario_por_id(
    db: Any,
    usuario_id: int,
    repo: Any = usuarios_repository,
) -> dict:
    """Obtiene usuario por ID."""
    usuario = repo.obtener_por_id(db, usuario_id)
    if not usuario:
        raise UsuarioNoEncontradoError(f"El usuario con ID {usuario_id} no existe")
    return usuario
