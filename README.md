# 📚 Gerenciador de Livros — API REST com FastAPI

API RESTful de gerenciamento de livros desenvolvida com **FastAPI**, **SQLAlchemy** e **PostgreSQL**, totalmente containerizada com **Docker Compose**. Projeto prático do curso **Full Stack Python da EBAC**.

> Sobe com dois comandos. Não é preciso instalar Python, Poetry ou PostgreSQL na máquina, só Docker.

---

## 🧠 Sobre o projeto

Este projeto simula o back-end de uma livraria, expondo endpoints CRUD para gerenciar um catálogo de livros. O armazenamento é feito em um banco **PostgreSQL**, com persistência real via **SQLAlchemy ORM**.

A aplicação roda em dois containers orquestrados pelo Docker Compose: um para a API e outro para o banco, com healthcheck, controle de ordem de inicialização e volume nomeado para persistência dos dados.

---

## 🚀 Tecnologias utilizadas

- [Docker](https://www.docker.com/) e **Docker Compose**: containerização e orquestração
- [Python 3.14](https://www.python.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Uvicorn](https://www.uvicorn.org/): servidor ASGI
- [SQLAlchemy](https://www.sqlalchemy.org/): ORM
- [PostgreSQL 18](https://www.postgresql.org/) (via `psycopg2-binary`)
- [Pydantic](https://docs.pydantic.dev/): validação de dados
- [python-dotenv](https://pypi.org/project/python-dotenv/): variáveis de ambiente
- [Poetry](https://python-poetry.org/): gerenciamento de dependências
- Swagger UI (embutido no FastAPI): documentação interativa

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────┐
│                    Docker                       │
│                                                 │
│   ┌──────────────────┐    ┌──────────────────┐  │
│   │   livros-api     │    │    livros-db     │  │
│   │  FastAPI/uvicorn │───▶│   PostgreSQL 18  │  │
│   │      :8000       │    │      :5432       │  │
│   └──────────────────┘    └──────────────────┘  │
│            │                       │            │
│            │                  ┌────────┐        │
│            │                  │ pgdata │        │
│            │                  │(volume)│        │
│            │                  └────────┘        │
└────────────┼───────────────────────┼────────────┘
             ▼                       ▼
      localhost:8000          localhost:5433
       (API / Swagger)      (acesso via pgAdmin)
```

A API acessa o banco pelo hostname `db` na rede interna do Compose. A porta `5433` existe apenas para inspeção externa (pgAdmin, DBeaver) e é opcional.

---

## 📋 Funcionalidades

| Método | Endpoint          | Descrição                       | Auth |
| ------ | ----------------- | ------------------------------- | ---- |
| GET    | `/`               | Health check da aplicação       | ❌   |
| GET    | `/ler`            | Lista os livros com paginação   | ✅   |
| POST   | `/adicionar`      | Adiciona um novo livro          | ✅   |
| PUT    | `/atualizar/{id}` | Atualização parcial de um livro | ✅   |
| DELETE | `/deletar/{id}`   | Remove um livro pelo ID         | ✅   |

> Com exceção do health check, todos os endpoints requerem autenticação via **HTTP Basic Auth**.

---

## ⚙️ Como executar

### Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e em execução

Só isso. Python, Poetry e PostgreSQL ficam dentro dos containers.

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

# Credenciais do HTTP Basic Auth da API
MEU_USUARIO=
MINHA_SENHA=
```

> ⚠️ A senha do banco aparece **duas vezes**: em `DATABASE_URL` e em `POSTGRES_PASSWORD`. Os dois valores precisam ser idênticos.

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
| `docker compose ps`                                            | Mostra o status dos containers              |

O código é montado via bind mount e o uvicorn roda com `--reload`: alterações em arquivos `.py` são aplicadas automaticamente, sem rebuild. Use `--build` apenas ao alterar o `Dockerfile` ou o `pyproject.toml`.

---

## 🗄️ Acessando o banco pelo pgAdmin

| Campo    | Valor                        |
| -------- | ---------------------------- |
| Host     | `localhost`                  |
| Porta    | `5433`                       |
| Database | `backend_book_ebac`          |
| Username | valor de `POSTGRES_USER`     |
| Password | valor de `POSTGRES_PASSWORD` |

> A porta externa é `5433` para não conflitar com uma instalação local do PostgreSQL na `5432`.

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
├── database.py          # Engine e sessão do SQLAlchemy
├── models.py            # Modelo ORM (tabela Livro)
├── schemas.py           # Schemas Pydantic (validação de entrada/saída)
├── create_table.py      # Script para criar as tabelas no banco
├── Dockerfile           # Imagem da aplicação
├── docker-compose.yml   # Orquestração dos serviços (app + db)
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

### Atualizar um livro

```http
PUT /atualizar/1
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

Todos os campos acima ficam opcionais, permitindo atualizações parciais (PATCH-like via PUT). Campos omitidos no corpo não são alterados.

### Códigos de resposta

| Código | Significado                       |
| ------ | --------------------------------- |
| `200`  | Requisição bem-sucedida           |
| `201`  | Livro criado                      |
| `204`  | Livro removido (sem conteúdo)     |
| `400`  | Parâmetros de paginação inválidos |
| `401`  | Credenciais ausentes ou inválidas |
| `404`  | Livro não encontrado (PUT/DELETE) |
| `409`  | Já existe um livro com esse nome  |
| `422`  | Corpo da requisição inválido      |

---

## 🎓 Contexto de aprendizado

Projeto desenvolvido como exercício prático do curso **Full Stack Python** da [EBAC](https://ebaconline.com.br/), cobrindo:

**API e back-end**

- Criação de APIs REST com FastAPI
- Métodos HTTP: `GET`, `POST`, `PUT`, `DELETE`
- Modelagem de dados e persistência com **SQLAlchemy ORM** + **PostgreSQL**
- Constraints de integridade no banco (`UNIQUE`) e tratamento de `IntegrityError`
- Validação de dados com **Pydantic** e `Field` constraints
- Autenticação com **HTTP Basic Auth** e `compare_digest`
- Validação de configuração na inicialização (fail-fast em variáveis de ambiente ausentes)
- Tratamento de erros com `HTTPException`
- Injeção de dependências com `Depends`
- Paginação de resultados
- Documentação automática via **Swagger UI**
- Arquitetura modular: `auth.py`, `database.py`, `models.py`, `schemas.py`

**Containerização**

- Escrita de `Dockerfile` com aproveitamento de cache de camadas
- Orquestração multi-container com **Docker Compose**
- Rede interna e resolução de serviços por nome (`db` como hostname)
- Mapeamento de portas e resolução de conflitos com serviços locais
- **Volumes nomeados** para persistência de dados vs. **bind mounts** para hot reload
- `healthcheck` + `depends_on: condition: service_healthy` para controle de inicialização
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
