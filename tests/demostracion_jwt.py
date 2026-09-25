"""
Demostración de Auth + JWT (Artículo IV.2 y IV.4)
=================================================
Parte A — Cómo funciona el JWT de la app y por qué no se puede adulterar.
Parte B — Qué pasaría si un endpoint NO verificara el JWT (endpoints
          vulnerables construidos SOLO dentro de este script, nunca en app/).

Usa repositorios en memoria (tests/fakes.py): no toca habitos.db.
Ejecutar: uv run python tests/demostracion_jwt.py
"""

import base64
import json
import logging
import sys
import warnings
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")  # claves cortas de los atacantes y deprecations de httpx
logging.getLogger("httpx").setLevel(logging.WARNING)

import jwt
from fastapi import FastAPI, Header
from fastapi.testclient import TestClient

from app.config import settings
from app.dependencies import get_db, get_habitos_repo, get_usuarios_repo
from app.main import app
from app.security import ALGORITHM, crear_token_acceso
from app.services import habitos as habitos_service
from tests.fakes import RepositorioFalsoHabitos, RepositorioFalsoUsuarios

repo_usuarios = RepositorioFalsoUsuarios()
repo_habitos = RepositorioFalsoHabitos()


def titulo(texto: str) -> None:
    print("\n" + "=" * 78)
    print(f"  {texto}")
    print("=" * 78)


def resultado(etiqueta: str, resp) -> None:
    print(f"  {etiqueta:<52} -> HTTP {resp.status_code}")


def decodificar_sin_verificar(token: str) -> tuple[dict, dict]:
    """Un JWT es header.payload.firma en base64url: cualquiera puede LEERLO."""
    def b64(parte: str) -> dict:
        return json.loads(base64.urlsafe_b64decode(parte + "=" * (-len(parte) % 4)))
    header, payload, _ = token.split(".")
    return b64(header), b64(payload)


def preparar_escenario(client: TestClient) -> tuple[str, int]:
    """Registra a Alice (víctima) y Bob (atacante); Alice crea un hábito privado."""
    for email, pw in [("alice@demo.com", "Alice123!"), ("bob@demo.com", "Bob12345!")]:
        client.post("/usuarios/", json={"email": email, "password": pw})
    tok_alice = client.post(
        "/usuarios/token", data={"username": "alice@demo.com", "password": "Alice123!"}
    ).json()["access_token"]
    client.post(
        "/habitos/",
        json={"nombre": "Tomar medicación psiquiátrica", "frecuencia_objetivo": 7},
        headers={"Authorization": f"Bearer {tok_alice}"},
    )
    return tok_alice, 1  # Alice es el usuario id=1


def parte_a(client: TestClient) -> None:
    titulo("PARTE A — Auth + JWT en la app real")

    print("\n[A1] Login de Bob -> la app emite un JWT firmado con SECRET_KEY (HS256)")
    tok_bob = client.post(
        "/usuarios/token", data={"username": "bob@demo.com", "password": "Bob12345!"}
    ).json()["access_token"]
    header, payload = decodificar_sin_verificar(tok_bob)
    print(f"  token  : {tok_bob[:40]}...")
    print(f"  header : {header}")
    print(f"  payload: {payload}")
    print("  OJO: el payload es legible por cualquiera (base64, no cifrado).")
    print("       Lo que lo protege es la FIRMA, no el secreto del contenido.")

    h_bob = {"Authorization": f"Bearer {tok_bob}"}
    print("\n[A2] Uso legítimo")
    resultado("GET /habitos/ con token de Bob", client.get("/habitos/", headers=h_bob))
    print(f"  Bob ve {len(client.get('/habitos/', headers=h_bob).json())} hábitos (los de Alice no aparecen)")

    print("\n[A3] Ataques contra la app real (todos deben fallar)")
    resultado("Sin cabecera Authorization", client.get("/habitos/"))

    # Bob edita el payload (sub=1 -> Alice) pero conserva su firma original
    h64, _, firma = tok_bob.split(".")
    payload_alice = dict(payload, sub="1")
    p64 = base64.urlsafe_b64encode(json.dumps(payload_alice).encode()).rstrip(b"=").decode()
    tok_editado = f"{h64}.{p64}.{firma}"
    resultado("Payload editado a sub=1 (firma de Bob)",
              client.get("/habitos/", headers={"Authorization": f"Bearer {tok_editado}"}))

    tok_otra_clave = jwt.encode({"sub": "1"}, "clave-que-adivino-el-atacante", algorithm=ALGORITHM)
    resultado("Firmado con otra clave",
              client.get("/habitos/", headers={"Authorization": f"Bearer {tok_otra_clave}"}))

    tok_none = jwt.encode({"sub": "1"}, key=None, algorithm="none")
    resultado("alg=none (sin firma)",
              client.get("/habitos/", headers={"Authorization": f"Bearer {tok_none}"}))

    tok_expirado = crear_token_acceso({"sub": "2"}, expires_delta=timedelta(seconds=-1))
    resultado("Token expirado",
              client.get("/habitos/", headers={"Authorization": f"Bearer {tok_expirado}"}))

    tok_sin_usuario = crear_token_acceso({"sub": "999"})
    resultado("Firma válida pero usuario inexistente (sub=999)",
              client.get("/habitos/", headers={"Authorization": f"Bearer {tok_sin_usuario}"}))

    print("\n[A4] ¿Y si la SECRET_KEY se filtra? (la firma solo vale si la clave es secreta)")
    clave_publica = next(
        linea.split("=", 1)[1].strip()
        for linea in Path(".env.example").read_text(encoding="utf-8").splitlines()
        if linea.startswith("SECRET_KEY=")
    )
    tok_forjado = jwt.encode({"sub": "1"}, clave_publica, algorithm=ALGORITHM)
    resp = client.get("/habitos/", headers={"Authorization": f"Bearer {tok_forjado}"})
    resultado("JWT forjado con la clave de .env.example (sub=1)", resp)
    if resp.status_code == 200:
        print(f"  !! VULNERABLE: tu SECRET_KEY es la de .env.example. Bob lee: {resp.json()}")
        print("     Genera una nueva: python -c \"import secrets; print(secrets.token_hex(32))\"")
    else:
        print("  OK: tu SECRET_KEY no es la publicada en el repo.")


def crear_app_vulnerable() -> FastAPI:
    """
    Endpoints INSEGUROS a propósito, solo para la demostración.
    Reutilizan el mismo service y los mismos datos que la app real:
    la única diferencia es de dónde sale el usuario_id.
    """
    vuln = FastAPI()

    @vuln.get("/v1/habitos")
    def confia_en_parametro(usuario_id: int):
        # ERROR 1: el cliente dice quién es (?usuario_id=...). No hay auth.
        return habitos_service.listar_habitos(None, usuario_id=usuario_id, repo=repo_habitos)

    @vuln.get("/v2/habitos")
    def decodifica_sin_verificar_firma(authorization: str = Header()):
        # ERROR 2: exige un JWT, pero lo decodifica sin verificar la firma.
        token = authorization.removeprefix("Bearer ")
        payload = jwt.decode(token, options={"verify_signature": False})
        return habitos_service.listar_habitos(None, usuario_id=int(payload["sub"]), repo=repo_habitos)

    return vuln


def parte_b(tok_alice: str) -> None:
    titulo("PARTE B — ¿Qué pasa si un endpoint NO verifica el JWT?")
    vuln = TestClient(crear_app_vulnerable())

    print("\n[B1] Endpoint que acepta usuario_id como parámetro")
    resp = vuln.get("/v1/habitos", params={"usuario_id": 1})
    resultado("Bob (sin token) pide GET /v1/habitos?usuario_id=1", resp)
    print(f"  Bob obtiene los datos privados de Alice: {resp.json()}")
    print("  Y basta un bucle usuario_id=1..N para volcar la base completa.")

    print("\n[B2] Endpoint que 'usa JWT' pero no verifica la firma")
    tok_falso = jwt.encode({"sub": "1"}, "cualquier-cosa", algorithm=ALGORITHM)
    resp = vuln.get("/v2/habitos", headers={"Authorization": f"Bearer {tok_falso}"})
    resultado("Bob inventa un JWT con sub=1 y cualquier clave", resp)
    print(f"  Bob obtiene los datos privados de Alice: {resp.json()}")
    print("  Tener un JWT no sirve de nada si no se verifica: es solo texto.")

    print("\n[B3] El mismo ataque contra la app real")
    real = TestClient(app)
    resultado("GET /habitos/?usuario_id=1 (sin token)", real.get("/habitos/", params={"usuario_id": 1}))
    resultado("GET /habitos/ con el JWT inventado",
              real.get("/habitos/", headers={"Authorization": f"Bearer {tok_falso}"}))


def main() -> None:
    app.dependency_overrides[get_db] = lambda: None
    app.dependency_overrides[get_usuarios_repo] = lambda: repo_usuarios
    app.dependency_overrides[get_habitos_repo] = lambda: repo_habitos
    try:
        client = TestClient(app)
        tok_alice, _ = preparar_escenario(client)
        parte_a(client)
        parte_b(tok_alice)
    finally:
        app.dependency_overrides.clear()

    titulo("CONCLUSIÓN")
    print("  - El usuario_id sale SOLO del JWT verificado (get_current_user), nunca del cliente.")
    print("  - Verificar = firma + expiración + usuario existente. Saltar cualquiera rompe todo.")
    print("  - La garantía depende de que SECRET_KEY sea secreta y aleatoria.")


if __name__ == "__main__":
    main()
