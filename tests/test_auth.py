import os
import pytest

from dotenv import load_dotenv
from fastapi.testclient import TestClient

from app.main import app

load_dotenv()

os.environ["MEU_USUARIO"] = "admin"
os.environ["MINHA_SENHA"] = "admin"

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_redis(mocker):
    mock_redis_client = mocker.patch("app.cache.redis_client", autospec=True)
    mock_redis_client.get.return_value = None

def test_user_authenticate_sucesso():
    response = client.get(
        "/livros",
        auth=("admin", "admin")
    )
    
    assert response.status_code == 200

def test_user_authenticate_error():
    response = client.get(
        "/livros",
        auth=("error_usuario", "admin")
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized credentials"
    assert response.json()["headers"] == {"WWW-Authenticate": "Basic"}
