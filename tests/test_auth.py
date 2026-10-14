import os

# As variáveis precisam existir ANTES de importar a app,
# porque o módulo de autenticação lê as credenciais corretas do ambiente.
os.environ["MEU_USUARIO"] = "usuario_teste"
os.environ["MINHA_SENHA"] = "senha_teste"

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient

from app.auth import user_authenticate
from app.main import app

USUARIO_CORRETO = "usuario_teste"
SENHA_CORRETA = "senha_teste"

# Rota criada só para os testes: qualquer requisição a ela passa pela
# dependência user_authenticate, então ela serve para exercitar a autenticação.
@app.get("/protegida")
async def rota_protegida(credentials=Depends(user_authenticate)):
    return {"mensagem": "Acesso autorizado", "usuario": credentials.username}

client = TestClient(app)

# Cenário de sucesso: usuário e senha corretos.
# Esperado: 200 e o corpo com a mensagem de acesso e o usuário autenticado.
def test_login_com_credenciais_corretas():
    response = client.get("/protegida", auth=(USUARIO_CORRETO, SENHA_CORRETA))
    
    assert response.status_code == 200
    
    corpo = response.json()
    assert corpo["mensagem"] == "Acesso autorizado"
    assert corpo["usuario"] == USUARIO_CORRETO

# Cenários de credenciais enviadas, mas inválidas. Cada tupla roda como um teste separado:
# 1. usuário certo, senha errada
# 2. usuário errado, senha certa
# 3. os dois errados
# 4. os dois vazios
# Esperado em todos: 401, mensagem de credenciais inválidas e o header
# WWW-Authenticate pedindo autenticação Basic.
@pytest.mark.parametrize(
    "usuario, senha",
    [
        (USUARIO_CORRETO, "senha_errada"),
        ("usuario_errado", SENHA_CORRETA),
        ("usuario_errado", "senha_errada"),
        ("", ""),
    ],
)
def test_login_com_credenciais_invalidas(usuario, senha):
    response = client.get("/protegida", auth=(usuario, senha))
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized credentials"
    assert response.headers["WWW-Authenticate"] == "Basic"

# Cenário sem credenciais: a requisição não manda o header Authorization.
# Quem barra é o próprio HTTPBasic do FastAPI, antes de chegar na nossa função,
# por isso a mensagem é a padrão do framework ("Not authenticated").
def test_requisicao_sem_credenciais():
    response = client.get("/protegida")
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
    assert response.headers["WWW-Authenticate"] == "Basic"

# Cenário de caracteres acentuados: o HTTPBasic do FastAPI só aceita ASCII
# ao decodificar as credenciais. O objetivo aqui é garantir que isso vire
# um 401 controlado, e não um erro 500 derrubando a API.
# Como a recusa acontece no FastAPI, a mensagem é a padrão do framework.
def test_credenciais_com_acento_nao_derrubam_a_api():
    response = client.get("/protegida", auth=("usuário", "senhação"))
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
    assert response.headers["WWW-Authenticate"] == "Basic"