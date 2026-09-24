from datetime import date, datetime
from typing import Any

from app.repositories import habitos as habitos_repository
from app.services.errores import (
    FrecuenciaInvalidaError,
    HabitoAjenoError,
    HabitoDuplicadoError,
    HabitoNoEncontradoError,
    NombreInvalidoError,
    FechaFuturaError,
    YaMarcadoHoyError,
)
from app.utils.fechas import a_formato_iso, es_fecha_futura, obtener_fecha_hoy
from app.utils.texto import limpiar_nombre_para_mostrar, normalizar_nombre

# Artículo II.2 (OCP): Constantes configurables
NOMBRE_MIN_LONGITUD = 3
FRECUENCIA_MINIMA = 1
FRECUENCIA_MAXIMA = 7


# Validaciones atómicas (Artículo II.1 - SRP)
def _validar_nombre(nombre: str) -> str:
    """Valida regla R1: el nombre debe tener al menos 3 caracteres útiles."""
    if not isinstance(nombre, str):
        raise NombreInvalidoError("El nombre del hábito debe ser una cadena de texto")
    nombre_limpio = limpiar_nombre_para_mostrar(nombre)
    if len(nombre_limpio) < NOMBRE_MIN_LONGITUD:
        raise NombreInvalidoError(
            f"El nombre del hábito no puede estar vacío ni tener menos de {NOMBRE_MIN_LONGITUD} caracteres"
        )
    return nombre_limpio


def _validar_frecuencia(frecuencia: Any) -> int:
    """Valida regla R2: la frecuencia debe ser un entero entre 1 y 7."""
    if not isinstance(frecuencia, int) or isinstance(frecuencia, bool):
        raise FrecuenciaInvalidaError("La frecuencia objetivo debe ser un número entero")
    if frecuencia < FRECUENCIA_MINIMA or frecuencia > FRECUENCIA_MAXIMA:
        raise FrecuenciaInvalidaError(
            f"La frecuencia objetivo debe ser un entero entre {FRECUENCIA_MINIMA} y {FRECUENCIA_MAXIMA}"
        )
    return frecuencia


def _habito_propio(db: Any, usuario_id: int, habito_id: int, repo: Any = habitos_repository) -> dict:
    """
    Valida regla R6: verifica existencia y pertenencia antes de operar sobre un hábito.
    Distingue explícitamente 404 (no existe) de 403 (existe pero pertenece a otro).
    """
    habito = repo.obtener(db, habito_id)
    if not habito:
        raise HabitoNoEncontradoError(f"El hábito con ID {habito_id} no existe")
    if habito["usuario_id"] != usuario_id:
        raise HabitoAjenoError("No tienes permiso para acceder o modificar este hábito")
    return habito


def _validar_fecha(fecha: date | str | None) -> date:
    """Valida regla R5: rechaza fechas estrictamente posteriores a hoy."""
    hoy = obtener_fecha_hoy()
    if fecha is None:
        return hoy

    if isinstance(fecha, str):
        try:
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
        except ValueError:
            raise FechaFuturaError("Formato de fecha inválido. Se espera YYYY-MM-DD")
    else:
        fecha_obj = fecha

    if es_fecha_futura(fecha_obj, hoy=hoy):
        raise FechaFuturaError("No se puede marcar un hábito en una fecha futura")
    return fecha_obj


# Funciones de orquestación (Artículo II.3 - DIP)
def crear_habito(
    db: Any,
    usuario_id: int,
    nombre: str,
    frecuencia_objetivo: int,
    repo: Any = habitos_repository,
) -> dict:
    """Orquesta la creación de un nuevo hábito validando R1, R2 y R3."""
    nombre_limpio = _validar_nombre(nombre)
    frecuencia_valida = _validar_frecuencia(frecuencia_objetivo)
    norm = normalizar_nombre(nombre_limpio)

    # R3: Control de duplicados por usuario
    existente = repo.buscar_por_nombre(db, usuario_id, norm)
    if existente:
        raise HabitoDuplicadoError("Ya tienes un hábito registrado con este nombre")

    return repo.crear(
        db,
        usuario_id=usuario_id,
        nombre=nombre_limpio,
        nombre_normalizado=norm,
        frecuencia_objetivo=frecuencia_valida,
    )


def listar_habitos(
    db: Any,
    usuario_id: int,
    skip: int = 0,
    limit: int = 20,
    repo: Any = habitos_repository,
) -> list[dict]:
    """Lista los hábitos pertenecientes al usuario autenticado (R6 / III.3)."""
    return repo.listar(db, usuario_id=usuario_id, skip=skip, limit=limit)


def obtener_habito(
    db: Any,
    usuario_id: int,
    habito_id: int,
    repo: Any = habitos_repository,
) -> dict:
    """Obtiene un hábito por ID verificando pertenencia (R6)."""
    return _habito_propio(db, usuario_id=usuario_id, habito_id=habito_id, repo=repo)


def actualizar_habito(
    db: Any,
    usuario_id: int,
    habito_id: int,
    nombre: str | None = None,
    frecuencia_objetivo: int | None = None,
    activo: bool | None = None,
    repo: Any = habitos_repository,
) -> dict:
    """Actualiza campos de un hábito verificando pertenencia y reglas de negocio."""
    _habito_propio(db, usuario_id=usuario_id, habito_id=habito_id, repo=repo)

    updates: dict[str, Any] = {}

    if nombre is not None:
        nombre_limpio = _validar_nombre(nombre)
        norm = normalizar_nombre(nombre_limpio)
        existente = repo.buscar_por_nombre(db, usuario_id, norm)
        if existente and existente["id"] != habito_id:
            raise HabitoDuplicadoError("Ya tienes otro hábito registrado con este nombre")
        updates["nombre"] = nombre_limpio
        updates["nombre_normalizado"] = norm

    if frecuencia_objetivo is not None:
        updates["frecuencia_objetivo"] = _validar_frecuencia(frecuencia_objetivo)

    if activo is not None:
        updates["activo"] = bool(activo)

    habito_act = repo.actualizar(db, habito_id, **updates)
    return habito_act


def eliminar_habito(
    db: Any,
    usuario_id: int,
    habito_id: int,
    repo: Any = habitos_repository,
) -> bool:
    """Elimina un hábito verificando pertenencia (R6)."""
    _habito_propio(db, usuario_id=usuario_id, habito_id=habito_id, repo=repo)
    return repo.eliminar(db, habito_id)


def marcar_habito(
    db: Any,
    usuario_id: int,
    habito_id: int,
    fecha: date | str | None = None,
    repo: Any = habitos_repository,
) -> dict:
    """
    Orquestación de la marca de cumplimiento (R4, R5, R6).
    Secuencia validada por speckit-analyze:
    1. Verificar pertenencia del hábito al usuario (R6).
    2. Validar que la fecha no sea futura (R5).
    3. Validar que no exista ya un registro para esa fecha (R4).
    4. Guardar y persistir el registro.
    """
    # 1. R6: Pertenencia
    _habito_propio(db, usuario_id=usuario_id, habito_id=habito_id, repo=repo)

    # 2. R5: Fecha no futura
    fecha_valida = _validar_fecha(fecha)

    # 3. R4: No marcado hoy/en la fecha
    if repo.existe_registro(db, habito_id, fecha_valida):
        raise YaMarcadoHoyError(
            f"El hábito ya fue marcado como cumplido en la fecha {a_formato_iso(fecha_valida)}"
        )

    # 4. Persistencia
    return repo.guardar_registro(db, habito_id, fecha_valida)


def listar_registros(
    db: Any,
    usuario_id: int,
    habito_id: int,
    skip: int = 0,
    limit: int = 50,
    repo: Any = habitos_repository,
) -> list[dict]:
    """Lista registros de cumplimiento de un hábito verificando pertenencia (R6)."""
    _habito_propio(db, usuario_id=usuario_id, habito_id=habito_id, repo=repo)
    return repo.listar_registros(db, habito_id, skip=skip, limit=limit)
