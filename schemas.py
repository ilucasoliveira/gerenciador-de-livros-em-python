from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import date

class SchemaLivro(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    nome: str=Field(min_length=1, max_length=300, description="Título do livro")
    autor: str=Field(min_length=1, max_length=200, description="Nome do autor")
    ano: int=Field(ge=1000, le=date.today().year, description="Ano de publicação")
    sinopse: Optional[str]=Field(default=None, max_length=1000, description="Descrição do livro")

class SchemaLivroResponse(SchemaLivro):
    id: int

class SchemaLivrosOrdenacaoResponse(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int
    livros: list[SchemaLivroResponse]

class SchemaUpdateLivro(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    nome: Optional[str]=Field(default=None, min_length=1, max_length=300)
    autor: Optional[str]=Field(default=None, min_length=1, max_length=200)
    ano: Optional[int]=Field(default=None, ge=1000, le=date.today().year)
    sinopse: Optional[str]=Field(default=None, max_length=1000)

class SchemaUpdateLivroResponse(SchemaUpdateLivro):
    id: int
