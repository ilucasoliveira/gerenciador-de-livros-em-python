import os
import redis
import json
from dotenv import load_dotenv
from schemas import SchemaLivro

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "redis") # lê a variável de ambiente. O segundo argumento é o valor padrão, usado se a variável não existir.
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379)) # mesma ideia, mas variáveis de ambiente sempre chegam como texto, então o int() converte.

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=0,
    decode_responses=True,
    socket_connect_timeout=2, # no máximo 2 segundos tentando abrir a conexão. Sem isso, o padrão é esperar indefinidamente.
    socket_timeout=2 # no máximo 2 segundos esperando resposta de um comando já conectado.
)

def salvar_livro_redis(id: int, livro: SchemaLivro):
    redis_client.setex(f"livro:{id}", 30, json.dumps(livro.model_dump()))

def delete_livro_redis(id: int):
    redis_client.delete(f"livro:{id}")

def invalidar_listagens():
    chaves = redis_client.keys("livros:*")
    if chaves:
        redis_client.delete(*chaves)