class ErrorDeDominio(Exception):
    """Excepción base para todos los errores de regla de negocio y dominio."""
    def __init__(self, mensaje: str):
        super().__init__(mensaje)
        self.mensaje = mensaje


# Reglas de Hábitos R1 a R6
class NombreInvalidoError(ErrorDeDominio):
    """R1: El nombre no puede estar vacío ni tener menos de 3 caracteres útiles."""
    pass


class FrecuenciaInvalidaError(ErrorDeDominio):
    """R2: La frecuencia objetivo debe ser un entero entre 1 y 7."""
    pass


class HabitoDuplicadoError(ErrorDeDominio):
    """R3: Un usuario no puede tener dos hábitos con el mismo nombre normalizado."""
    pass


class YaMarcadoHoyError(ErrorDeDominio):
    """R4: Un hábito no puede marcarse dos veces en la misma fecha."""
    pass


class FechaFuturaError(ErrorDeDominio):
    """R5: No se puede marcar un hábito en una fecha futura."""
    pass


class HabitoAjenoError(ErrorDeDominio):
    """R6: El hábito existe pero pertenece a otro usuario."""
    pass


class HabitoNoEncontradoError(ErrorDeDominio):
    """R6: El hábito solicitado no existe."""
    pass


# Errores de Usuarios
class EmailDuplicadoError(ErrorDeDominio):
    """El email ya se encuentra registrado por otro usuario."""
    pass


class CredencialesInvalidasError(ErrorDeDominio):
    """Email inexistente o contraseña incorrecta."""
    pass


class UsuarioNoEncontradoError(ErrorDeDominio):
    """El usuario solicitado no existe."""
    pass
