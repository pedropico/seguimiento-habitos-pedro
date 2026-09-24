from datetime import date, timedelta
import pytest
from app.services.errores import (
    FechaFuturaError,
    FrecuenciaInvalidaError,
    HabitoAjenoError,
    HabitoDuplicadoError,
    HabitoNoEncontradoError,
    NombreInvalidoError,
    YaMarcadoHoyError,
)
from app.services import habitos as habitos_service
from tests.fakes import RepositorioFalsoHabitos


# ---------------------------------------------------------------------------
# Regla R1: Nombre no vacío ni menor a 3 caracteres útiles
# ---------------------------------------------------------------------------
def test_R1_nombre_demasiado_corto_es_rechazado():
    repo = RepositorioFalsoHabitos()
    db = None

    with pytest.raises(NombreInvalidoError):
        habitos_service.crear_habito(db, usuario_id=1, nombre="ab", frecuencia_objetivo=3, repo=repo)

    with pytest.raises(NombreInvalidoError):
        habitos_service.crear_habito(db, usuario_id=1, nombre="   ", frecuencia_objetivo=3, repo=repo)

    with pytest.raises(NombreInvalidoError):
        habitos_service.crear_habito(db, usuario_id=1, nombre="  a  ", frecuencia_objetivo=3, repo=repo)


# ---------------------------------------------------------------------------
# Regla R2: Frecuencia objetivo entre 1 y 7 veces por semana
# ---------------------------------------------------------------------------
def test_R2_frecuencia_fuera_de_rango_es_rechazada():
    repo = RepositorioFalsoHabitos()
    db = None

    with pytest.raises(FrecuenciaInvalidaError):
        habitos_service.crear_habito(db, usuario_id=1, nombre="Leer", frecuencia_objetivo=0, repo=repo)

    with pytest.raises(FrecuenciaInvalidaError):
        habitos_service.crear_habito(db, usuario_id=1, nombre="Leer", frecuencia_objetivo=8, repo=repo)


def test_R2_frecuencia_no_entera_es_rechazada():
    repo = RepositorioFalsoHabitos()
    db = None

    with pytest.raises(FrecuenciaInvalidaError):
        habitos_service.crear_habito(db, usuario_id=1, nombre="Leer", frecuencia_objetivo="5", repo=repo)  # type: ignore

    with pytest.raises(FrecuenciaInvalidaError):
        habitos_service.crear_habito(db, usuario_id=1, nombre="Leer", frecuencia_objetivo=True, repo=repo)  # type: ignore


# ---------------------------------------------------------------------------
# Regla R3: No duplicidad de nombre para el mismo usuario
# ---------------------------------------------------------------------------
def test_R3_nombre_duplicado_para_el_mismo_usuario_es_rechazado():
    repo = RepositorioFalsoHabitos()
    db = None

    habitos_service.crear_habito(db, usuario_id=1, nombre="Leer libros", frecuencia_objetivo=5, repo=repo)

    with pytest.raises(HabitoDuplicadoError):
        habitos_service.crear_habito(db, usuario_id=1, nombre="  leer   LIBROS ", frecuencia_objetivo=3, repo=repo)


def test_R3_el_mismo_nombre_en_otro_usuario_si_se_permite():
    repo = RepositorioFalsoHabitos()
    db = None

    h1 = habitos_service.crear_habito(db, usuario_id=1, nombre="Leer libros", frecuencia_objetivo=5, repo=repo)
    h2 = habitos_service.crear_habito(db, usuario_id=2, nombre="leer libros", frecuencia_objetivo=4, repo=repo)

    assert h1["id"] != h2["id"]
    assert h1["usuario_id"] == 1
    assert h2["usuario_id"] == 2


# ---------------------------------------------------------------------------
# Regla R4: Un hábito no puede marcarse dos veces el mismo día
# ---------------------------------------------------------------------------
def test_R4_marcar_dos_veces_el_mismo_dia_es_rechazado():
    repo = RepositorioFalsoHabitos()
    db = None

    h = habitos_service.crear_habito(db, usuario_id=1, nombre="Correr", frecuencia_objetivo=3, repo=repo)
    hoy = date.today()

    habitos_service.marcar_habito(db, usuario_id=1, habito_id=h["id"], fecha=hoy, repo=repo)

    with pytest.raises(YaMarcadoHoyError):
        habitos_service.marcar_habito(db, usuario_id=1, habito_id=h["id"], fecha=hoy, repo=repo)


def test_R4_marcar_el_mismo_habito_en_dias_distintos_si_se_permite():
    repo = RepositorioFalsoHabitos()
    db = None

    h = habitos_service.crear_habito(db, usuario_id=1, nombre="Correr", frecuencia_objetivo=3, repo=repo)
    ayer = date.today() - timedelta(days=1)
    hoy = date.today()

    r1 = habitos_service.marcar_habito(db, usuario_id=1, habito_id=h["id"], fecha=ayer, repo=repo)
    r2 = habitos_service.marcar_habito(db, usuario_id=1, habito_id=h["id"], fecha=hoy, repo=repo)

    assert r1["id"] != r2["id"]


def test_R4_sin_fecha_explicita_se_usa_hoy():
    repo = RepositorioFalsoHabitos()
    db = None

    h = habitos_service.crear_habito(db, usuario_id=1, nombre="Meditar", frecuencia_objetivo=7, repo=repo)
    reg = habitos_service.marcar_habito(db, usuario_id=1, habito_id=h["id"], fecha=None, repo=repo)

    assert reg["fecha"] == date.today()


# ---------------------------------------------------------------------------
# Regla R5: Rechazo de fechas futuras
# ---------------------------------------------------------------------------
def test_R5_marcar_en_fecha_futura_es_rechazado():
    repo = RepositorioFalsoHabitos()
    db = None

    h = habitos_service.crear_habito(db, usuario_id=1, nombre="Estudiar", frecuencia_objetivo=5, repo=repo)
    manana = date.today() + timedelta(days=1)

    with pytest.raises(FechaFuturaError):
        habitos_service.marcar_habito(db, usuario_id=1, habito_id=h["id"], fecha=manana, repo=repo)


# ---------------------------------------------------------------------------
# Regla R6: Pertenencia estricta antes de operar por ID
# ---------------------------------------------------------------------------
def test_R6_no_se_puede_marcar_el_habito_de_otro_usuario():
    repo = RepositorioFalsoHabitos()
    db = None

    h_u1 = habitos_service.crear_habito(db, usuario_id=1, nombre="Yoga", frecuencia_objetivo=2, repo=repo)

    with pytest.raises(HabitoAjenoError):
        habitos_service.marcar_habito(db, usuario_id=2, habito_id=h_u1["id"], repo=repo)


def test_R6_no_se_puede_eliminar_el_habito_de_otro_usuario():
    repo = RepositorioFalsoHabitos()
    db = None

    h_u1 = habitos_service.crear_habito(db, usuario_id=1, nombre="Yoga", frecuencia_objetivo=2, repo=repo)

    with pytest.raises(HabitoAjenoError):
        habitos_service.eliminar_habito(db, usuario_id=2, habito_id=h_u1["id"], repo=repo)


def test_R6_habito_inexistente_se_distingue_de_habito_ajeno():
    repo = RepositorioFalsoHabitos()
    db = None

    h_u1 = habitos_service.crear_habito(db, usuario_id=1, nombre="Yoga", frecuencia_objetivo=2, repo=repo)

    # Inexistente → HabitoNoEncontradoError (404)
    with pytest.raises(HabitoNoEncontradoError):
        habitos_service.obtener_habito(db, usuario_id=1, habito_id=999, repo=repo)

    # De otro usuario → HabitoAjenoError (403)
    with pytest.raises(HabitoAjenoError):
        habitos_service.obtener_habito(db, usuario_id=2, habito_id=h_u1["id"], repo=repo)


def test_R6_listar_solo_devuelve_los_habitos_propios():
    repo = RepositorioFalsoHabitos()
    db = None

    habitos_service.crear_habito(db, usuario_id=1, nombre="Habito 1 U1", frecuencia_objetivo=1, repo=repo)
    habitos_service.crear_habito(db, usuario_id=1, nombre="Habito 2 U1", frecuencia_objetivo=2, repo=repo)
    habitos_service.crear_habito(db, usuario_id=2, nombre="Habito 1 U2", frecuencia_objetivo=3, repo=repo)

    lista_u1 = habitos_service.listar_habitos(db, usuario_id=1, repo=repo)
    assert len(lista_u1) == 2
    assert all(h["usuario_id"] == 1 for h in lista_u1)


# ---------------------------------------------------------------------------
# Actualización, eliminación y listado de registros
# ---------------------------------------------------------------------------
def test_actualizar_y_eliminar_habito():
    repo = RepositorioFalsoHabitos()
    db = None

    h = habitos_service.crear_habito(db, usuario_id=1, nombre="Caminar", frecuencia_objetivo=4, repo=repo)

    act = habitos_service.actualizar_habito(
        db, usuario_id=1, habito_id=h["id"], nombre="Caminar Rápido", frecuencia_objetivo=5, repo=repo
    )
    assert act["nombre"] == "Caminar Rápido"
    assert act["frecuencia_objetivo"] == 5

    res = habitos_service.eliminar_habito(db, usuario_id=1, habito_id=h["id"], repo=repo)
    assert res is True
    assert len(habitos_service.listar_habitos(db, usuario_id=1, repo=repo)) == 0


def test_listar_registros_orden_y_pertenencia():
    repo = RepositorioFalsoHabitos()
    db = None

    h = habitos_service.crear_habito(db, usuario_id=1, nombre="Dibujar", frecuencia_objetivo=3, repo=repo)
    d1 = date.today() - timedelta(days=2)
    d2 = date.today() - timedelta(days=1)

    habitos_service.marcar_habito(db, usuario_id=1, habito_id=h["id"], fecha=d1, repo=repo)
    habitos_service.marcar_habito(db, usuario_id=1, habito_id=h["id"], fecha=d2, repo=repo)

    regs = habitos_service.listar_registros(db, usuario_id=1, habito_id=h["id"], repo=repo)
    assert len(regs) == 2
    assert regs[0]["fecha"] == d2  # Orden descendente

    with pytest.raises(HabitoAjenoError):
        habitos_service.listar_registros(db, usuario_id=2, habito_id=h["id"], repo=repo)
