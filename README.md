# 📚 Gerenciador de Livros — API REST com FastAPI

API RESTful de gerenciamento de livros desenvolvida com **FastAPI**, **SQLAlchemy** e **PostgreSQL**, como projeto prático do curso **Full Stack Python da EBAC**.

---

## 🧠 Sobre o projeto

Este projeto simula o back-end de uma livraria, expondo endpoints CRUD para gerenciar um catálogo de livros. O armazenamento é feito em um banco de dados **PostgreSQL**, com persistência real via **SQLAlchemy ORM**, permitindo o foco no aprendizado de FastAPI, SQLAlchemy, Pydantic, autenticação HTTP Basic e boas práticas de arquitetura de API REST.

---

## 🚀 Tecnologias utilizadas

- [Python 3.14+](https://www.python.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/) — ORM
- [PostgreSQL](https://www.postgresql.org/) (via `psycopg2-binary`)
- [Pydantic](https://docs.pydantic.dev/)
- [python-dotenv](https://pypi.org/project/python-dotenv/) — gerenciamento de variáveis de ambiente
- [Poetry](https://python-poetry.org/) — gerenciamento de dependências
- Swagger UI (embutido no FastAPI) — documentação interativa

---

## 📋 Funcionalidades

| Método | Endpoint          | Descrição                     | Auth |
| ------ | ----------------- | ----------------------------- | ---- |
| GET    | `/ler`            | Lista os livros com paginação | ✅   |
| POST   | `/adicionar`      | Adiciona um novo livro        | ✅   |
| PUT    | `/atualizar/{id}` | Atualiza dados de um livro    | ✅   |
| DELETE | `/deletar/{id}`   | Remove um livro pelo ID       | ✅   |

> Todos os endpoints requerem autenticação via **HTTP Basic Auth**.

---

## 🔐 Autenticação

A API utiliza **HTTP Basic Authentication**, com as credenciais carregadas de variáveis de ambiente (nada fixo no código).

Configure no seu `.env`:

```
MEU_USUARIO=seu_usuario
MINHA_SENHA=sua_senha
```

---

## 🗂️ Estrutura do projeto

```
gerenciador-de-livros-em-python/
├── main.py           # Rotas e lógica dos endpoints
├── auth.py           # Autenticação HTTP Basic
├── database.py        # Configuração da engine e sessão do SQLAlchemy
├── models.py          # Modelo ORM (tabela Livro)
├── schemas.py         # Schemas Pydantic (validação de entrada/saída)
├── create_table.py    # Script para criar as tabelas no banco
├── pyproject.toml     # Configuração do projeto e dependências (Poetry)
├── poetry.lock        # Lock file das dependências
├── .env                # Variáveis de ambiente (não versionado)
└── README.md
```

---

## ⚙️ Como executar localmente

### Pré-requisitos

- Python 3.14+
- [Poetry](https://python-poetry.org/docs/#installation) instalado
- PostgreSQL rodando localmente (ou acessível remotamente)

### Passo a passo

```bash
# 1. Clone o repositório
git clone https://github.com/ilucasoliveira/gerenciador-de-livros-em-python.git
cd gerenciador-de-livros-em-python

# 2. Instale as dependências
poetry install

# 3. Ative o ambiente virtual
poetry shell

# 4. Crie o arquivo .env na raiz do projeto
echo "DATABASE_URL=postgresql://usuario:senha@localhost:5432/nome_do_banco" >> .env
echo "MEU_USUARIO=seu_usuario" >> .env
echo "MINHA_SENHA=sua_senha" >> .env

# 5. Crie as tabelas no banco
python create_table.py

# 6. Inicie o servidor
fastapi dev main.py
```

A API estará disponível em: `http://127.0.0.1:8000`

---

## 📖 Documentação interativa

Após subir o servidor, acesse a documentação **Swagger UI** gerada automaticamente pelo FastAPI:

```
http://127.0.0.1:8000/docs
```

Lá você pode visualizar e testar todos os endpoints diretamente pelo navegador.

---

## 📦 Exemplos de uso

> As credenciais no header `Authorization` variam de acordo com o que você definir no seu `.env`.

### Adicionar um livro

```http
POST /adicionar
Authorization: Basic <seu_usuario_e_senha_em_base64>
Content-Type: application/json

{
  "nome": "O Senhor dos Anéis",
  "autor": "J.R.R. Tolkien",
  "ano": 1954,
  "sinopse": "A jornada de Frodo para destruir o Um Anel."
}
```

### Listar livros (com paginação)

```http
GET /ler?page=1&limit=10
Authorization: Basic <seu_usuario_e_senha_em_base64>
```

### Atualizar um livro

```http
PUT /atualizar/1
Authorization: Basic <seu_usuario_e_senha_em_base64>
Content-Type: application/json

{
  "sinopse": "Uma épica aventura pela Terra Média."
}
```

### Deletar um livro

```http
DELETE /deletar/1
Authorization: Basic <seu_usuario_e_senha_em_base64>
```

---

## 📐 Modelo de dados

### Livro (criação)

| Campo   | Tipo     | Obrigatório | Descrição         |
| ------- | -------- | ----------- | ----------------- |
| nome    | `string` | ✅          | Título do livro   |
| autor   | `string` | ✅          | Nome do autor     |
| ano     | `int`    | ✅          | Ano de publicação |
| sinopse | `string` | ❌          | Resumo do livro   |

### UpdateLivro (atualização parcial)

Todos os campos são opcionais, permitindo atualizações parciais (PATCH-like via PUT).

---

## 🎓 Contexto de aprendizado

Projeto desenvolvido como exercício prático do curso **Full Stack Python** da [EBAC](https://ebaconline.com.br/), cobrindo os seguintes conceitos:

- Criação de APIs REST com FastAPI
- Métodos HTTP: `GET`, `POST`, `PUT`, `DELETE`
- Modelagem de dados e persistência com **SQLAlchemy ORM** + **PostgreSQL**
- Validação de dados com **Pydantic** e `Field` constraints
- Autenticação com **HTTP Basic Auth** e `compare_digest`
- Gerenciamento de variáveis de ambiente com **python-dotenv**
- Arquitetura modular: separação de responsabilidades em `auth.py`, `database.py`, `models.py`, `schemas.py`
- Tratamento de erros com `HTTPException`
- Injeção de dependências com `Depends`
- Paginação de resultados
- Documentação automática via **Swagger UI**
- Gerenciamento de projeto com **Poetry**

---

## 👤 Autor

**Lucas de Oliveira**
GitHub: [ilucasoliveira](https://github.com/ilucasoliveira)
LinkedIn: [linkedin.com/in/ilucasoliveira/](https://www.linkedin.com/in/ilucasoliveira/)

---

## 📄 Licença

Este projeto é de uso educacional e não possui licença formal.
