from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.database import Base
from app.models.usuario import Usuario
from app.models.habito import Habito, RegistroHabito


def test_models_creation_and_relations():
    # SQLite en memoria para test unitario de modelos
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        user = Usuario(email="test@user.com", hashed_password="fakehash123")
        session.add(user)
        session.commit()
        session.refresh(user)

        assert user.id is not None
        assert user.email == "test@user.com"

        habito = Habito(
            usuario_id=user.id,
            nombre="Lectura",
            nombre_normalizado="lectura",
            frecuencia_objetivo=5,
        )
        session.add(habito)
        session.commit()
        session.refresh(habito)

        assert habito.id is not None
        assert habito.usuario.email == "test@user.com"

        reg = RegistroHabito(habito_id=habito.id, fecha=date(2026, 9, 23))
        session.add(reg)
        session.commit()
        session.refresh(reg)

        assert reg.id is not None
        assert reg.habito.nombre == "Lectura"
