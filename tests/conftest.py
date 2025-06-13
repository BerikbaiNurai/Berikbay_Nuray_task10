# tests/conftest.py
import os, sys, pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine
from sqlalchemy.pool import StaticPool

# Чтобы imports работали
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import database
import main
import models  # регистрируем все модели в metadata

@pytest.fixture
def client(monkeypatch):
    # 1) создаём in-memory SQLite с StaticPool
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    # 2) подменяем движок в вашем приложении
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(main, "engine", engine)
    # 3) вручную создаём все таблицы (User, Note и т.д.)
    SQLModel.metadata.create_all(engine)
    # 4) TestClient — контекстный менеджер, чтобы сработали startup/shutdown
    with TestClient(main.app) as c:
        yield c
