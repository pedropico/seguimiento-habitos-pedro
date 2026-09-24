import pytest
from pydantic import ValidationError
from app.schemas.usuario import UsuarioCreate, UsuarioOut
from app.schemas.habito import HabitoCreate, HabitoOut


def test_usuario_create_schema():
    u = UsuarioCreate(email="test@user.com", password="password123")
    assert u.email == "test@user.com"
    assert u.password == "password123"

    with pytest.raises(ValidationError):
        UsuarioCreate(email="invalido", password="password123")


def test_habito_create_schema_ignores_or_forbids_usuario_id():
    h = HabitoCreate(nombre="Ejercicio", frecuencia_objetivo=4)
    assert h.nombre == "Ejercicio"
    assert h.frecuencia_objetivo == 4
    assert not hasattr(h, "usuario_id") or "usuario_id" not in h.model_fields
