from datetime import date
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import Session
from app.models.habito import Habito, RegistroHabito
from app.utils.fechas import utc_a_local


def _habito_a_dict(habito: Habito | None) -> dict | None:
    """Convierte modelo Habito a diccionario plano (Artículo I.3)."""
    if habito is None:
        return None
    return {
        "id": habito.id,
        "usuario_id": habito.usuario_id,
        "nombre": habito.nombre,
        "nombre_normalizado": habito.nombre_normalizado,
        "frecuencia_objetivo": habito.frecuencia_objetivo,
        "activo": habito.activo,
        "fecha_creacion": utc_a_local(habito.fecha_creacion),
    }


def _registro_a_dict(registro: RegistroHabito | None) -> dict | None:
    """Convierte modelo RegistroHabito a diccionario plano (Artículo I.3)."""
    if registro is None:
        return None
    return {
        "id": registro.id,
        "habito_id": registro.habito_id,
        "fecha": registro.fecha,
        "fecha_registro": utc_a_local(registro.fecha_registro),
    }


def crear(
    db: Session,
    usuario_id: int,
    nombre: str,
    nombre_normalizado: str,
    frecuencia_objetivo: int,
) -> dict:
    """Crea y persiste un hábito para un usuario."""
    habito = Habito(
        usuario_id=usuario_id,
        nombre=nombre,
        nombre_normalizado=nombre_normalizado,
        frecuencia_objetivo=frecuencia_objetivo,
        activo=True,
    )
    db.add(habito)
    db.commit()
    db.refresh(habito)
    return _habito_a_dict(habito)  # type: ignore


def listar(db: Session, usuario_id: int, skip: int = 0, limit: int = 20) -> list[dict]:
    """Lista hábitos filtrando obligatoriamente por usuario_id (Artículo III.3)."""
    stmt = (
        select(Habito)
        .where(Habito.usuario_id == usuario_id)
        .order_by(Habito.id)
        .offset(skip)
        .limit(limit)
    )
    habitos = db.scalars(stmt).all()
    return [_habito_a_dict(h) for h in habitos]  # type: ignore


def obtener(db: Session, habito_id: int) -> dict | None:
    """
    Obtiene un hábito por ID. No filtra por usuario_id a propósito,
    para que la capa de servicios verifique la pertenencia y distinga 404 de 403 (Artículo III.3).
    """
    stmt = select(Habito).where(Habito.id == habito_id)
    habito = db.scalar(stmt)
    return _habito_a_dict(habito)


def buscar_por_nombre(db: Session, usuario_id: int, nombre_normalizado: str) -> dict | None:
    """Busca un hábito de un usuario específico por su nombre normalizado."""
    stmt = select(Habito).where(
        and_(
            Habito.usuario_id == usuario_id,
            Habito.nombre_normalizado == nombre_normalizado,
        )
    )
    habito = db.scalar(stmt)
    return _habito_a_dict(habito)


def actualizar(db: Session, habito_id: int, **kwargs) -> dict | None:
    """Actualiza campos de un hábito."""
    stmt = select(Habito).where(Habito.id == habito_id)
    habito = db.scalar(stmt)
    if not habito:
        return None

    for clave, valor in kwargs.items():
        if valor is not None and hasattr(habito, clave):
            setattr(habito, clave, valor)

    db.commit()
    db.refresh(habito)
    return _habito_a_dict(habito)


def eliminar(db: Session, habito_id: int) -> bool:
    """Elimina un hábito y sus registros asociados por cascade."""
    stmt = select(Habito).where(Habito.id == habito_id)
    habito = db.scalar(stmt)
    if not habito:
        return False
    db.delete(habito)
    db.commit()
    return True


def existe_registro(db: Session, habito_id: int, fecha: date) -> bool:
    """Verifica si ya existe un registro de cumplimiento para el hábito en la fecha indicada."""
    stmt = select(RegistroHabito).where(
        and_(
            RegistroHabito.habito_id == habito_id,
            RegistroHabito.fecha == fecha,
        )
    )
    registro = db.scalar(stmt)
    return registro is not None


def guardar_registro(db: Session, habito_id: int, fecha: date) -> dict:
    """Guarda una marca de cumplimiento de un hábito."""
    registro = RegistroHabito(
        habito_id=habito_id,
        fecha=fecha,
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return _registro_a_dict(registro)  # type: ignore


def listar_registros(db: Session, habito_id: int, skip: int = 0, limit: int = 50) -> list[dict]:
    """Lista registros de cumplimiento de un hábito ordenados cronológicamente descendente."""
    stmt = (
        select(RegistroHabito)
        .where(RegistroHabito.habito_id == habito_id)
        .order_by(desc(RegistroHabito.fecha), desc(RegistroHabito.id))
        .offset(skip)
        .limit(limit)
    )
    registros = db.scalars(stmt).all()
    return [_registro_a_dict(r) for r in registros]  # type: ignore
