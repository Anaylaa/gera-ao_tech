
import importlib.util
from unittest.mock import Mock

import pytest

import app.database as database_module
from app.database import get_db


def test_get_db_cria_e_fecha_sessao(monkeypatch):
    sessao_falsa = Mock()

    monkeypatch.setattr(
        "app.database.SessionLocal",
        Mock(return_value=sessao_falsa)
    )

    gerador = get_db()

    # A sessão disponibilizada deve ser a sessão criada.
    sessao = next(gerador)

    assert sessao is sessao_falsa

    # Finaliza o gerador, executando o bloco finally.
    with pytest.raises(StopIteration):
        next(gerador)

    # Confirma que a sessão foi fechada.
    sessao_falsa.close.assert_called_once()


from unittest.mock import patch


def test_impedir_inicializacao_sem_database_url():
    spec = importlib.util.spec_from_file_location(
        "database_sem_configuracao",
        database_module.__file__
    )

    modulo = importlib.util.module_from_spec(spec)

    with (
        patch("os.getenv", return_value=None),
        patch("dotenv.load_dotenv"),
        pytest.raises(
            ValueError,
            match="DATABASE_URL não foi configurada"
        )
    ):
        spec.loader.exec_module(modulo)
