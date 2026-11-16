
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LivroCreate(BaseModel):
    titulo: str = Field(min_length=1, max_length=200)
    autor: str = Field(min_length=1, max_length=150)
    isbn: str = Field(min_length=1, max_length=20)
    categoria: str = Field(min_length=1, max_length=100)
    quantidade_total: int = Field(default=1, ge=1)


class LivroResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    autor: str
    isbn: str
    categoria: str
    quantidade_total: int
    quantidade_disponivel: int


class LeitorCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=150)
    email: EmailStr
    telefone: str | None = Field(default=None, max_length=20)


class LeitorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: EmailStr
    telefone: str | None
    data_cadastro: datetime


class EmprestimoCreate(BaseModel):
    livro_id: int = Field(gt=0)
    leitor_id: int = Field(gt=0)



class EmprestimoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    livro_id: int
    leitor_id: int
    data_emprestimo: datetime
    data_devolucao_prevista: date
    data_devolucao_real: date | None
    renovacoes: int
    status: Literal["ativo", "devolvido"]
    multa: Decimal
    status_multa: Literal["nao_aplicavel", "pendente", "paga"]
    data_pagamento_multa: date | None
