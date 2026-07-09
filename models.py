from typing import Optional
from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass

class Livro(Base):
    __tablename__="livros"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(300))
    autor: Mapped[str] = mapped_column(String(200))
    ano: Mapped[int] = mapped_column(Integer)
    sinopse: Mapped[Optional[str]] = mapped_column(String(1000), default=None)