import asyncio
import json

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasicCredentials

from auth import user_authenticate
from cache import redis_client, salvar_livro_redis, delete_livro_redis, invalidar_listagens
from models import Livro
from schemas import SchemaLivro, SchemaLivroResponse, SchemaLivrosOrdenacaoResponse, SchemaUpdateLivro ,SchemaUpdateLivroResponse
from database import get_db
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

app = FastAPI(
    title="Gerenciador de Livros API",
    description="Esse gerenciador foi criado no intuito de aprender como utilizar API e seus métodos, funções e funcionabilidades.",
    version="1.0.0",
    contact={
        "name":"Lucas de Oliveira",
        "email":"lucasdeoliveira937@gmail.com"
    }
)

@app.get("/")
def health_check():
    return {"message":"OK"}

async def chamada_externa1():
    await asyncio.sleep(2)
    return "Resultado chamada externa 1: OK"

async def chamada_externa2():
    await asyncio.sleep(2)
    return "Resultado chamada externa 2: OK"

async def chamada_externa3():
    await asyncio.sleep(2)
    return "Resultado chamada externa 3: OK"

@app.get("/chamadas-externas")
async def chamadas_externas():
    tarefa1 = asyncio.create_task(chamada_externa1())
    tarefa2 = asyncio.create_task(chamada_externa2())
    tarefa3 = asyncio.create_task(chamada_externa3())
    
    resultado1 = await tarefa1
    resultado2 = await tarefa2
    resultado3 = await tarefa3
    
    return {
        "message":"Todas as chamadas nas API's foram concluídas com sucesso.",
        "resultado": [resultado1, resultado2, resultado3]
    }


@app.post("/adicionar", status_code=201, response_model=SchemaLivroResponse)
async def create_livro( livro: SchemaLivro, credentials: HTTPBasicCredentials = Depends(user_authenticate), db: Session=Depends(get_db)):
    
    conflict = db.execute(select(Livro).filter(Livro.nome == livro.nome)).scalars().first()
    if conflict:
        raise HTTPException(status_code=409, detail="Livro já adicionado a biblioteca!")
    
    new_livro = Livro(**livro.model_dump())
    
    try:
        db.add(new_livro)
        db.commit()
        db.refresh(new_livro)
        
        salvar_livro_redis(new_livro.id, livro)
        
        invalidar_listagens()
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Não foi possível adicionar esse livro. Tente Novamente!")
    
    return new_livro

@app.get("/debug/redis")
def ver_livros_redis(credentials: HTTPBasicCredentials = Depends(user_authenticate)):
    chaves = redis_client.keys("livro*")
    livros = []
    
    for chave in chaves:
        valor = redis_client.get(chave)
        
        if valor is None: 
            continue
        
        ttl = redis_client.ttl(chave)
        
        livros.append({"chave": chave, "valor": json.loads(valor), "ttl": ttl})
    
    return livros

@app.get("/ler", status_code=200, response_model=SchemaLivrosOrdenacaoResponse)
async def read_livros(page: int= 1, limit: int= 10, credentials: HTTPBasicCredentials = Depends(user_authenticate), db: Session=Depends(get_db)):
    
    if page < 1 or limit < 1:
        raise HTTPException(status_code=400, detail="Page or limit estão inválidos!")
    
    cache_key = f"livros:page={page}&limit={limit}"
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    livros = db.execute(select(Livro).offset((page - 1) * limit).limit(limit)).scalars().all()
    
    total = db.execute(select(func.count(Livro.id))).scalar()
    
    total_pages = (total + limit - 1) // limit
    
    resposta = SchemaLivrosOrdenacaoResponse.model_validate({ # cria o schema a partir do dicionário. O campo livros chega como lista de objetos Livro do SQLAlchemy, e o Pydantic consegue lê-los porque SchemaLivroResponse herda o ConfigDict(from_attributes=True) do SchemaLivro.
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "livros": livros
    })
    
    redis_client.setex(cache_key, 30, resposta.model_dump_json()) # devolve uma string JSON já pronta. Não precisa mais do json.dumps, e o TypeError desaparece porque quem serializa agora é o Pydantic, não o json.
    
    return resposta # devolve o objeto Pydantic. O FastAPI lida com isso normalmente.

@app.patch("/atualizar/{id}", status_code=200,response_model=SchemaUpdateLivroResponse)
async def update_livro(id: int, update_livro: SchemaUpdateLivro, credentials: HTTPBasicCredentials = Depends(user_authenticate), db: Session=Depends(get_db)):
    
    livro = db.execute(select(Livro).filter(Livro.id == id)).scalars().first()
    
    if not livro:
        raise HTTPException(status_code=404, detail="Livro não encontrado!")
    
    novo_dado = update_livro.model_dump(exclude_unset=True)
    
    for chave, valor in novo_dado.items():
        setattr(livro, chave, valor)
    
    try:
        db.commit()
        db.refresh(livro)
        delete_livro_redis(id)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Já existe um livro com esse nome. Tente Novamente!")
    
    invalidar_listagens()
    
    return livro

@app.delete("/deletar/{id}", status_code=204)
async def delete_livro(id: int, credentials: HTTPBasicCredentials = Depends(user_authenticate), db: Session=Depends(get_db)):
    livro = db.execute(select(Livro).filter(Livro.id == id)).scalars().first()
    
    if not livro:
        raise HTTPException(status_code=404, detail="Livro não encontrado!")
    
    db.delete(livro)
    db.commit()
    
    delete_livro_redis(livro.id)
    invalidar_listagens()