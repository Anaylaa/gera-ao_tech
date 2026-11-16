
from datetime import date

from sqlalchemy.orm import Session

from app import models
from app.schemas import LeitorCreate, LivroCreate


class LivroRepository:
    def __init__(self, db: Session):
        self.db = db

    def criar(self, dados: LivroCreate):
        novo_livro = models.Livro(
            titulo=dados.titulo,
            autor=dados.autor,
            isbn=dados.isbn,
            categoria=dados.categoria,
            quantidade_total=dados.quantidade_total,
            quantidade_disponivel=dados.quantidade_total,
        )

        self.db.add(novo_livro)
        self.db.flush()

        return novo_livro

    def listar(self):
        return self.db.query(models.Livro).all()

    def buscar_por_id(self, livro_id: int):
        return (
            self.db.query(models.Livro)
            .filter(models.Livro.id == livro_id)
            .first()
        )

    def buscar_por_id_com_bloqueio(self, livro_id: int):
        return (
            self.db.query(models.Livro)
            .filter(models.Livro.id == livro_id)
            .with_for_update()
            .first()
        )

    def buscar_por_isbn(self, isbn: str):
        return (
            self.db.query(models.Livro)
            .filter(models.Livro.isbn == isbn)
            .first()
        )


class LeitorRepository:
    def __init__(self, db: Session):
        self.db = db

    def criar(self, dados: LeitorCreate):
        novo_leitor = models.Leitor(
            nome=dados.nome,
            email=dados.email,
            telefone=dados.telefone,
        )

        self.db.add(novo_leitor)
        self.db.flush()

        return novo_leitor

    def listar(self):
        return self.db.query(models.Leitor).all()

    def buscar_por_id(self, leitor_id: int):
        return (
            self.db.query(models.Leitor)
            .filter(models.Leitor.id == leitor_id)
            .first()
        )

    def buscar_por_id_com_bloqueio(self, leitor_id: int):
        return (
            self.db.query(models.Leitor)
            .filter(models.Leitor.id == leitor_id)
            .with_for_update()
            .first()
        )

    def buscar_por_email(self, email: str):
        return (
            self.db.query(models.Leitor)
            .filter(models.Leitor.email == email)
            .first()
        )



class EmprestimoRepository:
    def __init__(self, db: Session):
        self.db = db

    def adicionar(self, emprestimo: models.Emprestimo):
        self.db.add(emprestimo)
        self.db.flush()

        return emprestimo

    def listar(self):
        return self.db.query(models.Emprestimo).all()

    def buscar_por_id(self, emprestimo_id: int):
        return (
            self.db.query(models.Emprestimo)
            .filter(models.Emprestimo.id == emprestimo_id)
            .first()
        )

    def buscar_por_id_com_bloqueio(self, emprestimo_id: int):
        return (
            self.db.query(models.Emprestimo)
            .filter(models.Emprestimo.id == emprestimo_id)
            .with_for_update()
            .first()
        )

    def adicionar_renovacao(self, renovacao: models.Renovacao):
        self.db.add(renovacao)
        self.db.flush()

        return renovacao

    def listar_ativos_por_leitor(self, leitor_id: int):
        return (
            self.db.query(models.Emprestimo)
            .filter(
                models.Emprestimo.leitor_id == leitor_id,
                models.Emprestimo.status == "ativo",
            )
            .all()
        )

    def contar_ativos_por_leitor(self, leitor_id: int):
        return (
            self.db.query(models.Emprestimo)
            .filter(
                models.Emprestimo.leitor_id == leitor_id,
                models.Emprestimo.status == "ativo",
            )
            .count()
        )

    def listar_atrasados_por_leitor(
        self,
        leitor_id: int,
        hoje: date,
    ):
        return (
            self.db.query(models.Emprestimo)
            .filter(
                models.Emprestimo.leitor_id == leitor_id,
                models.Emprestimo.status == "ativo",
                models.Emprestimo.data_devolucao_prevista < hoje,
            )
            .all()
        )
