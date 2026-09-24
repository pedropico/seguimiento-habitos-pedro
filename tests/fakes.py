from datetime import date, datetime, timezone


class RepositorioFalsoUsuarios:
    """Implementación falsa en memoria del repositorio de usuarios."""

    def __init__(self):
        self.usuarios: list[dict] = []
        self._next_id = 1

    def crear_usuario(self, db, email: str, hashed_password: str) -> dict:
        usuario = {
            "id": self._next_id,
            "email": email,
            "hashed_password": hashed_password,
            "fecha_creacion": datetime.now(timezone.utc),
        }
        self._next_id += 1
        self.usuarios.append(usuario)
        return dict(usuario)

    def obtener_por_email(self, db, email: str) -> dict | None:
        for u in self.usuarios:
            if u["email"] == email:
                return dict(u)
        return None

    def obtener_por_id(self, db, usuario_id: int) -> dict | None:
        for u in self.usuarios:
            if u["id"] == usuario_id:
                return dict(u)
        return None


class RepositorioFalsoHabitos:
    """Implementación falsa en memoria del repositorio de hábitos."""

    def __init__(self):
        self.habitos: list[dict] = []
        self.registros: list[dict] = []
        self._next_habito_id = 1
        self._next_registro_id = 1

    def crear(
        self,
        db,
        usuario_id: int,
        nombre: str,
        nombre_normalizado: str,
        frecuencia_objetivo: int,
    ) -> dict:
        habito = {
            "id": self._next_habito_id,
            "usuario_id": usuario_id,
            "nombre": nombre,
            "nombre_normalizado": nombre_normalizado,
            "frecuencia_objetivo": frecuencia_objetivo,
            "activo": True,
            "fecha_creacion": datetime.now(timezone.utc),
        }
        self._next_habito_id += 1
        self.habitos.append(habito)
        return dict(habito)

    def listar(self, db, usuario_id: int, skip: int = 0, limit: int = 20) -> list[dict]:
        filtrados = [dict(h) for h in self.habitos if h["usuario_id"] == usuario_id]
        return filtrados[skip : skip + limit]

    def obtener(self, db, habito_id: int) -> dict | None:
        for h in self.habitos:
            if h["id"] == habito_id:
                return dict(h)
        return None

    def buscar_por_nombre(self, db, usuario_id: int, nombre_normalizado: str) -> dict | None:
        for h in self.habitos:
            if h["usuario_id"] == usuario_id and h["nombre_normalizado"] == nombre_normalizado:
                return dict(h)
        return None

    def actualizar(self, db, habito_id: int, **kwargs) -> dict | None:
        for h in self.habitos:
            if h["id"] == habito_id:
                for k, v in kwargs.items():
                    if v is not None:
                        h[k] = v
                return dict(h)
        return None

    def eliminar(self, db, habito_id: int) -> bool:
        for i, h in enumerate(self.habitos):
            if h["id"] == habito_id:
                self.habitos.pop(i)
                self.registros = [r for r in self.registros if r["habito_id"] != habito_id]
                return True
        return False

    def existe_registro(self, db, habito_id: int, fecha: date) -> bool:
        for r in self.registros:
            if r["habito_id"] == habito_id and r["fecha"] == fecha:
                return True
        return False

    def guardar_registro(self, db, habito_id: int, fecha: date) -> dict:
        registro = {
            "id": self._next_registro_id,
            "habito_id": habito_id,
            "fecha": fecha,
            "fecha_registro": datetime.now(timezone.utc),
        }
        self._next_registro_id += 1
        self.registros.append(registro)
        return dict(registro)

    def listar_registros(self, db, habito_id: int, skip: int = 0, limit: int = 50) -> list[dict]:
        filtrados = [dict(r) for r in self.registros if r["habito_id"] == habito_id]
        filtrados.sort(key=lambda x: (x["fecha"], x["id"]), reverse=True)
        return filtrados[skip : skip + limit]
