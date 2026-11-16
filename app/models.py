
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Livro(Base):
    __tablename__ = "livros"

    __table_args__ = (
        CheckConstraint(
            "quantidade_total >= 0",
            name="ck_livro_quantidade_total",
        ),
        CheckConstraint(
            "quantidade_disponivel >= 0 AND quantidade_disponivel <= quantidade_total",
            name="ck_livro_quantidade_disponivel",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    autor: Mapped[str] = mapped_column(String(150), nullable=False)
    isbn: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    categoria: Mapped[str] = mapped_column(String(100), nullable=False)

    quantidade_total: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    quantidade_disponivel: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    emprestimos: Mapped[list["Emprestimo"]] = relationship(
        back_populates="livro"
    )


class Leitor(Base):
    __tablename__ = "leitores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    data_cadastro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    emprestimos: Mapped[list["Emprestimo"]] = relationship(
        back_populates="leitor"
    )


class Emprestimo(Base):
    __tablename__ = "emprestimos"

    __table_args__ = (
        CheckConstraint(
            "renovacoes >= 0 AND renovacoes <= 5",
            name="ck_emprestimo_renovacoes",
        ),
        CheckConstraint(
            "status IN ('ativo', 'devolvido')",
            name="ck_emprestimo_status",
        ),
        CheckConstraint(
            "multa >= 0",
            name="ck_emprestimo_multa",
        ),
        CheckConstraint(
            "status_multa IN ('nao_aplicavel', 'pendente', 'paga')",
            name="ck_emprestimo_status_multa",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    livro_id: Mapped[int] = mapped_column(
        ForeignKey("livros.id", ondelete="RESTRICT"),
        nullable=False,
    )

    leitor_id: Mapped[int] = mapped_column(
        ForeignKey("leitores.id", ondelete="RESTRICT"),
        nullable=False,
    )

    data_emprestimo: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    data_devolucao_prevista: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    data_devolucao_real: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    renovacoes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="ativo",
        nullable=False,
    )

    multa: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    status_multa: Mapped[str] = mapped_column(
        String(20),
        default="nao_aplicavel",
        nullable=False,
    )

    data_pagamento_multa: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    livro: Mapped["Livro"] = relationship(back_populates="emprestimos")
    leitor: Mapped["Leitor"] = relationship(back_populates="emprestimos")

    historico_renovacoes: Mapped[list["Renovacao"]] = relationship(
        back_populates="emprestimo",
        cascade="all, delete-orphan",
    )


class Renovacao(Base):
    __tablename__ = "renovacoes"

    __table_args__ = (
        CheckConstraint(
            "numero_renovacao >= 1 AND numero_renovacao <= 5",
            name="ck_renovacao_numero",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    emprestimo_id: Mapped[int] = mapped_column(
        ForeignKey("emprestimos.id", ondelete="CASCADE"),
        nullable=False,
    )

    numero_renovacao: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    data_renovacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    data_devolucao_anterior: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    data_devolucao_nova: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    emprestimo: Mapped["Emprestimo"] = relationship(
        back_populates="historico_renovacoes"
    )
