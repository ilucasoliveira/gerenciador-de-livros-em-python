# 📚 Gerenciador de Livros: API REST com FastAPI

API RESTful de gerenciamento de livros desenvolvida com **FastAPI**, **SQLAlchemy (async)**, **PostgreSQL**, **Redis** e **Celery**, totalmente containerizada com **Docker Compose**. Projeto prático do curso **Full Stack Python da EBAC**.

> Sobe com dois comandos. Não é preciso instalar Python, Poetry, PostgreSQL ou Redis na máquina, só Docker.

---

## 🧠 Sobre o projeto

Este projeto simula o back-end de uma livraria, expondo endpoints CRUD para gerenciar um catálogo de livros. O armazenamento é feito em um banco **PostgreSQL**, com persistência via **SQLAlchemy ORM** em modo assíncrono, e as listagens são aceleradas por uma camada de **cache em Redis** com estratégia cache-aside.

Além do CRUD, a aplicação demonstra **processamento assíncrono em background** com **Celery**: tarefas demoradas são publicadas em uma fila no Redis e executadas por um worker separado, sem bloquear a resposta HTTP.

A aplicação roda em quatro containers orquestrados pelo Docker Compose: a API, o banco, o cache/broker e o worker do Celery, com healthcheck, controle de ordem de inicialização e volume nomeado para persistência dos dados.

---

## 🚀 Tecnologias utilizadas

- [Docker](https://www.docker.com/) e **Docker Compose**: containerização e orquestração
- [Python 3.14](https://www.python.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Uvicorn](https://www.uvicorn.org/): servidor ASGI
- [SQLAlchemy 2.0](https://www.sqlalchemy.org/): ORM em modo assíncrono (`AsyncSession`)
- [PostgreSQL 18](https://www.postgresql.org/) via **asyncpg**
- [Redis 8](https://redis.io/) via `redis.asyncio`: cache de leitura e broker do Celery
- [Celery 5](https://docs.celeryq.dev/): fila de tarefas em background
- [Pydantic](https://docs.pydantic.dev/): validação e serialização de dados
- [python-dotenv](https://pypi.org/project/python-dotenv/): variáveis de ambiente
- [Poetry](https://python-poetry.org/): gerenciamento de dependências
- Swagger UI (embutido no FastAPI): documentação interativa

---

## 🏗️ Arquitetura

```
┌──────────────────────────────────────────────────────────────────┐
│                             Docker                               │
│                                                                  │
│   ┌──────────────────┐        ┌──────────────────┐               │
│   │   livros-api     │───────▶│    livros-db     │               │
│   │  FastAPI/uvicorn │        │   PostgreSQL 18  │               │
│   │      :8000       │        │      :5432       │               │
│   └────────┬─────────┘        └────────┬─────────┘               │
│            │                           │                         │
│            │ cache + fila         ┌────────┐                     │
│            ▼                      │ pgdata │                     │
│   ┌──────────────────┐            │(volume)│                     │
│   │  livros-cache    │            └────────┘                     │
│   │     Redis 8      │                                           │
│   │      :6379       │                                           │
│   └────────▲─────────┘                                           │
│            │ consome a fila "livros"                             │
│   ┌────────┴─────────┐                                           │
│   │  livros-celery   │                                           │
│   │  Celery worker   │                                           │
│   └──────────────────┘                                           │
└────────────┼────────────────────────┼────────────────────────────┘
             ▼                        ▼
      localhost:8000            localhost:5433
       (API / Swagger)        (acesso via pgAdmin)
```

A API acessa o banco pelo hostname `db` e o Redis pelo hostname `redis`, ambos na rede interna do Compose. A porta `5433` existe apenas para inspeção externa do banco (pgAdmin, DBeaver).

O Redis acumula duas funções: cache das listagens e broker/backend do Celery.

---

## 📋 Funcionalidades

| Método | Endpoint             | Descrição                                 | Auth |
| ------ | -------------------- | ----------------------------------------- | ---- |
| GET    | `/`                  | Health check da aplicação                 | ❌   |
| POST   | `/calcular/soma`     | Enfileira uma soma no Celery              | ❌   |
| POST   | `/calcular/fatorial` | Enfileira um fatorial no Celery           | ❌   |
| GET    | `/ler`               | Lista os livros com paginação (com cache) | ✅   |
| POST   | `/adicionar`         | Adiciona um novo livro                    | ✅   |
| PATCH  | `/atualizar/{id}`    | Atualização parcial de um livro           | ✅   |
| DELETE | `/deletar/{id}`      | Remove um livro pelo ID                   | ✅   |
| GET    | `/debug/redis`       | Inspeciona as chaves do cache e seus TTLs | ✅   |

> Os endpoints de livros e o `/debug/redis` requerem autenticação via **HTTP Basic Auth**.

---

## ⚙️ Processamento em background com Celery

Os endpoints `/calcular/*` não executam o cálculo na requisição. Eles publicam uma mensagem no Redis e devolvem imediatamente um `task_id`, com status `200`. O worker consome a fila e executa em outro processo.

As tasks incluem um `time.sleep(3)` proposital, para tornar visível a diferença entre "aceitar o trabalho" e "concluir o trabalho".

### Registro das tasks

O objeto `Celery` é criado em `app/celery_app.py` com `include=["app.tasks"]`. Sem isso, o worker sobe com a lista `[tasks]` vazia: o decorador `@celery_app.task` só registra a função quando o módulo é efetivamente importado, e o worker não importa o `main.py`.

### Roteamento da fila

O worker é iniciado com `-Q livros`, ou seja, escuta apenas a fila `livros`. Por padrão, o Celery publica na fila `celery`. Sem roteamento explícito, as mensagens ficariam paradas no Redis para sempre.

A ligação é feita pela configuração `task_routes`, que envia tudo que casa com `app.tasks.*` para a fila `livros`.

### Verificando

```bash
docker compose logs celery --tail 20
docker compose exec redis redis-cli LLEN livros
```

O log deve mostrar `received` e, três segundos depois, `succeeded`.

---

## ⚡ Estratégia de cache

O cache usa o padrão **cache-aside** (lazy loading): a aplicação consulta o cache primeiro e só vai ao banco quando não encontra o dado.

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

> ℹ️ O TTL de **30 segundos** é intencionalmente baixo para fins de demonstração: permite observar a expiração acontecendo em tempo real pelo `/debug/redis`. Em cenário real, listagens usam TTLs de minutos.

O `/debug/redis` filtra pelo padrão `livro:*`, com os dois pontos fixos. Sem eles, o padrão `livro*` também casaria com as chaves de listagem `livros:...`, misturando as duas famílias na resposta.

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

## 🔄 Stack assíncrona

O projeto usa I/O assíncrono de ponta a ponta, e isso exige coerência em todas as camadas:

| Camada    | Peça                                         |
| --------- | -------------------------------------------- |
| Engine    | `create_async_engine` + driver `asyncpg`     |
| Sessão    | `async_sessionmaker` e `AsyncSession`        |
| Redis     | `redis.asyncio`, com `await` em todo comando |
| Endpoints | `async def`                                  |

Dois pontos que costumam passar despercebidos:

**A URL precisa declarar o driver.** `postgresql://` faz o SQLAlchemy escolher o psycopg2, que é síncrono, e a engine assíncrona recusa. O formato correto é `postgresql+asyncpg://`.

**`session.add()` não é assíncrono.** Ele apenas coloca o objeto na sessão em memória. Só `commit`, `refresh`, `execute`, `flush` e `delete` recebem `await`.

---

## 🛠️ Como executar

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
# ATENÇÃO: o driver "+asyncpg" é obrigatório, a engine é assíncrona
DATABASE_URL=postgresql+asyncpg://postgres:SUA_SENHA_AQUI@db:5432/backend_book_ebac

# Credenciais do PostgreSQL (usadas pelo container do banco)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=SUA_SENHA_AQUI
POSTGRES_DB=backend_book_ebac

# Cache e broker
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

Aguarde até ver `Application startup complete` no `livros-api` e `celery@... ready` no `livros-celery`.

**4. Crie as tabelas**

Em outro terminal, na mesma pasta:

```bash
docker compose exec app python -m app.create_table
```

> ⚠️ O `-m` não é opcional. Os módulos vivem dentro do pacote `app/` e se importam por caminho absoluto (`from app.models import Base`). Rodar `python app/create_table.py` trataria o arquivo como script solto, fora do pacote, e o import quebraria.

> ⚠️ O script usa `Base.metadata.create_all()`, que **apenas cria tabelas inexistentes**. Ele não altera tabelas já criadas. Se você mudar o modelo depois, rode `docker compose down -v` para recriar o banco do zero, ou adote o Alembic.

Pronto. A API está em `http://localhost:8000`.

---

## 🐳 Comandos úteis

| Comando                                                        | Descrição                                   |
| -------------------------------------------------------------- | ------------------------------------------- |
| `docker compose up -d`                                         | Sobe em segundo plano                       |
| `docker compose logs -f app`                                   | Acompanha os logs da API                    |
| `docker compose logs -f celery`                                | Acompanha os logs do worker                 |
| `docker compose down`                                          | Derruba os containers (**mantém** os dados) |
| `docker compose down -v`                                       | Derruba e **apaga** o banco                 |
| `docker compose exec app bash`                                 | Abre um terminal dentro do container da API |
| `docker compose exec db psql -U postgres -d backend_book_ebac` | Acessa o banco via psql                     |
| `docker compose exec redis redis-cli KEYS "livro*"`            | Lista as chaves de cache                    |
| `docker compose exec redis redis-cli LLEN livros`              | Mostra o tamanho da fila do Celery          |
| `docker compose ps`                                            | Mostra o status dos containers              |

O código é montado via bind mount e o uvicorn roda com `--reload`: alterações em arquivos `.py` são aplicadas automaticamente, sem rebuild. Use `--build` apenas ao alterar o `Dockerfile` ou o `pyproject.toml`.

> ⚠️ O worker do Celery **não** tem hot reload. Ao alterar `tasks.py` ou `celery_app.py`, reinicie o serviço com `docker compose restart celery`.

> ⚠️ Evite manter o projeto em pastas sincronizadas por nuvem (OneDrive, Dropbox, Google Drive). O bind mount dessas pastas quebra o file watcher do `--reload`.

---

## 🗄️ Acessando o banco pelo pgAdmin

| Campo    | Valor                        |
| -------- | ---------------------------- |
| Host     | `localhost`                  |
| Porta    | `5433`                       |
| Database | `backend_book_ebac`          |
| Username | valor de `POSTGRES_USER`     |
| Password | valor de `POSTGRES_PASSWORD` |

> A porta externa é `5433` para não conflitar com uma instalação local do PostgreSQL na `5432`. A aplicação usa `5432`, porque fala com o container pela rede interna e não passa por esse mapeamento.

---

## 🔐 Autenticação

A API utiliza **HTTP Basic Authentication**, com as credenciais carregadas de variáveis de ambiente (nada fixo no código) e comparação via `secrets.compare_digest`, que protege contra ataques de temporização.

As variáveis são validadas na inicialização do módulo: se `MEU_USUARIO` ou `MINHA_SENHA` estiverem ausentes ou vazias, a aplicação levanta `RuntimeError` e não sobe.

> ℹ️ HTTP Basic transmite as credenciais em Base64, o que **não** é criptografia. É adequado para fins didáticos; em produção seria necessário HTTPS e, preferencialmente, JWT ou OAuth2.

---

## 🗂️ Estrutura do projeto

```
gerenciador-de-livros-em-python/
├── app/
│   ├── __init__.py       # marca o diretório como pacote Python
│   ├── main.py           # rotas e lógica dos endpoints
│   ├── auth.py           # autenticação HTTP Basic
│   ├── cache.py          # cliente Redis assíncrono e funções de cache
│   ├── celery_app.py     # instância e configuração do Celery
│   ├── tasks.py          # tarefas executadas pelo worker
│   ├── database.py       # engine e sessão assíncrona do SQLAlchemy
│   ├── models.py         # modelo ORM (tabela Livro)
│   ├── schemas.py        # schemas Pydantic (validação de entrada/saída)
│   └── create_table.py   # script para criar as tabelas no banco
├── Dockerfile            # imagem da aplicação
├── docker-compose.yml    # orquestração (app + db + redis + celery)
├── .dockerignore
├── pyproject.toml        # dependências (Poetry)
├── poetry.lock
├── .env.example          # modelo das variáveis de ambiente (versionado)
├── .env                  # variáveis reais (não versionado)
├── .gitignore
└── README.md
```

> O `__init__.py` é o que transforma `app/` em um pacote importável. É ele que faz `from app.models import Base` e `uvicorn app.main:app` funcionarem.

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

### Enfileirar uma tarefa

```http
POST /calcular/soma?a=2&b=3
```

Resposta imediata:

```json
{
  "task_id": "5ceacab3-a994-4174-bcc6-f43d9cd4b430",
  "message": "Tarefa de soma enviada para execução!"
}
```

O `200` significa apenas que a mensagem foi publicada na fila. O resultado aparece no log do worker cerca de três segundos depois.

### Inspecionar o cache

```http
GET /debug/redis
Authorization: Basic <usuario_e_senha_em_base64>
```

O campo `ttl` traz os segundos restantes. O valor `-1` indica chave sem prazo de expiração e `-2`, chave inexistente. Uma lista vazia normalmente significa que os 30 segundos de TTL já passaram.

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

- **Sem consulta de status das tarefas**: os endpoints `/calcular/*` devolvem um `task_id`, mas não existe rota que consulte o resultado. Falta um `GET /tarefas/{task_id}` usando o `AsyncResult` do Celery.
- **`KEYS` em vez de `SCAN`**: a inspeção e a invalidação do cache usam `KEYS`, que varre todo o keyspace. O Redis é single-threaded, então em bases grandes isso bloqueia o servidor.
- **Chaves `livro:{id}` sem consumidor**: são gravadas e invalidadas, mas nenhum endpoint as lê. Falta um `GET /livro/{id}`. A chave também é gravada a partir do schema de entrada, sem o campo `id`.
- **Falha do cache derruba a requisição**: se o Redis estiver indisponível, os endpoints retornam `500`, mesmo com a operação no banco bem-sucedida. O ideal é registrar o erro em log e seguir sem cache.
- **Sem migrações**: o schema é criado via `create_all()`, que não altera tabelas existentes. Alembic resolveria.
- **Sem testes automatizados**: toda a verificação é manual, via Swagger.

---

## 🎓 Contexto de aprendizado

Projeto desenvolvido como exercício prático do curso **Full Stack Python** da [EBAC](https://ebaconline.com.br/), cobrindo:

**API e back-end**

- Criação de APIs REST com FastAPI
- Métodos HTTP: `GET`, `POST`, `PATCH`, `DELETE`
- Modelagem e persistência com **SQLAlchemy ORM** assíncrono + **PostgreSQL**
- Diferença entre operações que exigem `await` e operações em memória na sessão
- Constraints de integridade (`UNIQUE`) e tratamento de `IntegrityError`
- Validação com **Pydantic** e `Field` constraints
- Serialização de objetos ORM com `ConfigDict(from_attributes=True)`
- Autenticação com **HTTP Basic Auth** e `compare_digest`
- Validação de configuração na inicialização (fail-fast)
- Injeção de dependências com `Depends` e paginação
- Organização em pacote Python e imports absolutos

**Cache**

- Estratégia **cache-aside** com Redis
- Modelagem de chaves por parâmetro de consulta e padrões de busca (`livro:*`)
- Expiração por TTL com `SETEX`
- Invalidação explícita após escritas, posicionada depois do `commit`
- Diferença entre expiração (relógio) e invalidação (aplicação)

**Filas e background**

- Instância do Celery com broker e backend no Redis
- Registro de tasks via `include`
- Roteamento de filas com `task_routes` e consumo com `-Q`
- Diferença entre aceitar uma tarefa e concluí-la
- Inspeção de filas pelo `redis-cli`

**Containerização**

- `Dockerfile` com aproveitamento de cache de camadas
- Orquestração multi-container com **Docker Compose**
- Rede interna e resolução de serviços por nome
- Mapeamento de portas e resolução de conflitos com serviços locais
- **Volumes nomeados** para persistência vs. **bind mounts** para hot reload
- `healthcheck` + `depends_on` com `service_healthy` e `service_started`
- Gerenciamento de segredos via `.env` e interpolação `${VARIAVEL}`

---

## 👤 Autor

**Lucas de Oliveira**
GitHub: [ilucasoliveira](https://github.com/ilucasoliveira)
LinkedIn: [linkedin.com/in/ilucasoliveira/](https://www.linkedin.com/in/ilucasoliveira/)

---

## 📄 Licença

Este projeto é de uso educacional e não possui licença formal.
