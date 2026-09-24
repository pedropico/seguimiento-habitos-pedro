from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, get_habitos_repo
from app.schemas.habito import HabitoCreate, HabitoOut, HabitoUpdate, RegistroCreate, RegistroOut
from app.services import habitos as habitos_service
from app.services.errores import (
    ErrorDeDominio,
    FechaFuturaError,
    FrecuenciaInvalidaError,
    HabitoAjenoError,
    HabitoDuplicadoError,
    HabitoNoEncontradoError,
    NombreInvalidoError,
    YaMarcadoHoyError,
)

router = APIRouter(prefix="/habitos", tags=["Hábitos"])

# Artículo V.1: Diccionario centralizado de traducción excepción de dominio -> código HTTP
_CODIGOS: dict[type[ErrorDeDominio], int] = {
    NombreInvalidoError: status.HTTP_400_BAD_REQUEST,
    FrecuenciaInvalidaError: status.HTTP_400_BAD_REQUEST,
    HabitoDuplicadoError: status.HTTP_409_CONFLICT,
    YaMarcadoHoyError: status.HTTP_409_CONFLICT,
    FechaFuturaError: status.HTTP_400_BAD_REQUEST,
    HabitoAjenoError: status.HTTP_403_FORBIDDEN,
    HabitoNoEncontradoError: status.HTTP_404_NOT_FOUND,
}


def _a_http(exc: ErrorDeDominio) -> HTTPException:
    """
    Traduce exclusivamente excepciones de dominio a HTTPException.
    Cualquier otra excepción no capturada subirá al manejador global de main.py
    y retornará un 500 genérico (Artículo IV.5 y V.1).
    """
    codigo = _CODIGOS.get(type(exc), status.HTTP_400_BAD_REQUEST)
    return HTTPException(status_code=codigo, detail=exc.mensaje)


@router.post("/", response_model=HabitoOut, status_code=status.HTTP_201_CREATED)
def crear_habito(
    datos: HabitoCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    repo: Any = Depends(get_habitos_repo),
):
    """Crea un nuevo hábito para el usuario autenticado (R1, R2, R3)."""
    try:
        habito = habitos_service.crear_habito(
            db=db,
            usuario_id=current_user["id"],
            nombre=datos.nombre,
            frecuencia_objetivo=datos.frecuencia_objetivo,
            repo=repo,
        )
        return habito
    except ErrorDeDominio as exc:
        raise _a_http(exc)


@router.get("/", response_model=list[HabitoOut])
def listar_habitos(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    repo: Any = Depends(get_habitos_repo),
):
    """Lista hábitos del usuario autenticado (Artículo III.3)."""
    return habitos_service.listar_habitos(
        db=db,
        usuario_id=current_user["id"],
        skip=skip,
        limit=limit,
        repo=repo,
    )


@router.get("/{id}", response_model=HabitoOut)
def obtener_habito(
    id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    repo: Any = Depends(get_habitos_repo),
):
    """Obtiene un hábito por ID verificando pertenencia (R6)."""
    try:
        return habitos_service.obtener_habito(
            db=db,
            usuario_id=current_user["id"],
            habito_id=id,
            repo=repo,
        )
    except ErrorDeDominio as exc:
        raise _a_http(exc)


@router.patch("/{id}", response_model=HabitoOut)
def actualizar_habito(
    id: int,
    datos: HabitoUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    repo: Any = Depends(get_habitos_repo),
):
    """Actualiza parcialmente un hábito (R1, R2, R3, R6)."""
    try:
        return habitos_service.actualizar_habito(
            db=db,
            usuario_id=current_user["id"],
            habito_id=id,
            nombre=datos.nombre,
            frecuencia_objetivo=datos.frecuencia_objetivo,
            activo=datos.activo,
            repo=repo,
        )
    except ErrorDeDominio as exc:
        raise _a_http(exc)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_habito(
    id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    repo: Any = Depends(get_habitos_repo),
):
    """Elimina un hábito verificando pertenencia (R6)."""
    try:
        habitos_service.eliminar_habito(
            db=db,
            usuario_id=current_user["id"],
            habito_id=id,
            repo=repo,
        )
        return None
    except ErrorDeDominio as exc:
        raise _a_http(exc)


@router.post("/{id}/marcar", response_model=RegistroOut, status_code=status.HTTP_201_CREATED)
def marcar_habito(
    id: int,
    datos: RegistroCreate | None = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    repo: Any = Depends(get_habitos_repo),
):
    """Marca un hábito como cumplido (R4, R5, R6)."""
    fecha = datos.fecha if datos else None
    try:
        registro = habitos_service.marcar_habito(
            db=db,
            usuario_id=current_user["id"],
            habito_id=id,
            fecha=fecha,
            repo=repo,
        )
        return registro
    except ErrorDeDominio as exc:
        raise _a_http(exc)


@router.get("/{id}/registros", response_model=list[RegistroOut])
def listar_registros(
    id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    repo: Any = Depends(get_habitos_repo),
):
    """Lista registros de cumplimiento de un hábito (R6)."""
    try:
        return habitos_service.listar_registros(
            db=db,
            usuario_id=current_user["id"],
            habito_id=id,
            skip=skip,
            limit=limit,
            repo=repo,
        )
    except ErrorDeDominio as exc:
        raise _a_http(exc)
