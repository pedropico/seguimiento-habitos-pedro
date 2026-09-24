from datetime import timedelta
from app.security import crear_token_acceso, decodificar_token, hashear_password, verificar_password


def test_password_hashing():
    pw = "SuperClave123!"
    h = hashear_password(pw)
    assert h != pw
    assert verificar_password(pw, h) is True
    assert verificar_password("otra", h) is False


def test_jwt_token_flow():
    data = {"sub": "42", "email": "test@domain.com"}
    token = crear_token_acceso(data)
    decoded = decodificar_token(token)

    assert decoded is not None
    assert decoded["sub"] == "42"
    assert decoded["email"] == "test@domain.com"
    assert "exp" in decoded

    # Token expirado
    expired_token = crear_token_acceso(data, expires_delta=timedelta(seconds=-10))
    assert decodificar_token(expired_token) is None

    # Token inválido
    assert decodificar_token("token_invalido_totalmente") is None
