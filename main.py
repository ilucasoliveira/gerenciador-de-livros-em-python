# API de Livros 

# GET, POST, PUT, DELETE

# POST - Adiciona novos livros (Create)
# GET - Buscar os dados dos livros (Read)
# PUT - Atualiza informações nos livros (Update)
# DELETE - Deleta informações nos livros (Delete)

# CRUD

# Create
# Read
# Update
# Delete

# Documentação Swagger -> Documentar endpoints da nossa aplicação (nossa API): http://127.0.0.1:8000/docs

from fastapi import FastAPI, HTTPException, Depends
# HTTPException (utilizar para tratativas de erros)
from fastapi.security import HTTPBasic, HTTPBasicCredentials
# usado para implementar HTTP Basic
from pydantic import BaseModel
# modelos que definem o formato dos dados que a API vai receber/devolver
from typing import Optional
# serve para indicar que um campo pode ser daquele tipo ou NONE
from secrets import compare_digest
# serve para gerar valor aleatórios criptograficamente seguros

app = FastAPI(
    title="Gerenciador de Livros API",
    description="Esse gerenciador foi criado no intuito de aprender como utilizar API e seus métodos, funções e funcionabilidades.",
    version="1.0.0",
    contact={
        "name":"Lucas de Oliveira",
        "email":"lucasdeoliveira937@gmail.com"
    }
)

# Fabrica (onde produz os livros, precisa de um lugar para guarda-lo, ESTOQUE(Banco de Dados))
# Livraria ( precisa tambem de um ESTOQUE(Banco de Dados) para guardar os novos livros)
# Como ainda não sei Bando de Dados iremos adicionar os dados em um Dicionário

MEU_USUARIO = "admin"
MINHA_SENHA = "admin"

security = HTTPBasic()

estoque = {}

class Livro(BaseModel):
    nome: str
    autor: str
    ano: int
    sinopse: Optional[str] = None

class UpdateLivro(BaseModel):
    nome: Optional[str] = None
    autor: Optional[str] = None
    ano: Optional[int] = None
    sinopse: Optional[str] = None

def autenticar_usuario(credentials: HTTPBasicCredentials = Depends(security)):
    is_username_corrrect = compare_digest(credentials.username, MEU_USUARIO)
    is_password_correct = compare_digest(credentials.password, MINHA_SENHA)
    
    if not(is_username_corrrect and is_password_correct):
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos", headers={"WWW-Authenticate": "Basic"})
    
    return credentials

@app.get("/ler")
def read_livros(page: int= 1, limit: int= 10, credentials: HTTPBasicCredentials = Depends(autenticar_usuario)):
    if page < 1 or limit < 1:
        raise HTTPException(status_code=400, detail="Pagina ou Limite estão inválidos!")
    
    if not estoque:
        return {"message":"Não existe nenhum livro!"}
    
    start = (page - 1) * limit
    end = start + limit
    
    livros_paginados = [
        {"id": id, "nome": livro_data["nome"], "autor": livro_data["autor"], "ano": livro_data["ano"], "sinopse": livro_data["sinopse"]}
        for id, livro_data in list(estoque.items())[start: end]
    ]
    
    return {
        "page": page,
        "limit": limit,
        "total": len(estoque),
        "livros": livros_paginados
    }

#Livro: ID, Nome, Autor, Ano
@app.post("/adicionar")
def create_livro(id: int, livro: Livro, credentials: HTTPBasicCredentials = Depends(autenticar_usuario)):
    if id in estoque:
        raise HTTPException(status_code=400, detail="Esse ID de livro já existe!") # raise: função reservada para aparecer o HTTPException
    
    for valor in estoque.values():
        if valor["nome"] == livro.nome:
            raise HTTPException(status_code=400, detail="Esse livro já existe na base de dados!")
    
    estoque[id] = livro.model_dump() # Serve para pegar tudo o que está em livro e colocar em ID
    
    return {"mensagem": "Livro criado com sucesso!", "livro": estoque[id]}

@app.put("/atualizar/{id}")
def update_livro(id: int, new_livro: UpdateLivro, credentials: HTTPBasicCredentials = Depends(autenticar_usuario)):
    
    livro = estoque.get(id)
    
    if not livro:
        raise HTTPException(status_code=404, detail="Livro não encontrado!")
    else:
        if new_livro.nome is not None:
            livro["nome"] = new_livro.nome
        if new_livro.autor is not None:
            livro["autor"] = new_livro.autor
        if new_livro.ano is not None:
            livro["ano"] = new_livro.ano
        if new_livro.sinopse is not None:
            livro["sinopse"] = new_livro.sinopse
        return {"message": "Atualização feita com sucesso!", "livro": livro}

@app.delete("/deletar/{id}")
def delete_livro(id: int, credentials: HTTPBasicCredentials = Depends(autenticar_usuario)):
    if id not in estoque:
        raise HTTPException(status_code=404, detail="Livro não encontrado!")
    else:
        del estoque[id]
        return {"message": "Livro removido com sucesso!"}