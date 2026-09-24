from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UsuarioCreate(BaseModel):
    """Esquema de entrada para registro de usuarios."""
    email: EmailStr
    password: str = Field(min_length=6, description="Contraseña en texto plano a ser hasheada")


class UsuarioOut(BaseModel):
    """Esquema de salida para datos de usuario (nunca expone hashed_password)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    fecha_creacion: datetime


class Token(BaseModel):
    """Esquema de respuesta para token de autenticación JWT."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Datos extraídos del token decodificado."""
    usuario_id: int | None = None
    email: str | None = None
