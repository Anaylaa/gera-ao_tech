
from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.schemas import LivroCreate
from app.services import LivroService


def test_criar_livro_com_dados_validos():
    livro = LivroCreate(
        titulo="Estatística Básica",
        autor="Wilton Bussab",
        isbn="123456789",
        categoria="Estatística",
        quantidade_total=3
    )

    assert livro.titulo == "Estatística Básica"
    assert livro.quantidade_total == 3


def test_impedir_livro_sem_titulo():
    with pytest.raises(ValidationError):
        LivroCreate(
            titulo="",
            autor="Wilton Bussab",
            isbn="123456789",
            categoria="Estatística",
            quantidade_total=3
        )


def test_impedir_quantidade_total_zero():
    with pytest.raises(ValidationError):
        LivroCreate(
            titulo="Estatística Básica",
            autor="Wilton Bussab",
            isbn="123456789",
            categoria="Estatística",
            quantidade_total=0
        )


def test_impedir_cadastro_de_livro_com_isbn_duplicado(db, livro):
    service = LivroService(db)

    dados = LivroCreate(
        titulo="Outro livro",
        autor="Outro autor",
        isbn=livro.isbn,
        categoria="Teste",
        quantidade_total=2
    )

    with pytest.raises(ValueError, match="ISBN"):
        service.criar(dados)


def test_rollback_quando_ocorre_integrity_error_ao_criar_livro(
    db, monkeypatch
):
    service = LivroService(db)

    dados = LivroCreate(
        titulo="Livro de Teste",
        autor="Autor Teste",
        isbn="123456789",
        categoria="Teste",
        quantidade_total=2
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
        with pytest.raises(ValueError, match="Verifique o ISBN"):
            service.criar(dados)

        rollback.assert_called_once()


def test_rollback_quando_ocorre_erro_inesperado_ao_criar_livro(
    db, monkeypatch
):
    service = LivroService(db)

    dados = LivroCreate(
        titulo="Livro de Teste",
        autor="Autor Teste",
        isbn="123456789",
        categoria="Teste",
        quantidade_total=2
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
