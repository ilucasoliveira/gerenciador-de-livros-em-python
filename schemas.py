from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class SchemaLivro(BaseModel):
    nome: str=Field(min_length=1, max_length=300, description="Título do livro")
    autor: str=Field(min_length=1, max_length=200, description="Nome do autor")
    ano: int=Field(ge=1000, le=date.today().year, description="Ano de publicação")
    sinopse: Optional[str]=Field(default=None, max_length=1000, description="Descrição do livro")

class SchemaBookResponse(SchemaLivro):
    id: int

class SchemaUpdateLivro(SchemaLivro):
    nome: Optional[str]=Field(default=None, min_length=1, max_length=300)
    autor: Optional[str]=Field(default=None, min_length=1, max_length=200)
    ano: Optional[int]=Field(default=None, ge=1000, le=date.today().year)