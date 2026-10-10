import os

import pytest

# Mesmo motivo do test_auth.py: o app/auth.py exige essas variáveis no import.
os.environ.setdefault("MEU_USUARIO", "admin")
os.environ.setdefault("MINHA_SENHA", "admin")

from dotenv import load_dotenv  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, delete  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

load_dotenv()

from app.main import app  # noqa: E402
from app.models import Base, Livro  # noqa: E402

USUARIO = os.environ["MEU_USUARIO"]
SENHA = os.environ["MINHA_SENHA"]

# Banco de teste. No GitHub Actions ele vem do serviço "postgres" definido no workflow.
# Engine síncrona (psycopg2) só para preparar os dados; a API usa a engine assíncrona
# do app/database.py, apontando para o MESMO banco via DATABASE_URL.
DATABASE_URL_TEST = os.getenv("DATABASE_URL_TEST")
engine = create_engine(DATABASE_URL_TEST)
TestingSessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(bind=engine)  # cria a tabela "livros" se ainda não existir

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_redis(mocker):
    # Caminho corrigido: era "main.redis_client", mas o módulo é app.main.
    mock_redis_client = mocker.patch("app.main.redis_client")
    # get devolvendo None = "não tem cache", então a rota vai buscar no banco.
    mock_redis_client.get = mocker.AsyncMock(return_value=None)
    # setex é chamado depois da consulta para salvar no cache; só precisa existir.
    mock_redis_client.setex = mocker.AsyncMock()
    return mock_redis_client


@pytest.fixture(scope="function")
def db():
    db = TestingSessionLocal()
    # Deixa o banco num estado conhecido: apaga tudo e insere o livro esperado.
    # Sem isso o teste dependia de dados que só existiam na sua máquina.
    db.execute(delete(Livro))
    db.add(Livro(nome="A Revolução dos Bichos", autor="George Orwell", ano=1945))
    db.commit()
    yield db
    db.execute(delete(Livro))  # limpa depois do teste
    db.commit()
    db.close()


def test_get_book(db):
    response = client.get("/ler", auth=(USUARIO, SENHA))

    assert response.status_code == 200

    data = response.json()

    assert data["livros"][0]["nome"] == "A Revolução dos Bichos"
    assert data["livros"][0]["autor"] == "George Orwell"
    assert data["livros"][0]["ano"] == 1945
