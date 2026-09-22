import os
import pytest

from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models import Base, Livro

client = TestClient(app)

DATABASE_URL_TEST = os.getenv("DATABASE_URL_TEST")
engine = create_engine(DATABASE_URL_TEST)
TestingSessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(bind=engine)

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_redis(mocker):
    mock_redis_client = mocker.patch("main.redis_client", autospec=True)
    mock_redis_client.get.return_value = None

@pytest.fixture(scope="function")
def db():
    db = TestingSessionLocal()
    yield db
    db.close()

def test_get_book(db, mocker):
    response = client.get("/livros", auth=("admin", "admin"))
    
    data = response.json()
    
    assert data["livros"][0]["nome"] == "A Revolução dos Bichos"
    assert data["livros"][0]["autor"] == "George Orwell"
    assert data["livros"][0]["ano"] == 1945