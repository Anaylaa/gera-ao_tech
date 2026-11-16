from datetime import date, timedelta
from unittest.mock import patch

from sqlalchemy.exc import SQLAlchemyError

from app import models


def test_rota_inicial(client):
    resposta = client.get("/")

    assert resposta.status_code == 200
    assert "text/html" in resposta.headers["content-type"]
    assert "<!DOCTYPE html>" in resposta.text


def test_rota_health(client):
    resposta = client.get("/health")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_cadastrar_livro_pela_api(client):
    dados = {
        "titulo": "Banco de Dados",
        "autor": "Carlos Silva",
        "isbn": "987654321",
        "categoria": "Tecnologia",
        "quantidade_total": 5
    }

    resposta = client.post("/livros", json=dados)

    assert resposta.status_code in (200, 201)
    assert resposta.json()["titulo"] == "Banco de Dados"
    assert resposta.json()["quantidade_total"] == 5


def test_listar_livros_pela_api(client, livro):
    resposta = client.get("/livros")

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["titulo"] == "Estatística Básica"


def test_buscar_livro_por_id_pela_api(client, livro):
    resposta = client.get(f"/livros/{livro.id}")

    assert resposta.status_code == 200
    assert resposta.json()["id"] == livro.id
    assert resposta.json()["titulo"] == "Estatística Básica"


def test_cadastrar_leitor_pela_api(client):
    dados = {
        "nome": "João Santos",
        "email": "joao@email.com",
        "telefone": "85988888888"
    }

    resposta = client.post("/leitores", json=dados)

    assert resposta.status_code in (200, 201)
    assert resposta.json()["nome"] == "João Santos"
    assert resposta.json()["email"] == "joao@email.com"


def test_listar_leitores_pela_api(client, leitor):
    resposta = client.get("/leitores")

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["nome"] == "Maria Silva"


def test_buscar_leitor_por_id_pela_api(client, leitor):
    resposta = client.get(f"/leitores/{leitor.id}")

    assert resposta.status_code == 200
    assert resposta.json()["id"] == leitor.id
    assert resposta.json()["nome"] == "Maria Silva"


def test_realizar_emprestimo_pela_api(client, livro, leitor):
    dados = {
        "livro_id": livro.id,
        "leitor_id": leitor.id
    }

    resposta = client.post("/emprestimos", json=dados)

    assert resposta.status_code in (200, 201)

    resultado = resposta.json()

    assert resultado["livro_id"] == livro.id
    assert resultado["leitor_id"] == leitor.id
    assert resultado["status"] == "ativo"
    assert resultado["renovacoes"] == 0


def test_listar_emprestimos_pela_api(client, livro, leitor):
    dados = {
        "livro_id": livro.id,
        "leitor_id": leitor.id
    }

    client.post("/emprestimos", json=dados)

    resposta = client.get("/emprestimos")

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["status"] == "ativo"


def test_buscar_emprestimo_por_id_pela_api(client, livro, leitor):
    dados = {
        "livro_id": livro.id,
        "leitor_id": leitor.id
    }

    criacao = client.post("/emprestimos", json=dados)
    emprestimo_id = criacao.json()["id"]

    resposta = client.get(f"/emprestimos/{emprestimo_id}")

    assert resposta.status_code == 200
    assert resposta.json()["id"] == emprestimo_id
    assert resposta.json()["status"] == "ativo"


def test_renovar_emprestimo_pela_api(client, livro, leitor):
    dados = {
        "livro_id": livro.id,
        "leitor_id": leitor.id
    }

    criacao = client.post("/emprestimos", json=dados)
    emprestimo_id = criacao.json()["id"]

    resposta = client.post(
        f"/emprestimos/{emprestimo_id}/renovacao"
    )

    assert resposta.status_code == 200
    assert resposta.json()["renovacoes"] == 1


def test_devolver_emprestimo_pela_api(client, livro, leitor):
    dados = {
        "livro_id": livro.id,
        "leitor_id": leitor.id
    }

    criacao = client.post("/emprestimos", json=dados)
    emprestimo_id = criacao.json()["id"]

    resposta = client.post(
        f"/emprestimos/{emprestimo_id}/devolucao"
    )

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "devolvido"
    assert resposta.json()["multa"] == "0.00"
    assert resposta.json()["status_multa"] == "nao_aplicavel"



def test_devolver_livro_com_atraso_pela_api(client, db, livro, leitor):
    dados = {
        "livro_id": livro.id,
        "leitor_id": leitor.id
    }

    criacao = client.post("/emprestimos", json=dados)
    emprestimo_id = criacao.json()["id"]

    emprestimo = db.get(models.Emprestimo, emprestimo_id)
    emprestimo.data_devolucao_prevista = (
        date.today() - timedelta(days=3)
    )
    db.commit()

    resposta = client.post(
        f"/emprestimos/{emprestimo_id}/devolucao"
    )

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "devolvido"
    assert resposta.json()["multa"] == "3.00"
    assert resposta.json()["status_multa"] == "pendente"


def test_pagar_multa_pela_api(client, db, livro, leitor):
    dados = {
        "livro_id": livro.id,
        "leitor_id": leitor.id
    }

    criacao = client.post("/emprestimos", json=dados)
    emprestimo_id = criacao.json()["id"]

    emprestimo = db.get(models.Emprestimo, emprestimo_id)
    emprestimo.data_devolucao_prevista = (
        date.today() - timedelta(days=3)
    )
    db.commit()

    client.post(f"/emprestimos/{emprestimo_id}/devolucao")

    resposta = client.post(
        f"/emprestimos/{emprestimo_id}/pagamento-multa"
    )

    assert resposta.status_code == 200
    assert resposta.json()["status_multa"] == "paga"
    assert resposta.json()["multa"] == "3.00"
    assert resposta.json()["data_pagamento_multa"] == str(date.today())


def test_impedir_pagamento_duplicado_pela_api(
    client, db, livro, leitor
):
    dados = {
        "livro_id": livro.id,
        "leitor_id": leitor.id
    }

    criacao = client.post("/emprestimos", json=dados)
    emprestimo_id = criacao.json()["id"]

    emprestimo = db.get(models.Emprestimo, emprestimo_id)
    emprestimo.data_devolucao_prevista = (
        date.today() - timedelta(days=3)
    )
    db.commit()

    client.post(f"/emprestimos/{emprestimo_id}/devolucao")

    primeira_resposta = client.post(
        f"/emprestimos/{emprestimo_id}/pagamento-multa"
    )

    assert primeira_resposta.status_code == 200

    segunda_resposta = client.post(
        f"/emprestimos/{emprestimo_id}/pagamento-multa"
    )

    assert segunda_resposta.status_code == 400
    assert "já foi paga" in segunda_resposta.json()["detail"].lower()


def test_impedir_pagamento_antes_da_devolucao_pela_api(
    client, livro, leitor
):
    dados = {
        "livro_id": livro.id,
        "leitor_id": leitor.id
    }

    criacao = client.post("/emprestimos", json=dados)
    emprestimo_id = criacao.json()["id"]

    resposta = client.post(
        f"/emprestimos/{emprestimo_id}/pagamento-multa"
    )

    assert resposta.status_code == 400
    assert "após a devolução" in resposta.json()["detail"].lower()


def test_impedir_devolucao_duplicada_pela_api(
    client, livro, leitor
):
    dados = {
        "livro_id": livro.id,
        "leitor_id": leitor.id
    }

    criacao = client.post("/emprestimos", json=dados)
    emprestimo_id = criacao.json()["id"]

    primeira_resposta = client.post(
        f"/emprestimos/{emprestimo_id}/devolucao"
    )

    assert primeira_resposta.status_code == 200

    segunda_resposta = client.post(
        f"/emprestimos/{emprestimo_id}/devolucao"
    )

    assert segunda_resposta.status_code == 400
    assert "devolvido" in segunda_resposta.json()["detail"].lower()


def test_buscar_livro_inexistente_pela_api(client):
    resposta = client.get("/livros/999")

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Livro não encontrado."


def test_buscar_leitor_inexistente_pela_api(client):
    resposta = client.get("/leitores/999")

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Leitor não encontrado."


def test_buscar_emprestimo_inexistente_pela_api(client):
    resposta = client.get("/emprestimos/999")

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Empréstimo não encontrado."

def test_impedir_cadastro_de_livro_com_isbn_duplicado_pela_api(client, livro):
    dados = {
        "titulo": "Outro livro",
        "autor": "Outro autor",
        "isbn": livro.isbn,
        "categoria": "Tecnologia",
        "quantidade_total": 2
    }

    resposta = client.post("/livros", json=dados)

    assert resposta.status_code == 400
    assert "ISBN" in resposta.json()["detail"]


def test_impedir_cadastro_de_leitor_com_email_duplicado_pela_api(client, leitor):
    dados = {
        "nome": "Outro leitor",
        "email": leitor.email,
        "telefone": "85988888888"
    }

    resposta = client.post("/leitores", json=dados)

    assert resposta.status_code == 400
    assert "e-mail" in resposta.json()["detail"]


def test_impedir_emprestimo_com_livro_inexistente_pela_api(client, leitor):
    dados = {
        "livro_id": 999,
        "leitor_id": leitor.id
    }

    resposta = client.post("/emprestimos", json=dados)

    assert resposta.status_code == 404
    assert "Livro não encontrado" in resposta.json()["detail"]


def test_impedir_emprestimo_com_leitor_inexistente_pela_api(client, livro):
    dados = {
        "livro_id": livro.id,
        "leitor_id": 999
    }

    resposta = client.post("/emprestimos", json=dados)

    assert resposta.status_code == 404
    assert "Leitor não encontrado" in resposta.json()["detail"]



def test_rota_health_db(client):
    resposta = client.get("/health/db")

    assert resposta.status_code == 200
    assert resposta.json() == {
        "status": "ok",
        "database": "conectado"
    }

def test_rota_health_db_quando_banco_indisponivel(client):
    with patch(
        "app.main.engine.connect",
        side_effect=SQLAlchemyError("Falha de conexão")
    ):
        resposta = client.get("/health/db")

    assert resposta.status_code == 503
    assert resposta.json() == {
        "detail": "Não foi possível conectar ao banco de dados."
    }

def test_impedir_pagamento_de_multa_sem_pendencia_pela_api(
    client, livro, leitor
):
    dados = {
        "livro_id": livro.id,
        "leitor_id": leitor.id
    }

    criacao = client.post("/emprestimos", json=dados)
    emprestimo_id = criacao.json()["id"]

    devolucao = client.post(
        f"/emprestimos/{emprestimo_id}/devolucao"
    )

    assert devolucao.status_code == 200
    assert devolucao.json()["status_multa"] == "nao_aplicavel"

    resposta = client.post(
        f"/emprestimos/{emprestimo_id}/pagamento-multa"
    )

    assert resposta.status_code == 400

def test_impedir_renovacao_de_emprestimo_devolvido_pela_api(
    client, livro, leitor
):
    dados = {
        "livro_id": livro.id,
        "leitor_id": leitor.id
    }

    criacao = client.post("/emprestimos", json=dados)
    emprestimo_id = criacao.json()["id"]

    devolucao = client.post(
        f"/emprestimos/{emprestimo_id}/devolucao"
    )

    assert devolucao.status_code == 200

    resposta = client.post(
        f"/emprestimos/{emprestimo_id}/renovacao"
    )

    assert resposta.status_code == 400
    assert "devolvido" in resposta.json()["detail"].lower()