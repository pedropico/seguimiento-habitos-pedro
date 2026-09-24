from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.database import Base
from app.models.usuario import Usuario
from app.repositories import habitos as habitos_repo


def test_repositorio_habitos_crud_y_registros():
    # SQLite en memoria con StaticPool para test de integración
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        user1 = Usuario(email="u1@test.com", hashed_password="hash")
        user2 = Usuario(email="u2@test.com", hashed_password="hash")
        session.add_all([user1, user2])
        session.commit()
        session.refresh(user1)
        session.refresh(user2)

        # 1. Crear hábito
        h1 = habitos_repo.crear(session, user1.id, "Leer", "leer", 5)
        assert isinstance(h1, dict)
        assert h1["nombre"] == "Leer"
        assert h1["usuario_id"] == user1.id

        # 2. Listar filtra por usuario_id (Artículo III.3)
        h2 = habitos_repo.crear(session, user2.id, "Correr", "correr", 3)
        lista_u1 = habitos_repo.listar(session, user1.id)
        assert len(lista_u1) == 1
        assert lista_u1[0]["id"] == h1["id"]

        # 3. Obtener no filtra por usuario_id (para permitir verificación de pertenencia en services)
        obtenido = habitos_repo.obtener(session, h1["id"])
        assert obtenido is not None
        assert obtenido["usuario_id"] == user1.id

        # 4. Buscar por nombre normalizado
        encontrado = habitos_repo.buscar_por_nombre(session, user1.id, "leer")
        assert encontrado is not None
        assert encontrado["id"] == h1["id"]

        # 5. Actualizar
        act = habitos_repo.actualizar(session, h1["id"], nombre="Leer Más", frecuencia_objetivo=6)
        assert act["nombre"] == "Leer Más"
        assert act["frecuencia_objetivo"] == 6

        # 6. Registros de cumplimiento
        hoy = date(2026, 9, 23)
        assert not habitos_repo.existe_registro(session, h1["id"], hoy)
        reg = habitos_repo.guardar_registro(session, h1["id"], hoy)
        assert isinstance(reg, dict)
        assert reg["fecha"] == hoy
        assert habitos_repo.existe_registro(session, h1["id"], hoy)

        regs = habitos_repo.listar_registros(session, h1["id"])
        assert len(regs) == 1
        assert regs[0]["id"] == reg["id"]

        # 7. Eliminar hábito y cascada
        eliminado = habitos_repo.eliminar(session, h1["id"])
        assert eliminado is True
        assert habitos_repo.obtener(session, h1["id"]) is None
        assert len(habitos_repo.listar_registros(session, h1["id"])) == 0
