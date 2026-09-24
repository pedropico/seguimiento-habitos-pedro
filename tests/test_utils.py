from datetime import date, timedelta
from app.utils.texto import normalizar_nombre, limpiar_nombre_para_mostrar
from app.utils.fechas import es_fecha_futura, a_formato_iso


def test_normalizar_nombre():
    assert normalizar_nombre("  Leer   LIBROS ") == "leer libros"
    assert normalizar_nombre("leer libros") == "leer libros"
    assert normalizar_nombre("") == ""
    assert normalizar_nombre("   ") == ""


def test_limpiar_nombre_para_mostrar():
    assert limpiar_nombre_para_mostrar("  Leer   LIBROS ") == "Leer LIBROS"
    assert limpiar_nombre_para_mostrar("") == ""


def test_es_fecha_futura():
    hoy = date(2026, 9, 23)
    pasado = hoy - timedelta(days=1)
    futuro = hoy + timedelta(days=1)

    assert not es_fecha_futura(hoy, hoy=hoy)
    assert not es_fecha_futura(pasado, hoy=hoy)
    assert es_fecha_futura(futuro, hoy=hoy)
    assert es_fecha_futura("2026-09-24", hoy=hoy)


def test_a_formato_iso():
    d = date(2026, 9, 23)
    assert a_formato_iso(d) == "2026-09-23"
    assert a_formato_iso("2026-09-23") == "2026-09-23"
