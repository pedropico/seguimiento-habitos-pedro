import re


def normalizar_nombre(texto: str) -> str:
    """
    Función pura para normalizar nombres de hábitos:
    - Descarta espacios al inicio y final.
    - Colapsa espacios múltiples consecutivos en uno solo.
    - Convierte a minúsculas para comparaciones insensibles a mayúsculas.
    """
    if not texto:
        return ""
    limpio = re.sub(r"\s+", " ", texto.strip())
    return limpio.lower()


def limpiar_nombre_para_mostrar(texto: str) -> str:
    """
    Función pura para limpiar el nombre preservando mayúsculas y formato legible,
    pero eliminando espacios sobrantes.
    """
    if not texto:
        return ""
    return re.sub(r"\s+", " ", texto.strip())
