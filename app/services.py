
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.repositories import (
    EmprestimoRepository,
    LeitorRepository,
    LivroRepository,
)
from app.schemas import LeitorCreate, LivroCreate


class LivroService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = LivroRepository(db)

    def criar(self, dados: LivroCreate):
        livro_existente = self.repository.buscar_por_isbn(dados.isbn)

        if livro_existente:
            raise ValueError("Já existe um livro cadastrado com esse ISBN.")

        try:
            novo_livro = self.repository.criar(dados)

            self.db.commit()
            self.db.refresh(novo_livro)

            return novo_livro

        except IntegrityError:
            self.db.rollback()
            raise ValueError(
                "Não foi possível cadastrar o livro. Verifique o ISBN."
            )

        except Exception:
            self.db.rollback()
            raise

    def listar(self):
        return self.repository.listar()

    def buscar_por_id(self, livro_id: int):
        return self.repository.buscar_por_id(livro_id)


class LeitorService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = LeitorRepository(db)

    def criar(self, dados: LeitorCreate):
        leitor_existente = self.repository.buscar_por_email(dados.email)

        if leitor_existente:
            raise ValueError("Já existe um leitor cadastrado com esse e-mail.")

        try:
            novo_leitor = self.repository.criar(dados)

            self.db.commit()
            self.db.refresh(novo_leitor)

            return novo_leitor

        except IntegrityError:
            self.db.rollback()
            raise ValueError(
                "Não foi possível cadastrar o leitor. Verifique o e-mail."
            )

        except Exception:
            self.db.rollback()
            raise

    def listar(self):
        return self.repository.listar()

    def buscar_por_id(self, leitor_id: int):
        return self.repository.buscar_por_id(leitor_id)


class EmprestimoService:
    PRAZO_EMPRESTIMO = 30
    LIMITE_EMPRESTIMOS = 10
    LIMITE_RENOVACOES = 5
    VALOR_MULTA_DIA = Decimal("1.00")

    def __init__(self, db: Session):
        self.db = db
        self.livro_repository = LivroRepository(db)
        self.leitor_repository = LeitorRepository(db)
        self.repository = EmprestimoRepository(db)

    def realizar_emprestimo(self, livro_id: int, leitor_id: int):
        try:
            # 1. Busca e bloqueia o leitor.
            leitor = self.leitor_repository.buscar_por_id_com_bloqueio(
                leitor_id
            )

            if not leitor:
                raise ValueError("Leitor não encontrado.")

            # 2. Verifica se o leitor possui empréstimos atrasados.
            hoje = date.today()

            emprestimos_atrasados = (
                self.repository.listar_atrasados_por_leitor(
                    leitor_id,
                    hoje,
                )
            )

            if emprestimos_atrasados:
                raise ValueError(
                    "Leitor possui empréstimos atrasados e não pode "
                    "realizar novos empréstimos."
                )

            # 3. Verifica o limite de empréstimos ativos.
            quantidade_ativos = (
                self.repository.contar_ativos_por_leitor(leitor_id)
            )

            if quantidade_ativos >= self.LIMITE_EMPRESTIMOS:
                raise ValueError(
                    "Leitor atingiu o limite de 10 empréstimos ativos."
                )

            # 4. Busca e bloqueia o livro.
            livro = self.livro_repository.buscar_por_id_com_bloqueio(
                livro_id
            )

            if not livro:
                raise ValueError("Livro não encontrado.")

            if livro.quantidade_disponivel <= 0:
                raise ValueError(
                    "Não existem exemplares disponíveis deste livro."
                )

            # 5. Define as datas do empréstimo.
            data_emprestimo = date.today()
            data_devolucao = data_emprestimo + timedelta(
                days=self.PRAZO_EMPRESTIMO
            )

            # 6. Cria o empréstimo.
            novo_emprestimo = models.Emprestimo(
                livro_id=livro_id,
                leitor_id=leitor_id,
                data_devolucao_prevista=data_devolucao,
                renovacoes=0,
                status="ativo",
                multa=Decimal("0.00"),
                status_multa="nao_aplicavel",
            )

            self.repository.adicionar(novo_emprestimo)

            # 7. Atualiza a quantidade disponível.
            livro.quantidade_disponivel -= 1

            # 8. Confirma a transação.
            self.db.commit()
            self.db.refresh(novo_emprestimo)

            return novo_emprestimo

        except IntegrityError:
            self.db.rollback()
            raise ValueError(
                "Não foi possível realizar o empréstimo."
            )

        except Exception:
            self.db.rollback()
            raise

    def listar(self):
        return self.repository.listar()

    def buscar_por_id(self, emprestimo_id: int):
        return self.repository.buscar_por_id(emprestimo_id)

    def devolver_emprestimo(self, emprestimo_id: int):
        try:
            # 1. Busca o empréstimo e bloqueia sua alteração.
            emprestimo = self.repository.buscar_por_id_com_bloqueio(
                emprestimo_id
            )

            if not emprestimo:
                raise ValueError("Empréstimo não encontrado.")

            # 2. Verifica se o empréstimo já foi devolvido.
            if emprestimo.status == "devolvido":
                raise ValueError("Este empréstimo já foi devolvido.")

            # 3. Busca e bloqueia o livro.
            livro = self.livro_repository.buscar_por_id_com_bloqueio(
                emprestimo.livro_id
            )

            if not livro:
                raise ValueError(
                    "Livro associado ao empréstimo não encontrado."
                )

            # 4. Registra a data da devolução.
            hoje = date.today()

            emprestimo.data_devolucao_real = hoje
            emprestimo.status = "devolvido"

            # 5. Calcula os dias de atraso.
            dias_atraso = (
                hoje - emprestimo.data_devolucao_prevista
            ).days

            # 6. Calcula a multa, se houver atraso.
            if dias_atraso > 0:
                emprestimo.multa = (
                    Decimal(dias_atraso) * self.VALOR_MULTA_DIA
                )
                emprestimo.status_multa = "pendente"
            else:
                emprestimo.multa = Decimal("0.00")
                emprestimo.status_multa = "nao_aplicavel"

            # 7. Devolve o exemplar ao estoque.
            livro.quantidade_disponivel += 1

            # 8. Confirma as alterações.
            self.db.commit()
            self.db.refresh(emprestimo)

            return emprestimo

        except Exception:
            self.db.rollback()
            raise

    def renovar_emprestimo(self, emprestimo_id: int):
        try:
            # 1. Busca o empréstimo e bloqueia sua alteração.
            emprestimo = self.repository.buscar_por_id_com_bloqueio(
                emprestimo_id
            )

            if not emprestimo:
                raise ValueError("Empréstimo não encontrado.")

            # 2. Verifica se o empréstimo ainda está ativo.
            if emprestimo.status != "ativo":
                raise ValueError(
                    "Não é possível renovar um empréstimo já devolvido."
                )

            # 3. Verifica se o empréstimo está atrasado.
            hoje = date.today()

            if emprestimo.data_devolucao_prevista < hoje:
                raise ValueError(
                    "Empréstimos atrasados não podem ser renovados."
                )

            # 4. Verifica o limite de renovações.
            if emprestimo.renovacoes >= self.LIMITE_RENOVACOES:
                raise ValueError(
                    "Este empréstimo já atingiu o limite de 5 renovações."
                )

            # 5. Guarda a data anterior.
            data_anterior = emprestimo.data_devolucao_prevista

            # 6. Acrescenta 30 dias à data prevista atual.
            nova_data = data_anterior + timedelta(
                days=self.PRAZO_EMPRESTIMO
            )

            # 7. Cria o registro do histórico.
            nova_renovacao = models.Renovacao(
                emprestimo_id=emprestimo.id,
                numero_renovacao=emprestimo.renovacoes + 1,
                data_devolucao_anterior=data_anterior,
                data_devolucao_nova=nova_data,
            )

            self.repository.adicionar_renovacao(nova_renovacao)

            # 8. Atualiza o empréstimo.
            emprestimo.data_devolucao_prevista = nova_data
            emprestimo.renovacoes += 1

            # 9. Confirma a transação.
            self.db.commit()
            self.db.refresh(emprestimo)

            return emprestimo

        except Exception:
            self.db.rollback()
            raise

    def registrar_pagamento_multa(self, emprestimo_id: int):
        try:
            # 1. Busca o empréstimo e bloqueia sua alteração.
            emprestimo = self.repository.buscar_por_id_com_bloqueio(
                emprestimo_id
            )

            if not emprestimo:
                raise ValueError("Empréstimo não encontrado.")

            # 2. Verifica se o empréstimo já foi devolvido.
            if emprestimo.status != "devolvido":
                raise ValueError(
                    "A multa só pode ser paga após a devolução do livro."
                )

            # 3. Verifica se existe multa pendente.
            if emprestimo.status_multa == "paga":
                raise ValueError("Esta multa já foi paga.")

            if emprestimo.status_multa != "pendente":
                raise ValueError(
                    "Este empréstimo não possui multa pendente."
                )

            # 4. Registra o pagamento.
            emprestimo.status_multa = "paga"
            emprestimo.data_pagamento_multa = date.today()

            # 5. Confirma as alterações.
            self.db.commit()
            self.db.refresh(emprestimo)

            return emprestimo

        except Exception:
            self.db.rollback()
            raise
