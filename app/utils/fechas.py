from datetime import date, datetime


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
