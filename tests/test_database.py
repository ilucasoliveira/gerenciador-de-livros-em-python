import asyncio
import os

# O app/auth.py exige essas variáveis no import.
os.environ.setdefault("MEU_USUARIO", "admin")
os.environ.setdefault("MINHA_SENHA", "admin")

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

load_dotenv()

from app.main import app  # noqa: E402
from app.models import Base, Livro  # noqa: E402

USUARIO = os.environ["MEU_USUARIO"]
SENHA = os.environ["MINHA_SENHA"]

# Precisa ser uma URL assíncrona: postgresql+asyncpg://usuario:senha@localhost:5433/banco
# Localmente, se DATABASE_URL_TEST não existir, usa a mesma DATABASE_URL do app.
DATABASE_URL_TEST = os.getenv("DATABASE_URL_TEST") or os.getenv("DATABASE_URL")
if not DATABASE_URL_TEST:
    raise RuntimeError(
        "Defina DATABASE_URL_TEST (ou DATABASE_URL) com uma URL postgresql+asyncpg://..."
    )

# NullPool: não deixa conexões presas a um event loop que já foi fechado.
engine = create_async_engine(DATABASE_URL_TEST, poolclass=NullPool)
TestingSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

client = TestClient(app)


async def _preparar_banco():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(delete(Livro))
    async with TestingSessionLocal() as session:
        session.add(
            Livro(nome="A Revolução dos Bichos", autor="George Orwell", ano=1945)
        )
        await session.commit()


async def _limpar_banco():
    async with TestingSessionLocal() as session:
        await session.execute(delete(Livro))
        await session.commit()


@pytest.fixture(autouse=True)
def mock_redis(mocker):
    mock_redis_client = mocker.patch("app.main.redis_client")
    mock_redis_client.get = mocker.AsyncMock(
        return_value=None
    )  # sem cache: vai ao banco
    mock_redis_client.setex = mocker.AsyncMock()
    return mock_redis_client


@pytest.fixture
def db():
    asyncio.run(_preparar_banco())
    yield
    asyncio.run(_limpar_banco())


def test_get_book(db):
    response = client.get("/ler", auth=(USUARIO, SENHA))

    assert response.status_code == 200

    data = response.json()

    assert data["livros"][0]["nome"] == "A Revolução dos Bichos"
    assert data["livros"][0]["autor"] == "George Orwell"
    assert data["livros"][0]["ano"] == 1945
