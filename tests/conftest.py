"""
1. Aislamiento: los tests NUNCA usan la base real (habitos.db).
2. Trazabilidad spec.md -> tests (SC-001).

Al final de cada `pytest` imprime qué tests cubren cada regla de negocio
R[N] de specs/001-seguimiento-habitos/spec.md, identificados por la
convención de nombre `test_R[N]_...`. Si una regla del spec no tiene
ningún test, la ejecución termina con error.
"""

import os
import re
import tempfile
from pathlib import Path

# Debe ejecutarse antes de importar `app`: las variables de entorno tienen
# prioridad sobre .env, así que app.database crea el engine sobre este archivo
# temporal y los fixtures que limpian tablas no borran los datos del desarrollador.
_DB_TESTS = Path(tempfile.gettempdir()) / f"habitos_tests_{os.getpid()}.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_TESTS.as_posix()}"

SPEC = Path(__file__).resolve().parent.parent / "specs" / "001-seguimiento-habitos" / "spec.md"
_PATRON_REGLA_SPEC = re.compile(r"^\|\s*\*\*(R\d+)\*\*\s*\|\s*(.+?)\s*\|", re.MULTILINE)
_PATRON_TEST = re.compile(r"^test_(R\d+)_")

_resultados: dict[str, str] = {}  # nodeid -> passed/failed/skipped


def _reglas_del_spec() -> dict[str, str]:
    """Lee la tabla de reglas de negocio del spec: {"R1": "El nombre de...", ...}."""
    return {rid: desc for rid, desc in _PATRON_REGLA_SPEC.findall(SPEC.read_text(encoding="utf-8"))}


def pytest_runtest_logreport(report):
    # Un fallo en setup/teardown también cuenta como fallo del test.
    if report.when == "call" or report.outcome != "passed":
        if _resultados.get(report.nodeid) != "failed":
            _resultados[report.nodeid] = report.outcome


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    reglas = _reglas_del_spec()
    if not reglas:
        return

    cobertura: dict[str, list[tuple[str, str]]] = {rid: [] for rid in reglas}
    for nodeid, estado in _resultados.items():
        nombre = nodeid.split("::")[-1]
        m = _PATRON_TEST.match(nombre)
        if m and m.group(1) in cobertura:
            cobertura[m.group(1)].append((nombre, estado))

    completa = _es_suite_completa(config)
    if not completa and not any(cobertura.values()):
        return  # ejecución parcial sin tests de reglas: nada que reportar

    tr = terminalreporter
    tr.section("Trazabilidad spec.md -> tests (SC-001)" + ("" if completa else " — ejecución parcial"))
    iconos = {"passed": "PASS", "failed": "FAIL", "skipped": "SKIP"}
    sin_test = []
    for rid, descripcion in reglas.items():
        tests = cobertura[rid]
        if not completa and not tests:
            continue
        descripcion = descripcion.replace("**", "").replace("`", "")
        resumen = descripcion if len(descripcion) <= 70 else descripcion[:67] + "..."
        estado_regla = "SIN TEST" if not tests else ("OK" if all(e == "passed" for _, e in tests) else "FALLA")
        tr.write_line(f"{rid} [{estado_regla}] {resumen}", bold=True, red=estado_regla != "OK", green=estado_regla == "OK")
        for nombre, estado in sorted(tests):
            tr.write_line(f"    {iconos.get(estado, estado):<4} {nombre}")
        if not tests:
            sin_test.append(rid)

    if not completa:
        return
    cubiertas = len(reglas) - len(sin_test)
    tr.write_line(f"\nReglas cubiertas: {cubiertas}/{len(reglas)}", bold=True)
    if sin_test:
        tr.write_line(f"Reglas del spec sin test identificable: {', '.join(sin_test)}", red=True, bold=True)


def _es_suite_completa(config) -> bool:
    """`pytest` sin argumentos (usa testpaths) y sin filtros -k / -m."""
    return (
        config.args_source == config.ArgsSource.TESTPATHS
        and not config.option.keyword
        and not config.option.markexpr
    )


def pytest_sessionstart(session):
    """Crea el esquema en la base temporal (la real ya lo tiene vía Alembic)."""
    from app.database import Base, engine
    import app.models.habito  # noqa: F401  registra los modelos en Base.metadata
    import app.models.usuario  # noqa: F401

    Base.metadata.create_all(engine)


def _borrar_db_tests() -> None:
    from app.database import engine

    engine.dispose()  # en Windows el archivo queda bloqueado mientras haya conexiones
    _DB_TESTS.unlink(missing_ok=True)


def pytest_sessionfinish(session, exitstatus):
    _borrar_db_tests()
    if not _es_suite_completa(session.config):
        return
    reglas = set(_reglas_del_spec())
    con_test = {m.group(1) for n in _resultados if (m := _PATRON_TEST.match(n.split("::")[-1]))}
    if reglas - con_test:
        session.exitstatus = 1
