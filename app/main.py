import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.mcp.server import crear_servidor_mcp
from app.routers.habitos import router as habitos_router
from app.routers.usuarios import router as usuarios_router

# Configuración básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")


class _MCPMontado:
    """
    ASGI montado en /mcp que delega en el servidor MCP creado en cada arranque.
    El session manager de streamable-http solo arranca una vez por instancia,
    así que el lifespan crea una nueva y la conecta aquí.
    """

    def __init__(self):
        self.asgi = None

    async def __call__(self, scope, receive, send):
        if self.asgi is None:
            response = JSONResponse({"detail": "Servidor MCP no iniciado"}, status_code=503)
            await response(scope, receive, send)
            return
        await self.asgi(scope, receive, send)


mcp_montado = _MCPMontado()


@asynccontextmanager
async def lifespan(app: FastAPI):
    servidor = crear_servidor_mcp()
    mcp_montado.asgi = servidor.streamable_http_app()
    async with servidor.session_manager.run():
        yield
    mcp_montado.asgi = None


app = FastAPI(
    title="Seguimiento de Hábitos API",
    description="API REST y Servidor MCP para seguimiento personal de hábitos",
    version="1.0.0",
    lifespan=lifespan,
)


# Artículo IV.5: Manejador global de excepciones no controladas
@app.exception_handler(Exception)
async def error_no_controlado(request: Request, exc: Exception):
    logger.error("Error no controlado capturado: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error interno del servidor"},
    )


# Inclusión de routers de negocio
app.include_router(usuarios_router)
app.include_router(habitos_router)

# Artículo VI: MCP vía streamable-http, protegido con el mismo JWT de REST
app.mount("/mcp", mcp_montado)


@app.get("/health", tags=["Salud"])
def health_check():
    return {"status": "ok"}
