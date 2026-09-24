import json
import pytest
from mcp.server.fastmcp import FastMCP
from app.mcp.tools.habitos import registrar_tools
from app.database import Base, SessionLocal, engine
from app.models.usuario import Usuario
from app.models.habito import Habito, RegistroHabito


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        # Limpiar datos anteriores
        db.query(RegistroHabito).delete()
        db.query(Habito).delete()
        db.query(Usuario).delete()
        db.commit()
    yield


@pytest.fixture
def mcp_app():
    test_mcp = FastMCP(name="TestMCP")
    registrar_tools(test_mcp)
    return test_mcp


@pytest.mark.asyncio
async def test_mcp_publica_4_tools_con_descripciones_de_3_partes(mcp_app):
    tools = await mcp_app.list_tools()
    tool_names = [t.name for t in tools]

    assert "crear_habito" in tool_names
    assert "listar_habitos" in tool_names
    assert "marcar_habito" in tool_names
    assert "eliminar_habito" in tool_names

    for t in tools:
        assert "Qué hace:" in t.description, f"{t.name} debe tener sección 'Qué hace:' (Artículo VI.2)"
        assert "Cuándo usarla:" in t.description, f"{t.name} debe tener sección 'Cuándo usarla:' (Artículo VI.2)"
        assert "Cuándo no usarla:" in t.description, f"{t.name} debe tener sección 'Cuándo no usarla:' (Artículo VI.2)"


@pytest.mark.asyncio
async def test_mcp_crear_habito_exito_y_error_negocio(mcp_app):
    # Caso exitoso
    res_exito = await mcp_app.call_tool("crear_habito", {"nombre": "Leer 20 mins", "frecuencia_objetivo": 5})
    assert res_exito is not None
    texto_exito = str(res_exito)
    assert "Leer 20 mins" in texto_exito or "id" in texto_exito

    # Caso de error de negocio (R1: nombre corto)
    res_error = await mcp_app.call_tool("crear_habito", {"nombre": "a", "frecuencia_objetivo": 5})
    assert res_error is not None
    texto_error = str(res_error)
    assert "error" in texto_error.lower() or "caracteres" in texto_error.lower()


@pytest.mark.asyncio
async def test_mcp_listar_marcar_y_eliminar_confirmado(mcp_app):
    # Crear hábito
    res_crear = await mcp_app.call_tool("crear_habito", {"nombre": "Rutina Mañana", "frecuencia_objetivo": 7})
    if isinstance(res_crear, list) and hasattr(res_crear[0], "text"):
        creado = json.loads(res_crear[0].text)
    elif isinstance(res_crear, dict):
        creado = res_crear
    else:
        creado = json.loads(str(res_crear))
    habito_id = creado["id"]

    # Listar
    lista = await mcp_app.call_tool("listar_habitos", {"skip": 0, "limit": 10})
    assert "Rutina Mañana" in str(lista)

    # Marcar hábito
    marca = await mcp_app.call_tool("marcar_habito", {"habito_id": habito_id})
    assert marca is not None

    # Error en marcar repetido hoy (R4)
    marca_dup = await mcp_app.call_tool("marcar_habito", {"habito_id": habito_id})
    assert "error" in str(marca_dup).lower() or "marcado" in str(marca_dup).lower()

    # Eliminar con confirmación
    res_elim = await mcp_app.call_tool("eliminar_habito", {"habito_id": habito_id, "confirmar": True})
    assert "eliminado" in str(res_elim).lower()
