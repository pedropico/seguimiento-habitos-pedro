from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_usuarios_repo
from app.schemas.usuario import Token, UsuarioCreate, UsuarioOut
from app.services import usuarios as usuarios_service
from app.services.errores import CredencialesInvalidasError, EmailDuplicadoError, ErrorDeDominio

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


def _a_http_usuarios(exc: ErrorDeDominio) -> HTTPException:
    """Traduce errores de dominio de usuarios a HTTPException."""
    if isinstance(exc, EmailDuplicadoError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.mensaje)
    if isinstance(exc, CredencialesInvalidasError):
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.mensaje)
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.mensaje)


@router.post("/", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def registrar_usuario(
    datos: UsuarioCreate,
    db: Session = Depends(get_db),
    repo: Any = Depends(get_usuarios_repo),
):
    """Registra un nuevo usuario en la plataforma."""
    try:
        usuario = usuarios_service.registrar_usuario(
            db=db,
            email=datos.email,
            password=datos.password,
            repo=repo,
        )
        return usuario
    except ErrorDeDominio as exc:
        raise _a_http_usuarios(exc)


@router.post("/token", response_model=Token)
def login_para_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    repo: Any = Depends(get_usuarios_repo),
):
    """Autentica credenciales y emite token JWT."""
    try:
        resultado = usuarios_service.autenticar_usuario(
            db=db,
            email=form_data.username,
            password=form_data.password,
            repo=repo,
        )
        return resultado
    except ErrorDeDominio as exc:
        raise _a_http_usuarios(exc)
