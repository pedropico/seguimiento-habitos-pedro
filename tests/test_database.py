from sqlalchemy import inspect
from app.database import Base, engine


def test_tables_created():
    Base.metadata.create_all(engine)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "usuarios" in tables
    assert "habitos" in tables
    assert "registros_habitos" in tables
