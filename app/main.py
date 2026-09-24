import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.routers.habitos import router as habitos_router
from app.routers.usuarios import router as usuarios_router

# Configuración básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

app = FastAPI(
    title="Seguimiento de Hábitos API",
    description="API REST y Servidor MCP para seguimiento personal de hábitos",
    version="1.0.0",
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


@app.get("/health", tags=["Salud"])
def health_check():
    return {"status": "ok"}
