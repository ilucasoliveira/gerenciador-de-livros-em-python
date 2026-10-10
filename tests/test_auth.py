import json
import os

import pytest

# As variáveis precisam existir ANTES de importar o app, porque o app/auth.py
# lê MEU_USUARIO e MINHA_SENHA no momento do import e levanta erro se faltarem.
# setdefault: usa o valor que já existir (ex.: vindo do workflow ou do .env), senão usa "admin".
os.environ.setdefault("MEU_USUARIO", "admin")
os.environ.setdefault("MINHA_SENHA", "admin")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

USUARIO = os.environ["MEU_USUARIO"]
SENHA = os.environ["MINHA_SENHA"]

client = TestClient(app)

# Resposta que o Redis devolveria se a listagem já estivesse em cache.
# Assim a rota /ler responde direto do cache e este teste não depende do PostgreSQL:
# o foco aqui é só a autenticação.
RESPOSTA_EM_CACHE = {
    "page": 1,
    "limit": 10,
    "total": 0,
    "total_pages": 0,
    "livros": [],
}


@pytest.fixture(autouse=True)
def mock_redis(mocker):
    # O main.py faz "from app.cache import redis_client", então o nome que a rota
    # usa mora em app.main. É ali que o mock precisa ser aplicado.
    mock_redis_client = mocker.patch("app.main.redis_client")
    # O cliente é redis.asyncio: os métodos são usados com await, por isso AsyncMock.
    mock_redis_client.get = mocker.AsyncMock(return_value=json.dumps(RESPOSTA_EM_CACHE))
    return mock_redis_client


def test_user_authenticate_sucesso():
    # A rota antiga /livros não existe mais; a listagem agora é /ler.
    response = client.get("/ler", auth=(USUARIO, SENHA))

    assert response.status_code == 200


def test_user_authenticate_error():
    response = client.get("/ler", auth=("error_usuario", SENHA))

    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized credentials"
    # O FastAPI devolve o header no cabeçalho HTTP da resposta, não dentro do corpo JSON.
    assert response.headers["www-authenticate"] == "Basic"
