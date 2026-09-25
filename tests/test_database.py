from pathlib import Path

from sqlalchemy import inspect
from app.database import Base, engine


def test_los_tests_no_usan_la_base_real():
    """conftest.py redirige DATABASE_URL: ningún test debe tocar habitos.db."""
    assert Path(engine.url.database).name != "habitos.db"


def test_tables_created():
    Base.metadata.create_all(engine)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "usuarios" in tables
    assert "habitos" in tables
    assert "registros_habitos" in tables
