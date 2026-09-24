from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.database import Base
from app.repositories.usuarios import crear_usuario, obtener_por_email, obtener_por_id


def test_usuarios_repository_returns_dict():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        user_dict = crear_usuario(session, "test@correo.com", "hash123")
        assert isinstance(user_dict, dict), "Repository debe retornar dict según Artículo I.3"
        assert user_dict["email"] == "test@correo.com"
        assert user_dict["id"] is not None

        by_email = obtener_por_email(session, "test@correo.com")
        assert isinstance(by_email, dict)
        assert by_email["id"] == user_dict["id"]

        by_id = obtener_por_id(session, user_dict["id"])
        assert isinstance(by_id, dict)
        assert by_id["email"] == "test@correo.com"

        assert obtener_por_email(session, "inexistente@correo.com") is None
