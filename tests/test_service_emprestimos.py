
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from app import models
from app.repositories import EmprestimoRepository
from app.services import EmprestimoService


def test_realizar_emprestimo_com_sucesso(db, livro, leitor):
    service = EmprestimoService(db)

    emprestimo = service.realizar_emprestimo(
        livro_id=livro.id,
        leitor_id=leitor.id
    )

    assert emprestimo.id is not None
    assert emprestimo.livro_id == livro.id
    assert emprestimo.leitor_id == leitor.id
    assert emprestimo.status == "ativo"
    assert emprestimo.renovacoes == 0
    assert livro.quantidade_disponivel == 2


def test_impedir_emprestimo_sem_estoque(db, livro, leitor):
    service = EmprestimoService(db)

    livro.quantidade_disponivel = 0
    db.commit()

    with pytest.raises(ValueError, match="exemplares disponíveis"):
        service.realizar_emprestimo(
            livro_id=livro.id,
            leitor_id=leitor.id
        )


def test_renovar_emprestimo_com_sucesso(db, livro, leitor):
    service = EmprestimoService(db)

    emprestimo = service.realizar_emprestimo(
        livro_id=livro.id,
        leitor_id=leitor.id
    )

    data_anterior = emprestimo.data_devolucao_prevista

    emprestimo_renovado = service.renovar_emprestimo(
        emprestimo.id
    )

    assert emprestimo_renovado.renovacoes == 1
    assert emprestimo_renovado.data_devolucao_prevista == (
        data_anterior + timedelta(days=30)
    )


def test_impedir_mais_de_cinco_renovacoes(db, livro, leitor):
    service = EmprestimoService(db)

    emprestimo = service.realizar_emprestimo(
        livro_id=livro.id,
        leitor_id=leitor.id
    )

    for _ in range(5):
        emprestimo = service.renovar_emprestimo(emprestimo.id)

    assert emprestimo.renovacoes == 5

    with pytest.raises(ValueError, match="5"):
        service.renovar_emprestimo(emprestimo.id)


def test_impedir_renovacao_de_emprestimo_atrasado(db, livro, leitor):
    service = EmprestimoService(db)

    emprestimo = service.realizar_emprestimo(
        livro_id=livro.id,
        leitor_id=leitor.id
    )

    emprestimo.data_devolucao_prevista = (
        date.today() - timedelta(days=1)
    )
    db.commit()

    with pytest.raises(ValueError, match="atrasado"):
        service.renovar_emprestimo(emprestimo.id)


def test_devolver_emprestimo_sem_atraso(db, livro, leitor):
    service = EmprestimoService(db)

    emprestimo = service.realizar_emprestimo(
        livro_id=livro.id,
        leitor_id=leitor.id
    )

    emprestimo_devolvido = service.devolver_emprestimo(
        emprestimo.id
    )

    assert emprestimo_devolvido.status == "devolvido"
    assert emprestimo_devolvido.multa == Decimal("0.00")
    assert emprestimo_devolvido.status_multa == "nao_aplicavel"
    assert emprestimo_devolvido.data_devolucao_real == date.today()
    assert livro.quantidade_disponivel == 3


def test_calcular_multa_por_atraso(db, livro, leitor):
    service = EmprestimoService(db)

    emprestimo = service.realizar_emprestimo(
        livro_id=livro.id,
        leitor_id=leitor.id
    )

    emprestimo.data_devolucao_prevista = (
        date.today() - timedelta(days=3)
    )
    db.commit()

    emprestimo_devolvido = service.devolver_emprestimo(
        emprestimo.id
    )

    assert emprestimo_devolvido.status == "devolvido"
    assert emprestimo_devolvido.multa == Decimal("3.00")
    assert emprestimo_devolvido.status_multa == "pendente"
    assert emprestimo_devolvido.data_devolucao_real == date.today()
    assert livro.quantidade_disponivel == 3


def test_registrar_pagamento_de_multa(db, livro, leitor):
    service = EmprestimoService(db)

    emprestimo = service.realizar_emprestimo(
        livro_id=livro.id,
        leitor_id=leitor.id
    )

    emprestimo.data_devolucao_prevista = (
        date.today() - timedelta(days=3)
    )
    db.commit()

    emprestimo = service.devolver_emprestimo(emprestimo.id)

    assert emprestimo.status_multa == "pendente"
    assert emprestimo.multa == Decimal("3.00")

    emprestimo = service.registrar_pagamento_multa(
        emprestimo.id
    )

    assert emprestimo.status_multa == "paga"
    assert emprestimo.data_pagamento_multa == date.today()
    assert emprestimo.multa == Decimal("3.00")


def test_impedir_pagamento_duplicado_de_multa(db, livro, leitor):
    service = EmprestimoService(db)

    emprestimo = service.realizar_emprestimo(
        livro_id=livro.id,
        leitor_id=leitor.id
    )

    emprestimo.data_devolucao_prevista = (
        date.today() - timedelta(days=3)
    )
    db.commit()

    emprestimo = service.devolver_emprestimo(emprestimo.id)

    service.registrar_pagamento_multa(emprestimo.id)

    with pytest.raises(ValueError, match="já foi paga"):
        service.registrar_pagamento_multa(emprestimo.id)


def test_impedir_mais_de_dez_emprestimos_ativos(db, leitor):
    service = EmprestimoService(db)

    livro = models.Livro(
        titulo="Livro para teste de limite",
        autor="Autor Teste",
        isbn="987654321",
        categoria="Teste",
        quantidade_total=11,
        quantidade_disponivel=11
    )

    db.add(livro)
    db.commit()
    db.refresh(livro)

    emprestimos = []

    for _ in range(10):
        emprestimo = service.realizar_emprestimo(
            livro_id=livro.id,
            leitor_id=leitor.id
        )
        emprestimos.append(emprestimo)

    assert len(emprestimos) == 10
    assert livro.quantidade_disponivel == 1

    with pytest.raises(ValueError, match="10"):
        service.realizar_emprestimo(
            livro_id=livro.id,
            leitor_id=leitor.id
        )

    assert livro.quantidade_disponivel == 1


def test_impedir_novo_emprestimo_com_atraso(db, livro, leitor):
    service = EmprestimoService(db)

    emprestimo = service.realizar_emprestimo(
        livro_id=livro.id,
        leitor_id=leitor.id
    )

    emprestimo.data_devolucao_prevista = (
        date.today() - timedelta(days=1)
    )
    db.commit()

    with pytest.raises(ValueError, match="atrasado"):
        service.realizar_emprestimo(
            livro_id=livro.id,
            leitor_id=leitor.id
        )


def test_impedir_devolucao_duplicada(db, livro, leitor):
    service = EmprestimoService(db)

    emprestimo = service.realizar_emprestimo(
        livro_id=livro.id,
        leitor_id=leitor.id
    )

    emprestimo = service.devolver_emprestimo(emprestimo.id)

    assert emprestimo.status == "devolvido"
    assert livro.quantidade_disponivel == 3

    with pytest.raises(ValueError, match="devolvido"):
        service.devolver_emprestimo(emprestimo.id)

    assert livro.quantidade_disponivel == 3


def test_impedir_emprestimo_com_leitor_inexistente(db, livro):
    service = EmprestimoService(db)

    with pytest.raises(ValueError, match="Leitor não encontrado"):
        service.realizar_emprestimo(
            livro_id=livro.id,
            leitor_id=9999
        )


def test_impedir_emprestimo_com_livro_inexistente(db, leitor):
    service = EmprestimoService(db)

    with pytest.raises(ValueError, match="Livro não encontrado"):
        service.realizar_emprestimo(
            livro_id=9999,
            leitor_id=leitor.id
        )


def test_prazo_inicial_do_emprestimo_e_de_trinta_dias(
    db, livro, leitor
):
    service = EmprestimoService(db)

    emprestimo = service.realizar_emprestimo(
        livro_id=livro.id,
        leitor_id=leitor.id
    )

    assert emprestimo.data_devolucao_prevista == (
        date.today() + timedelta(days=30)
    )


def test_registrar_historico_de_renovacao(db, livro, leitor):
    service = EmprestimoService(db)

    emprestimo = service.realizar_emprestimo(
        livro_id=livro.id,
        leitor_id=leitor.id
    )

    data_anterior = emprestimo.data_devolucao_prevista

    emprestimo = service.renovar_emprestimo(emprestimo.id)

    historico = (
        db.query(models.Renovacao)
        .filter_by(emprestimo_id=emprestimo.id)
        .all()
    )

    assert len(historico) == 1
    assert historico[0].numero_renovacao == 1
    assert historico[0].data_devolucao_anterior == data_anterior
    assert historico[0].data_devolucao_nova == (
        data_anterior + timedelta(days=30)
    )


def test_impedir_renovacao_de_emprestimo_devolvido(
    db, livro, leitor
):
    service = EmprestimoService(db)

    emprestimo = service.realizar_emprestimo(
        livro_id=livro.id,
        leitor_id=leitor.id
    )

    emprestimo = service.devolver_emprestimo(emprestimo.id)

    with pytest.raises(ValueError, match="devolvido"):
        service.renovar_emprestimo(emprestimo.id)


def test_devolver_no_dia_do_vencimento_sem_multa(
    db, livro, leitor
):
    service = EmprestimoService(db)

    emprestimo = service.realizar_emprestimo(
        livro_id=livro.id,
        leitor_id=leitor.id
    )

    emprestimo.data_devolucao_prevista = date.today()
    db.commit()

    emprestimo = service.devolver_emprestimo(emprestimo.id)

    assert emprestimo.multa == Decimal("0.00")
    assert emprestimo.status_multa == "nao_aplicavel"


def test_impedir_devolucao_de_emprestimo_inexistente(db):
    service = EmprestimoService(db)

    with pytest.raises(ValueError, match="Empréstimo não encontrado"):
        service.devolver_emprestimo(9999)


def test_impedir_renovacao_de_emprestimo_inexistente(db):
    service = EmprestimoService(db)

    with pytest.raises(ValueError, match="Empréstimo não encontrado"):
        service.renovar_emprestimo(9999)


def test_impedir_pagamento_antes_da_devolucao(
    db, livro, leitor
):
    service = EmprestimoService(db)

    emprestimo = service.realizar_emprestimo(
        livro_id=livro.id,
        leitor_id=leitor.id
    )

    with pytest.raises(ValueError, match="após a devolução"):
        service.registrar_pagamento_multa(emprestimo.id)


def test_impedir_pagamento_sem_multa_pendente(
    db, livro, leitor
):
    service = EmprestimoService(db)

    emprestimo = service.realizar_emprestimo(
        livro_id=livro.id,
        leitor_id=leitor.id
    )

    emprestimo = service.devolver_emprestimo(emprestimo.id)

    with pytest.raises(ValueError, match="multa pendente"):
        service.registrar_pagamento_multa(emprestimo.id)


def test_impedir_pagamento_de_multa_de_emprestimo_inexistente(db):
    service = EmprestimoService(db)

    with pytest.raises(ValueError, match="Empréstimo não encontrado"):
        service.registrar_pagamento_multa(9999)

def test_listar_emprestimos_ativos_por_leitor(db, livro, leitor):
    service = EmprestimoService(db)

    service.realizar_emprestimo(
        livro_id=livro.id,
        leitor_id=leitor.id
    )

    repository = EmprestimoRepository(db)

    emprestimos = repository.listar_ativos_por_leitor(leitor.id)

    assert len(emprestimos) == 1
    assert emprestimos[0].leitor_id == leitor.id
    assert emprestimos[0].status == "ativo"



def test_rollback_quando_ocorre_integrity_error_ao_realizar_emprestimo(
    db, livro, leitor, monkeypatch
):
    service = EmprestimoService(db)

    erro = IntegrityError(
        "INSERT",
        {},
        Exception("Erro de integridade")
    )

    monkeypatch.setattr(
        service.repository,
        "adicionar",
        Mock(side_effect=erro)
    )

    with patch.object(db, "rollback", wraps=db.rollback) as rollback:
        with pytest.raises(
            ValueError,
            match="Não foi possível realizar o empréstimo"
        ):
            service.realizar_emprestimo(
                livro_id=livro.id,
                leitor_id=leitor.id
            )

        rollback.assert_called_once()

    # Confirma que o estoque não foi alterado permanentemente.
    db.refresh(livro)
    assert livro.quantidade_disponivel == 3



def test_impedir_devolucao_quando_livro_associado_nao_e_encontrado(
    db, livro, leitor, monkeypatch
):
    service = EmprestimoService(db)

    emprestimo = service.realizar_emprestimo(
        livro_id=livro.id,
        leitor_id=leitor.id
    )

    monkeypatch.setattr(
        service.livro_repository,
        "buscar_por_id_com_bloqueio",
        Mock(return_value=None)
    )

    with pytest.raises(
        ValueError,
        match="Livro associado ao empréstimo não encontrado"
    ):
        service.devolver_emprestimo(emprestimo.id)

    db.refresh(emprestimo)
    db.refresh(livro)

    assert emprestimo.status == "ativo"
    assert emprestimo.data_devolucao_real is None
    assert livro.quantidade_disponivel == 2
