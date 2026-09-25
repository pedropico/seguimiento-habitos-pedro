from datetime import date, datetime, timezone


def utc_a_local(momento: datetime | None) -> datetime | None:
    """
    Los timestamps se guardan en UTC, pero SQLite los devuelve sin zona horaria.
    Se marca como UTC y se convierte a la hora local del servidor, con offset explícito
    (p. ej. 2026-09-24T22:33:38-05:00), para que no aparenten ser del día siguiente.
    """
    if momento is None:
        return None
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)
    return momento.astimezone()


def obtener_fecha_hoy() -> date:
    """Función para obtener la fecha actual (date)."""
    return date.today()


def es_fecha_futura(fecha: date | str, hoy: date | None = None) -> bool:
    """
    Función pura para determinar si una fecha es estrictamente posterior a hoy.
    La fecha de hoy retorna False (no es futura).
    """
    if hoy is None:
        hoy = obtener_fecha_hoy()

    if isinstance(fecha, str):
        fecha = datetime.strptime(fecha, "%Y-%m-%d").date()

    return fecha > hoy


def a_formato_iso(fecha: date | datetime | str) -> str:
    """Convierte date o datetime a string ISO YYYY-MM-DD."""
    if isinstance(fecha, str):
        return fecha
    if isinstance(fecha, datetime):
        return fecha.date().isoformat()
    return fecha.isoformat()
