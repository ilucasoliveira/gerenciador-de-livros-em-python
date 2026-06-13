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

from fastapi import FastAPI, HTTPException
# HTTPException (utilizar para tratativas de erros)

app = FastAPI()

# Fabrica (onde produz os livros, precisa de um lugar para guarda-lo, ESTOQUE(Banco de Dados))
# Livraria ( precisa tambem de um ESTOQUE(Banco de Dados) para guardar os novos livros)
# Como ainda não sei Bando de Dados iremos adicionar os dados em um Dicionário

estoque = {}

@app.get("/livros")
def read_livros():
    if not estoque:
        return {"message": "Nenhum livro está no estoque!"}
    else:
        return {"livros": estoque}

#Livro: ID, Nome, Autor, Ano
@app.post("/adiciona")
def add_livro(id: int, nome: str, autor: str, quantidade: int):
    if id in estoque:
        raise HTTPException(status_code=400, detail="Esse livro já existe!") # raise: função reservada para aparecer o HTTPException
    elif nome in estoque:
        return {"message": "Esse livro já existe na base de dados!"}
    else:
        estoque[id] = {
            "nome": nome,
            "autor": autor,
            "quantidade": quantidade
        }
        return {"mensagem": "Livro criado com sucesso!"}

@app.put("/atualiza/{id}")
def update_livro(id: int, nome: str = None, autor: str = None, quantidade: int = None):
    livro = estoque.get(id)
    if not livro:
        raise HTTPException(status_code=404, detail="Livro não encontrado!")
    else:
        if nome is not None:
            livro["nome"] = nome
        if autor is not None:
            livro["autor"] = autor
        if quantidade is not None:
            livro["quantidade"] = quantidade
        return {"message": "Atualização feita com sucesso!"}

@app.delete("/deletar/{id}")
def delete_livro(id: int):
    if id not in estoque:
        raise HTTPException(status_code=404, detail="Livro não encontrado!")
    else:
        del estoque[id]
        return {"message": "Livro removido com sucesso!"}