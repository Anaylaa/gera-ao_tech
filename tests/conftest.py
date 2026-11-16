
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base, get_db
from app.main import app


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def livro(db):
    novo_livro = models.Livro(
        titulo="Estatística Básica",
        autor="Wilton Bussab",
        isbn="123456789",
        categoria="Estatística",
        quantidade_total=3,
        quantidade_disponivel=3
    )

    db.add(novo_livro)
    db.commit()
    db.refresh(novo_livro)

    return novo_livro


@pytest.fixture
def leitor(db):
    novo_leitor = models.Leitor(
        nome="Maria Silva",
        email="maria.teste@email.com",
        telefone="85999999999"
    )

    db.add(novo_leitor)
    db.commit()
    db.refresh(novo_leitor)

    return novo_leitor


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
