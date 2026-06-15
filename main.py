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

from fastapi import FastAPI, HTTPException
# HTTPException (utilizar para tratativas de erros)
from pydantic import BaseModel
# modelos que definem o formato dos dados que a API vai receber/devolver
from typing import Optional
# serve para indicar que um campo pode ser daquele tipo ou NONE

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

@app.get("/ler")
def read_livros():
    if not estoque:
        return {"message": "Nenhum livro está no estoque!"}
    else:
        return {"livros": estoque}

#Livro: ID, Nome, Autor, Ano
@app.post("/adicionar")
def create_livro(id: int, livro: Livro):
    if id in estoque:
        raise HTTPException(status_code=400, detail="Esse ID de livro já existe!") # raise: função reservada para aparecer o HTTPException
    
    for valor in estoque.values():
        if valor["nome"] == livro.nome:
            raise HTTPException(status_code=400, detail="Esse livro já existe na base de dados!")
    
    estoque[id] = livro.model_dump() # Serve para pegar tudo o que está em livro e colocar em ID
    
    return {"mensagem": "Livro criado com sucesso!", "livro": estoque[id]}

@app.put("/atualizar/{id}")
def update_livro(id: int, new_livro: UpdateLivro):
    
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
def delete_livro(id: int):
    if id not in estoque:
        raise HTTPException(status_code=404, detail="Livro não encontrado!")
    else:
        del estoque[id]
        return {"message": "Livro removido com sucesso!"}