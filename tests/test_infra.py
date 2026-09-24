import tomllib
from pathlib import Path


def test_pyproject_dependencies_and_omit():
    pyproject_path = Path("pyproject.toml")
    assert pyproject_path.exists(), "pyproject.toml debe existir"
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    deps = data["project"]["dependencies"]
    assert any("bcrypt<4.1" in d for d in deps), "Debe fijar bcrypt<4.1"
    assert any("fastapi" in d for d in deps), "Debe incluir fastapi"
    assert any("sqlalchemy" in d for d in deps), "Debe incluir sqlalchemy"

    omit_list = data["tool"]["coverage"]["run"]["omit"]
    assert "app/main.py" in omit_list, "Debe excluir app/main.py de coverage según Artículo VII.3"
    assert "app/database.py" in omit_list, "Debe excluir app/database.py según Artículo VII.3"


def test_env_example_and_gitignore():
    env_example = Path(".env.example").read_text(encoding="utf-8")
    assert "SECRET_KEY=" in env_example
    assert "DATABASE_URL=" in env_example
    assert "ACCESS_TOKEN_EXPIRE_MINUTES=" in env_example

    gitignore = Path(".gitignore").read_text(encoding="utf-8")
    assert ".env" in gitignore

