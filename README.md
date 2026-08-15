# 📚 Gerenciador de Livros — API REST com FastAPI

API RESTful de gerenciamento de livros desenvolvida com **FastAPI**, **SQLAlchemy**, **PostgreSQL** e **Redis**, totalmente containerizada com **Docker Compose**. Projeto prático do curso **Full Stack Python da EBAC**.

> Sobe com dois comandos. Não é preciso instalar Python, Poetry, PostgreSQL ou Redis na máquina, só Docker.

---

## 🧠 Sobre o projeto

Este projeto simula o back-end de uma livraria, expondo endpoints CRUD para gerenciar um catálogo de livros. O armazenamento é feito em um banco **PostgreSQL**, com persistência real via **SQLAlchemy ORM**, e as listagens são aceleradas por uma camada de **cache em Redis** com estratégia cache-aside.

A aplicação roda em três containers orquestrados pelo Docker Compose: um para a API, um para o banco e um para o cache, com healthcheck, controle de ordem de inicialização e volume nomeado para persistência dos dados.

---

## 🚀 Tecnologias utilizadas

- [Docker](https://www.docker.com/) e **Docker Compose**: containerização e orquestração
- [Python 3.14](https://www.python.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Uvicorn](https://www.uvicorn.org/): servidor ASGI
- [SQLAlchemy](https://www.sqlalchemy.org/): ORM
- [PostgreSQL 18](https://www.postgresql.org/) (via `psycopg2-binary`)
- [Redis 8](https://redis.io/) (via `redis-py`): cache de leitura
- [Pydantic](https://docs.pydantic.dev/): validação e serialização de dados
- [python-dotenv](https://pypi.org/project/python-dotenv/): variáveis de ambiente
- [Poetry](https://python-poetry.org/): gerenciamento de dependências
- Swagger UI (embutido no FastAPI): documentação interativa

---

## 🏗️ Arquitetura

```
┌──────────────────────────────────────────────────────────────┐
│                           Docker                             │
│                                                              │
│   ┌──────────────────┐    ┌──────────────────┐               │
│   │   livros-api     │───▶│    livros-db     │               │
│   │  FastAPI/uvicorn │    │   PostgreSQL 18  │               │
│   │      :8000       │    │      :5432       │               │
│   └────────┬─────────┘    └────────┬─────────┘               │
│            │                       │                         │
│            │                  ┌────────┐                     │
│            │                  │ pgdata │                     │
│            │                  │(volume)│                     │
│            ▼                  └────────┘                     │
│   ┌──────────────────┐                                       │
│   │  livros-cache    │                                       │
│   │     Redis 8      │  (sem volume: cache é descartável)     │
│   │      :6379       │                                       │
│   └──────────────────┘                                       │
└────────────┼───────────────────────┼─────────────────────────┘
             ▼                       ▼
      localhost:8000          localhost:5433
       (API / Swagger)      (acesso via pgAdmin)
```

A API acessa o banco pelo hostname `db` e o cache pelo hostname `redis`, ambos na rede interna do Compose. A porta `5433` existe apenas para inspeção externa do banco (pgAdmin, DBeaver) e é opcional. O Redis **não** expõe porta para o host: só os outros containers falam com ele.

---

## 📋 Funcionalidades

| Método | Endpoint             | Descrição                                  | Auth |
| ------ | -------------------- | ------------------------------------------ | ---- |
| GET    | `/`                  | Health check da aplicação                  | ❌   |
| GET    | `/chamadas-externas` | Demonstração de concorrência com `asyncio` | ❌   |
| GET    | `/ler`               | Lista os livros com paginação (com cache)  | ✅   |
| POST   | `/adicionar`         | Adiciona um novo livro                     | ✅   |
| PATCH  | `/atualizar/{id}`    | Atualização parcial de um livro            | ✅   |
| DELETE | `/deletar/{id}`      | Remove um livro pelo ID                    | ✅   |
| GET    | `/debug/redis`       | Inspeciona as chaves do cache e seus TTLs  | ✅   |

> Com exceção do health check e do `/chamadas-externas`, todos os endpoints requerem autenticação via **HTTP Basic Auth**.

---

## ⚡ Estratégia de cache

O cache usa o padrão **cache-aside** (também chamado de lazy loading): a aplicação consulta o cache primeiro, e só vai ao banco quando não encontra o dado.

### Fluxo do `GET /ler`

1. Monta a chave a partir dos parâmetros de paginação: `livros:page=1&limit=10`
2. Consulta o Redis
3. **Cache hit**: devolve o JSON armazenado, sem tocar no banco
4. **Cache miss**: consulta o PostgreSQL, serializa a resposta, grava no Redis com `SETEX` e devolve

A chave inclui `page` e `limit` porque cada combinação produz uma resposta diferente. Uma chave única para "a listagem" devolveria a página errada.

### Famílias de chave

| Padrão                  | Criada em         | TTL  | Consumida em        |
| ----------------------- | ----------------- | ---- | ------------------- |
| `livros:page=X&limit=Y` | `GET /ler`        | 30 s | `GET /ler`          |
| `livro:{id}`            | `POST /adicionar` | 30 s | ainda não consumida |

> ℹ️ O TTL de **30 segundos** é intencionalmente baixo para fins de demonstração: permite observar a expiração acontecendo em tempo real pelo `/debug/redis`. Em um cenário real, listagens costumam usar TTLs de minutos e itens individuais, TTLs maiores ainda.

### Invalidação

TTL sozinho não basta: sem invalidação explícita, um livro recém-criado levaria até 30 segundos para aparecer na listagem. Por isso toda escrita bem-sucedida invalida o cache, sempre **depois** do `commit` (se a transação falha, o cache não é tocado).

| Operação                | Ação no cache                                         |
| ----------------------- | ----------------------------------------------------- |
| `POST /adicionar`       | grava `livro:{id}` e apaga todas as chaves `livros:*` |
| `PATCH /atualizar/{id}` | apaga `livro:{id}` e todas as chaves `livros:*`       |
| `DELETE /deletar/{id}`  | apaga `livro:{id}` e todas as chaves `livros:*`       |

### Serialização

O módulo `json` da biblioteca padrão não sabe serializar objetos do SQLAlchemy. A resposta é montada com `SchemaLivrosOrdenacaoResponse.model_validate(...)` e gravada com `.model_dump_json()`, delegando a serialização ao Pydantic. Os schemas usam `ConfigDict(from_attributes=True)`, que permite construir o modelo a partir dos atributos do objeto ORM.

### Tolerância a falhas

O cliente Redis é criado com `socket_connect_timeout` e `socket_timeout` de 2 segundos. Sem esses limites, o padrão do `redis-py` é esperar indefinidamente, o que transformaria uma indisponibilidade do cache em requisições penduradas.

---

## ⚙️ Como executar

### Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e em execução

Só isso. Python, Poetry, PostgreSQL e Redis ficam dentro dos containers.

### Passo a passo

**1. Clone o repositório**

```bash
git clone https://github.com/ilucasoliveira/gerenciador-de-livros-em-python.git
cd gerenciador-de-livros-em-python
```

**2. Crie o arquivo `.env` a partir do exemplo**

```bash
cp .env.example .env
```

Depois abra o `.env` e preencha os valores:

```env
# Conexão da aplicação com o banco
# ATENÇÃO: o host é "db" (nome do serviço no Compose), não "localhost"
DATABASE_URL=postgresql://postgres:SUA_SENHA_AQUI@db:5432/backend_book_ebac

# Credenciais do PostgreSQL (usadas pelo container do banco)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=SUA_SENHA_AQUI
POSTGRES_DB=backend_book_ebac

# Cache Redis
# ATENÇÃO: o host é "redis" (nome do serviço no Compose), não "localhost"
REDIS_HOST=redis
REDIS_PORT=6379

# Credenciais do HTTP Basic Auth da API
MEU_USUARIO=
MINHA_SENHA=
```

> ⚠️ A senha do banco aparece **duas vezes**: em `DATABASE_URL` e em `POSTGRES_PASSWORD`. Os dois valores precisam ser idênticos.

> ⚠️ Dentro de um container, `localhost` aponta para o próprio container. Serviços do Compose se enxergam pelo **nome do serviço** (`db`, `redis`). Esse é o erro mais comum ao containerizar uma aplicação que antes rodava direto na máquina.

> ℹ️ `MEU_USUARIO` e `MINHA_SENHA` são obrigatórios. Se ficarem vazios, a aplicação se recusa a subir e exibe a mensagem no log, em vez de quebrar depois na primeira requisição.

**3. Suba os containers**

```bash
docker compose up --build
```

Aguarde até ver `Application startup complete`. A API espera automaticamente o banco ficar disponível.

**4. Crie as tabelas**

Em outro terminal, na mesma pasta:

```bash
docker compose exec app python create_table.py
```

> ⚠️ O script usa `Base.metadata.create_all()`, que **apenas cria tabelas inexistentes**. Ele não altera tabelas já criadas. Se você mudar o modelo depois (adicionar coluna, constraint etc.), rode `docker compose down -v` para recriar o banco do zero, ou adote uma ferramenta de migração como o Alembic.

Pronto. A API está em `http://localhost:8000`.

---

## 🐳 Comandos úteis

| Comando                                                        | Descrição                                   |
| -------------------------------------------------------------- | ------------------------------------------- |
| `docker compose up -d`                                         | Sobe em segundo plano                       |
| `docker compose logs -f app`                                   | Acompanha os logs da API                    |
| `docker compose down`                                          | Derruba os containers (**mantém** os dados) |
| `docker compose down -v`                                       | Derruba e **apaga** o banco                 |
| `docker compose exec app bash`                                 | Abre um terminal dentro do container da API |
| `docker compose exec db psql -U postgres -d backend_book_ebac` | Acessa o banco via psql                     |
| `docker compose exec redis redis-cli`                          | Abre o terminal do Redis                    |
| `docker compose exec redis redis-cli KEYS "*"`                 | Lista todas as chaves em cache              |
| `docker compose ps`                                            | Mostra o status dos containers              |

O código é montado via bind mount e o uvicorn roda com `--reload`: alterações em arquivos `.py` são aplicadas automaticamente, sem rebuild. Use `--build` apenas ao alterar o `Dockerfile` ou o `pyproject.toml`.

> ⚠️ Evite manter o projeto em pastas sincronizadas por serviços de nuvem (OneDrive, Dropbox, Google Drive). O bind mount dessas pastas quebra o file watcher do `--reload`, derrubando o processo em loop com erros de I/O.

---

## 🗄️ Acessando o banco pelo pgAdmin

| Campo    | Valor                        |
| -------- | ---------------------------- |
| Host     | `localhost`                  |
| Porta    | `5433`                       |
| Database | `backend_book_ebac`          |
| Username | valor de `POSTGRES_USER`     |
| Password | valor de `POSTGRES_PASSWORD` |

> A porta externa é `5433` para não conflitar com uma instalação local do PostgreSQL na `5432`. Repare que a aplicação usa `5432`, porque fala com o container pela rede interna e não passa por esse mapeamento.

---

## 🔐 Autenticação

A API utiliza **HTTP Basic Authentication**, com as credenciais carregadas de variáveis de ambiente (nada fixo no código) e comparação via `secrets.compare_digest`, que protege contra ataques de temporização.

As variáveis são validadas na inicialização do módulo: se `MEU_USUARIO` ou `MINHA_SENHA` estiverem ausentes ou vazias, a aplicação levanta `RuntimeError` e não sobe.

> ℹ️ HTTP Basic transmite as credenciais codificadas em Base64, o que **não** é criptografia. É adequado para fins didáticos; em produção seria necessário HTTPS e, preferencialmente, JWT ou OAuth2.

---

## 🗂️ Estrutura do projeto

```
gerenciador-de-livros-em-python/
├── main.py              # Rotas e lógica dos endpoints
├── auth.py              # Autenticação HTTP Basic
├── cache.py             # Cliente Redis e funções de cache
├── database.py          # Engine e sessão do SQLAlchemy
├── models.py            # Modelo ORM (tabela Livro)
├── schemas.py           # Schemas Pydantic (validação de entrada/saída)
├── create_table.py      # Script para criar as tabelas no banco
├── Dockerfile           # Imagem da aplicação
├── docker-compose.yml   # Orquestração dos serviços (app + db + redis)
├── .dockerignore        # Arquivos excluídos do contexto de build
├── pyproject.toml       # Configuração do projeto e dependências (Poetry)
├── poetry.lock          # Lock file das dependências
├── .env.example         # Modelo das variáveis de ambiente (versionado)
├── .env                 # Variáveis de ambiente reais (não versionado)
├── .gitignore
└── README.md
```

---

## 📖 Documentação interativa

Com os containers no ar, acesse o **Swagger UI**:

```
http://localhost:8000/docs
```

Clique em **Authorize** 🔒, informe as credenciais definidas em `MEU_USUARIO` e `MINHA_SENHA`, e teste os endpoints diretamente pelo navegador.

---

## 📦 Exemplos de uso

### Adicionar um livro

```http
POST /adicionar
Authorization: Basic <usuario_e_senha_em_base64>
Content-Type: application/json

{
  "nome": "O Senhor dos Anéis",
  "autor": "J.R.R. Tolkien",
  "ano": 1954,
  "sinopse": "A jornada de Frodo para destruir o Um Anel."
}
```

O campo `nome` tem constraint `UNIQUE` no banco: tentar cadastrar um título repetido retorna `409`.

### Listar livros (com paginação)

```http
GET /ler?page=1&limit=10
Authorization: Basic <usuario_e_senha_em_base64>
```

Resposta:

```json
{
  "page": 1,
  "limit": 10,
  "total": 1,
  "total_pages": 1,
  "livros": [
    {
      "id": 1,
      "nome": "O Senhor dos Anéis",
      "autor": "J.R.R. Tolkien",
      "ano": 1954,
      "sinopse": "A jornada de Frodo para destruir o Um Anel."
    }
  ]
}
```

Catálogo vazio ou página além do total retornam `200` com `livros: []`, não `404`.

A primeira chamada consulta o banco e grava o resultado no Redis. As seguintes, dentro da janela de TTL, são servidas direto do cache.

### Atualizar um livro

```http
PATCH /atualizar/1
Authorization: Basic <usuario_e_senha_em_base64>
Content-Type: application/json

{
  "sinopse": "Uma épica aventura pela Terra Média."
}
```

Todos os campos são opcionais: envie apenas os que quiser alterar.

### Deletar um livro

```http
DELETE /deletar/1
Authorization: Basic <usuario_e_senha_em_base64>
```

### Inspecionar o cache

```http
GET /debug/redis
Authorization: Basic <usuario_e_senha_em_base64>
```

Resposta:

```json
[
  {
    "chave": "livros:page=1&limit=10",
    "valor": {
      "page": 1,
      "limit": 10,
      "total": 1,
      "total_pages": 1,
      "livros": []
    },
    "ttl": 24
  }
]
```

O campo `ttl` traz os segundos restantes. O valor `-1` indica chave sem prazo de expiração e `-2`, chave inexistente.

---

## 📐 Modelo de dados

### Livro (criação)

| Campo   | Tipo     | Obrigatório | Restrições           | Descrição         |
| ------- | -------- | ----------- | -------------------- | ----------------- |
| nome    | `string` | ✅          | 1 a 300, **único**   | Título do livro   |
| autor   | `string` | ✅          | 1 a 200              | Nome do autor     |
| ano     | `int`    | ✅          | 1000 até o ano atual | Ano de publicação |
| sinopse | `string` | ❌          | até 1000             | Resumo do livro   |

### UpdateLivro (atualização parcial)

Todos os campos acima ficam opcionais, permitindo atualizações parciais via `PATCH`. Campos omitidos no corpo não são alterados, graças ao `model_dump(exclude_unset=True)`.

### Códigos de resposta

| Código | Significado                         |
| ------ | ----------------------------------- |
| `200`  | Requisição bem-sucedida             |
| `201`  | Livro criado                        |
| `204`  | Livro removido (sem conteúdo)       |
| `400`  | Parâmetros de paginação inválidos   |
| `401`  | Credenciais ausentes ou inválidas   |
| `404`  | Livro não encontrado (PATCH/DELETE) |
| `409`  | Já existe um livro com esse nome    |
| `422`  | Corpo da requisição inválido        |

---

## ⚠️ Limitações conhecidas

Pontos identificados e conscientemente adiados, por se tratar de um projeto de estudo:

- **`KEYS` em vez de `SCAN`**: a inspeção e a invalidação do cache usam o comando `KEYS`, que varre todo o keyspace. O Redis é single-threaded, então em bases grandes isso bloqueia o servidor. `SCAN` é a alternativa correta em produção.
- **Chaves `livro:{id}` sem consumidor**: são gravadas e invalidadas, mas nenhum endpoint as lê ainda. Faltam um `GET /livro/{id}` que as consuma.
- **Falha do cache derruba a requisição**: se o Redis estiver indisponível, os endpoints retornam `500`, mesmo quando a operação no banco foi bem-sucedida. O ideal é registrar o erro em log e seguir sem cache.
- **Rotas `async def` com I/O síncrono**: SQLAlchemy e redis-py são usados em modo bloqueante dentro de corrotinas, o que ocupa o event loop. A correção é usar `def` comum (delegando à threadpool) ou migrar para o stack assíncrono (`AsyncSession`, `redis.asyncio`).
- **Sem migrações**: o schema é criado via `create_all()`, que não altera tabelas existentes. Alembic resolveria.

---

## 🎓 Contexto de aprendizado

Projeto desenvolvido como exercício prático do curso **Full Stack Python** da [EBAC](https://ebaconline.com.br/), cobrindo:

**API e back-end**

- Criação de APIs REST com FastAPI
- Métodos HTTP: `GET`, `POST`, `PATCH`, `DELETE`
- Modelagem de dados e persistência com **SQLAlchemy ORM** + **PostgreSQL**
- Constraints de integridade no banco (`UNIQUE`) e tratamento de `IntegrityError`
- Validação de dados com **Pydantic** e `Field` constraints
- Serialização de objetos ORM com `ConfigDict(from_attributes=True)` e `model_dump_json()`
- Autenticação com **HTTP Basic Auth** e `compare_digest`
- Validação de configuração na inicialização (fail-fast em variáveis de ambiente ausentes)
- Tratamento de erros com `HTTPException`
- Injeção de dependências com `Depends`
- Paginação de resultados
- Concorrência com `asyncio.create_task` e `await`
- Documentação automática via **Swagger UI**
- Arquitetura modular: `auth.py`, `cache.py`, `database.py`, `models.py`, `schemas.py`

**Cache**

- Estratégia **cache-aside** com Redis
- Modelagem de chaves por parâmetro de consulta
- Expiração por TTL com `SETEX`
- Invalidação explícita após escritas, posicionada depois do `commit`
- Diferença entre expiração (relógio) e invalidação (aplicação)
- Timeouts de conexão e de socket no cliente

**Containerização**

- Escrita de `Dockerfile` com aproveitamento de cache de camadas
- Orquestração multi-container com **Docker Compose**
- Rede interna e resolução de serviços por nome (`db` e `redis` como hostnames)
- Mapeamento de portas e resolução de conflitos com serviços locais
- **Volumes nomeados** para persistência de dados vs. **bind mounts** para hot reload
- Decisão consciente de não persistir o cache: dado descartável por definição
- `healthcheck` + `depends_on` com `service_healthy` e `service_started`
- Gerenciamento de segredos via `.env` e interpolação `${VARIAVEL}` no Compose
- Uso de `.dockerignore` para reduzir o contexto de build

---

## 👤 Autor

**Lucas de Oliveira**
GitHub: [ilucasoliveira](https://github.com/ilucasoliveira)
LinkedIn: [linkedin.com/in/ilucasoliveira/](https://www.linkedin.com/in/ilucasoliveira/)

---

## 📄 Licença

Este projeto é de uso educacional e não possui licença formal.
