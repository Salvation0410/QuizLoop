import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    database = tmp_path / "quizeloop-test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database.as_posix()}")
    monkeypatch.setenv("LLM_MODE", "demo")

    from app import models  # noqa: F401
    from app.core.config import get_settings
    from app.db.base import Base
    from app.db.session import build_engine
    from app.main import create_app

    get_settings.cache_clear()
    engine = build_engine(f"sqlite:///{database.as_posix()}")
    Base.metadata.create_all(engine)
    engine.dispose()
    with TestClient(create_app()) as test_client:
        yield test_client
    get_settings.cache_clear()
