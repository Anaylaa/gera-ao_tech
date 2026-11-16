
from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.schemas import LeitorCreate
from app.services import LeitorService


def test_criar_leitor_com_dados_validos():
    leitor = LeitorCreate(
        nome="Maria Silva",
        email="maria@email.com",
        telefone="85999999999"
    )

    assert leitor.nome == "Maria Silva"
    assert leitor.email == "maria@email.com"


def test_impedir_leitor_com_email_invalido():
    with pytest.raises(ValidationError):
        LeitorCreate(
            nome="Maria Silva",
            email="email-invalido",
            telefone="85999999999"
        )


def test_impedir_leitor_sem_nome():
    with pytest.raises(ValidationError):
        LeitorCreate(
            nome="",
            email="maria@email.com",
            telefone="85999999999"
        )


def test_impedir_cadastro_de_leitor_com_email_duplicado(db, leitor):
    service = LeitorService(db)

    dados = LeitorCreate(
        nome="Outro leitor",
        email=leitor.email,
        telefone="85988888888"
    )

    with pytest.raises(ValueError, match="e-mail"):
        service.criar(dados)


def test_rollback_quando_ocorre_integrity_error_ao_criar_leitor(
    db, monkeypatch
):
    service = LeitorService(db)

    dados = LeitorCreate(
        nome="João Silva",
        email="joao@email.com",
        telefone="85999999999"
    )

    erro = IntegrityError(
        "INSERT",
        {},
        Exception("Erro de integridade")
    )

    monkeypatch.setattr(
        service.repository,
        "criar",
        Mock(side_effect=erro)
    )

    with patch.object(db, "rollback", wraps=db.rollback) as rollback:
        with pytest.raises(ValueError, match="Verifique o e-mail"):
            service.criar(dados)

        rollback.assert_called_once()


def test_rollback_quando_ocorre_erro_inesperado_ao_criar_leitor(
    db, monkeypatch
):
    service = LeitorService(db)

    dados = LeitorCreate(
        nome="João Silva",
        email="joao@email.com",
        telefone="85999999999"
    )

    monkeypatch.setattr(
        service.repository,
        "criar",
        Mock(side_effect=RuntimeError("Falha inesperada"))
    )

    with patch.object(db, "rollback", wraps=db.rollback) as rollback:
        with pytest.raises(RuntimeError, match="Falha inesperada"):
            service.criar(dados)

        rollback.assert_called_once()
