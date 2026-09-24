from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field


class HabitoCreate(BaseModel):
    """
    Esquema de entrada para creación de hábitos.
    Artículo IV.4: usuario_id NO se acepta en el body, se extrae del JWT.
    """
    nombre: str = Field(min_length=1, max_length=100, description="Nombre del hábito")
    frecuencia_objetivo: int = Field(description="Frecuencia semanal objetivo (1-7)")


class HabitoUpdate(BaseModel):
    """Esquema para actualización parcial de un hábito."""
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    frecuencia_objetivo: int | None = None
    activo: bool | None = None


class HabitoOut(BaseModel):
    """Esquema de salida de hábito."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    frecuencia_objetivo: int
    activo: bool
    fecha_creacion: datetime | str | None = None


class RegistroCreate(BaseModel):
    """Esquema de entrada para marcar hábito."""
    fecha: date | None = Field(default=None, description="Fecha de cumplimiento (default: hoy)")


class RegistroOut(BaseModel):
    """Esquema de salida para un registro de hábito."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    habito_id: int
    fecha: date | str
    fecha_registro: datetime | str | None = None
