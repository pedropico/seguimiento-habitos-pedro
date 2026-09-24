from app.config import Settings


def test_settings_loaded_from_env():
    s = Settings(
        SECRET_KEY="test_secret_123",
        DATABASE_URL="sqlite:///:memory:",
        ACCESS_TOKEN_EXPIRE_MINUTES=30,
    )
    assert s.SECRET_KEY == "test_secret_123"
    assert s.DATABASE_URL == "sqlite:///:memory:"
    assert s.ACCESS_TOKEN_EXPIRE_MINUTES == 30
