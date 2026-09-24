from datetime import date, datetime, timezone
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Habito(Base):
    """Modelo ORM para hábitos pertenecientes a un usuario."""

    __tablename__ = "habitos"

    __table_args__ = (
        UniqueConstraint("usuario_id", "nombre_normalizado", name="uq_usuario_habito_nombre"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    nombre_normalizado: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    frecuencia_objetivo: Mapped[int] = mapped_column(Integer, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    usuario = relationship("Usuario", back_populates="habitos")
    registros = relationship("RegistroHabito", back_populates="habito", cascade="all, delete-orphan")


class RegistroHabito(Base):
    """Modelo ORM para marcas de cumplimiento de un hábito."""

    __tablename__ = "registros_habitos"

    __table_args__ = (
        UniqueConstraint("habito_id", "fecha", name="uq_habito_fecha_registro"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    habito_id: Mapped[int] = mapped_column(Integer, ForeignKey("habitos.id", ondelete="CASCADE"), nullable=False, index=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    habito = relationship("Habito", back_populates="registros")
