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

estoque = {}

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasicCredentials

from auth import user_authenticate
from models import Livro
from schemas import SchemaLivro, SchemaUpdateLivro, SchemaBookResponse
from database import get_db
from sqlalchemy.orm import Session

app = FastAPI(
    title="Gerenciador de Livros API",
    description="Esse gerenciador foi criado no intuito de aprender como utilizar API e seus métodos, funções e funcionabilidades.",
    version="1.0.0",
    contact={
        "name":"Lucas de Oliveira",
        "email":"lucasdeoliveira937@gmail.com"
    }
)

@app.get("/ler")
def read_livros(page: int= 1, limit: int= 10, credentials: HTTPBasicCredentials = Depends(user_authenticate), db: Session=Depends(get_db)):
    if page < 1 or limit < 1:
        raise HTTPException(status_code=400, detail="Pagina ou Limite estão inválidos!")
    
    livros = db.query(Livro).offset((page - 1) * limit).limit(limit).all()
    
    if not livros:
        raise HTTPException(status_code=404, detail="Not Found")
    
    total_livros = db.query(Livro).count()
    
    return {
        "page": page,
        "limit": limit,
        "total": total_livros,
        "livros": [{"id": i.id, "nome": i.nome, "autor": i.autor, "ano": i.ano, "sinopse": i.sinopse} for i in livros]
    }

#Livro: ID, Nome, Autor, Ano
@app.post("/adicionar", status_code=201, response_model=SchemaBookResponse)
def create_livro( livro: SchemaLivro, credentials: HTTPBasicCredentials = Depends(user_authenticate), db: Session=Depends(get_db)):
    conflict = db.query(Livro).filter(Livro.nome == livro.nome).first()
    if conflict:
        raise HTTPException(status_code=409, detail="Livro já adicionado a biblioteca!")
    
    new_livro = Livro(**livro.model_dump())
    
    db.add(new_livro)
    db.commit()
    db.refresh(new_livro)
    
    return new_livro

@app.put("/atualizar/{id}", response_model=SchemaBookResponse)
def update_livro(id: int, new_livro: SchemaUpdateLivro, credentials: HTTPBasicCredentials = Depends(user_authenticate), db: Session=Depends(get_db)):
    
    livro = db.query(Livro).filter(Livro.id == id).first()
    
    if not livro:
        raise HTTPException(status_code=404, detail="Livro não encontrado!")
    
    if new_livro.nome is not None:
        livro.nome = new_livro.nome
    if new_livro.autor is not None:
        livro.autor = new_livro.autor
    if new_livro.ano is not None:
        livro.ano = new_livro.ano
    if new_livro.sinopse is not None:
        livro.sinopse = new_livro.sinopse
    
    db.commit()
    db.refresh(livro)
    
    return livro

@app.delete("/deletar/{id}", status_code=204)
def delete_livro(id: int, credentials: HTTPBasicCredentials = Depends(user_authenticate), db: Session=Depends(get_db)):
    livro = db.query(Livro).filter(Livro.id == id).first()
    
    if livro is None:
        raise HTTPException(status_code=404, detail="Livro não encontrado!")
    
    db.delete(livro)
    db.commit()