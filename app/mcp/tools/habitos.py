from typing import Any
from mcp.server.fastmcp import Context, FastMCP

from app.config import settings
from app.database import SessionLocal
from app.repositories import habitos as habitos_repo
from app.repositories import usuarios as usuarios_repo
from app.services import habitos as habitos_service
from app.services.errores import ErrorDeDominio


def _resolver_usuario_id(ctx: Context | None = None) -> int:
    """
    Artículo VI.4:
    - En transporte streamable-http, extrae el usuario_id del token JWT verificado en la sesión.
    - Simplificación consciente documentada: En transporte stdio (o cuando no hay token verificado
      en el contexto de la sesión), se recurre al usuario demo configurado en .env.
    """
    # Intentar resolver desde claims del token verificado en contexto
    if ctx is not None:
        try:
            client_id = getattr(ctx, "client_id", None)
            if client_id:
                return int(client_id)
        except Exception:
            pass

    # Respaldo legítimo: buscar el usuario demo configurado
    with SessionLocal() as db:
        demo_user = usuarios_repo.obtener_por_email(db, settings.DEMO_USER_EMAIL)
        if demo_user:
            return demo_user["id"]
        # Si aún no existe el usuario demo, crear uno base
        nuevo_demo = usuarios_repo.crear_usuario(
            db, email=settings.DEMO_USER_EMAIL, hashed_password="demo_hashed_password"
        )
        return nuevo_demo["id"]


def registrar_tools(mcp: FastMCP):
    """Registra los 4 tools de hábitos en la instancia FastMCP (Artículo VI)."""

    @mcp.tool(
        name="crear_habito",
        description=(
            "Qué hace: Crea un nuevo hábito personal con nombre y frecuencia semanal objetivo.\n"
            "Cuándo usarla: Cuando el usuario exprese la intención de registrar un hábito nuevo a sostener.\n"
            "Cuándo no usarla: No usar si se desea marcar cumplimiento de un hábito ya existente o modificarlo."
        ),
    )
    async def crear_habito(nombre: str, frecuencia_objetivo: int, ctx: Context = None) -> dict:
        usuario_id = _resolver_usuario_id(ctx)
        try:
            with SessionLocal() as db:
                return habitos_service.crear_habito(
                    db=db,
                    usuario_id=usuario_id,
                    nombre=nombre,
                    frecuencia_objetivo=frecuencia_objetivo,
                    repo=habitos_repo,
                )
        except ErrorDeDominio as exc:
            return {"error": exc.mensaje}

    @mcp.tool(
        name="listar_habitos",
        description=(
            "Qué hace: Lista todos los hábitos personales registrados pertenecientes al usuario actual.\n"
            "Cuándo usarla: Cuando el usuario consulte qué hábitos tiene registrados o requiera ver su listado.\n"
            "Cuándo no usarla: No usar si se necesita ver el historial de fechas de un hábito específico."
        ),
    )
    async def listar_habitos(skip: int = 0, limit: int = 20, ctx: Context = None) -> list[dict] | dict:
        usuario_id = _resolver_usuario_id(ctx)
        try:
            with SessionLocal() as db:
                return habitos_service.listar_habitos(
                    db=db,
                    usuario_id=usuario_id,
                    skip=skip,
                    limit=limit,
                    repo=habitos_repo,
                )
        except ErrorDeDominio as exc:
            return {"error": exc.mensaje}

    @mcp.tool(
        name="marcar_habito",
        description=(
            "Qué hace: Registra el cumplimiento de un hábito en una fecha dada o en el día de hoy.\n"
            "Cuándo usarla: Cuando el usuario indique que cumplió o realizó un hábito existente.\n"
            "Cuándo no usarla: No usar para crear un hábito nuevo ni para marcar en fechas futuras (R5)."
        ),
    )
    async def marcar_habito(habito_id: int, fecha: str | None = None, ctx: Context = None) -> dict:
        usuario_id = _resolver_usuario_id(ctx)
        try:
            with SessionLocal() as db:
                return habitos_service.marcar_habito(
                    db=db,
                    usuario_id=usuario_id,
                    habito_id=habito_id,
                    fecha=fecha,
                    repo=habitos_repo,
                )
        except ErrorDeDominio as exc:
            return {"error": exc.mensaje}

    @mcp.tool(
        name="eliminar_habito",
        description=(
            "Qué hace: Elimina definitivamente un hábito personal y todo su historial de registros.\n"
            "Cuándo usarla: Cuando el usuario solicite explícitamente borrar o dar de baja un hábito.\n"
            "Cuándo no usarla: No usar para desactivar temporalmente un hábito sin borrarlo."
        ),
    )
    async def eliminar_habito(habito_id: int, confirmar: bool = False, ctx: Context = None) -> dict:
        """
        Artículo VI.5: Operación destructiva que exige confirmación explícita.
        """
        if not confirmar:
            # Si ctx soporta elicit, se solicita confirmación interactiva
            if ctx is not None and hasattr(ctx, "elicit"):
                try:
                    respuesta = await ctx.elicit(
                        f"¿Está seguro de que desea eliminar permanentemente el hábito ID {habito_id} y todos sus registros?"
                    )
                    if not respuesta:
                        return {"error": "Operación de eliminación cancelada por el usuario"}
                except Exception:
                    return {"error": "Se requiere confirmación explícita: envíe confirmar=True para proceder"}
            else:
                return {"error": "Se requiere confirmación explícita: envíe confirmar=True para proceder"}

        usuario_id = _resolver_usuario_id(ctx)
        try:
            with SessionLocal() as db:
                habitos_service.eliminar_habito(
                    db=db,
                    usuario_id=usuario_id,
                    habito_id=habito_id,
                    repo=habitos_repo,
                )
                return {"mensaje": "Hábito eliminado correctamente"}
        except ErrorDeDominio as exc:
            return {"error": exc.mensaje}
