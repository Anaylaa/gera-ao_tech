
import pytest
from pydantic import ValidationError

from app.schemas import EmprestimoCreate


def test_criar_emprestimo_com_ids_validos():
    emprestimo = EmprestimoCreate(
        livro_id=1,
        leitor_id=1
    )

    assert emprestimo.livro_id == 1
    assert emprestimo.leitor_id == 1


def test_impedir_emprestimo_com_livro_id_zero():
    with pytest.raises(ValidationError):
        EmprestimoCreate(
            livro_id=0,
            leitor_id=1
        )


def test_impedir_emprestimo_com_leitor_id_negativo():
    with pytest.raises(ValidationError):
        EmprestimoCreate(
            livro_id=1,
            leitor_id=-1
        )
