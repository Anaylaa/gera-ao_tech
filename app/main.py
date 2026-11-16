
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.schemas import (
    EmprestimoCreate,
    EmprestimoResponse,
    LeitorCreate,
    LeitorResponse,
    LivroCreate,
    LivroResponse,
)
from app.services import (
    EmprestimoService,
    LeitorService,
    LivroService,
)

# =========================================================
# CONFIGURAÇÃO DA APLICAÇÃO
# =========================================================

app = FastAPI(
    title="LibraTech API",
    description="Sistema de gerenciamento de biblioteca",
    version="1.0.0",
)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static",
)


# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def tratar_erro_negocio(erro: ValueError):
    mensagem = str(erro)

    if "não encontrado" in mensagem.lower():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=mensagem,
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=mensagem,
    )


# =========================================================
# ROTAS PRINCIPAIS
# =========================================================

@app.get("/", tags=["Sistema"], include_in_schema=False)
def home():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health", tags=["Sistema"])
def health_check():
    return {"status": "ok"}


@app.get("/health/db", tags=["Sistema"])
def health_check_db():
    try:
        with engine.connect() as conexao:
            conexao.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "conectado",
        }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível conectar ao banco de dados.",
        )


# =========================================================
# LIVROS
# =========================================================

@app.post(
    "/livros",
    response_model=LivroResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Livros"],
)
def criar_livro(
    dados: LivroCreate,
    db: Session = Depends(get_db),
):
    try:
        service = LivroService(db)
        return service.criar(dados)

    except ValueError as erro:
        tratar_erro_negocio(erro)


@app.get(
    "/livros",
    response_model=list[LivroResponse],
    tags=["Livros"],
)
def listar_livros(
    db: Session = Depends(get_db),
):
    service = LivroService(db)
    return service.listar()


@app.get(
    "/livros/{livro_id}",
    response_model=LivroResponse,
    tags=["Livros"],
)
def buscar_livro(
    livro_id: int,
    db: Session = Depends(get_db),
):
    try:
        service = LivroService(db)
        livro = service.buscar_por_id(livro_id)

        if livro is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Livro não encontrado.",
            )

        return livro

    except ValueError as erro:
        tratar_erro_negocio(erro)


# =========================================================
# LEITORES
# =========================================================

@app.post(
    "/leitores",
    response_model=LeitorResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Leitores"],
)
def criar_leitor(
    dados: LeitorCreate,
    db: Session = Depends(get_db),
):
    try:
        service = LeitorService(db)
        return service.criar(dados)

    except ValueError as erro:
        tratar_erro_negocio(erro)


@app.get(
    "/leitores",
    response_model=list[LeitorResponse],
    tags=["Leitores"],
)
def listar_leitores(
    db: Session = Depends(get_db),
):
    service = LeitorService(db)
    return service.listar()


@app.get(
    "/leitores/{leitor_id}",
    response_model=LeitorResponse,
    tags=["Leitores"],
)
def buscar_leitor(
    leitor_id: int,
    db: Session = Depends(get_db),
):
    try:
        service = LeitorService(db)
        leitor = service.buscar_por_id(leitor_id)

        if leitor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leitor não encontrado.",
            )

        return leitor

    except ValueError as erro:
        tratar_erro_negocio(erro)


# =========================================================
# EMPRÉSTIMOS
# =========================================================

@app.post(
    "/emprestimos",
    response_model=EmprestimoResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Empréstimos"],
)
def realizar_emprestimo(
    dados: EmprestimoCreate,
    db: Session = Depends(get_db),
):
    try:
        service = EmprestimoService(db)

        return service.realizar_emprestimo(
            livro_id=dados.livro_id,
            leitor_id=dados.leitor_id,
        )

    except ValueError as erro:
        tratar_erro_negocio(erro)


@app.get(
    "/emprestimos",
    response_model=list[EmprestimoResponse],
    tags=["Empréstimos"],
)
def listar_emprestimos(
    db: Session = Depends(get_db),
):
    service = EmprestimoService(db)
    return service.listar()


@app.get(
    "/emprestimos/{emprestimo_id}",
    response_model=EmprestimoResponse,
    tags=["Empréstimos"],
)
def buscar_emprestimo(
    emprestimo_id: int,
    db: Session = Depends(get_db),
):
    try:
        service = EmprestimoService(db)
        emprestimo = service.buscar_por_id(emprestimo_id)

        if emprestimo is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empréstimo não encontrado.",
            )

        return emprestimo

    except ValueError as erro:
        tratar_erro_negocio(erro)


# =========================================================
# DEVOLUÇÃO
# =========================================================

@app.post(
    "/emprestimos/{emprestimo_id}/devolucao",
    response_model=EmprestimoResponse,
    tags=["Empréstimos"],
)
def devolver_livro(
    emprestimo_id: int,
    db: Session = Depends(get_db),
):
    try:
        service = EmprestimoService(db)
        return service.devolver_emprestimo(emprestimo_id)

    except ValueError as erro:
        tratar_erro_negocio(erro)


# =========================================================
# RENOVAÇÃO
# =========================================================

@app.post(
    "/emprestimos/{emprestimo_id}/renovacao",
    response_model=EmprestimoResponse,
    tags=["Empréstimos"],
)
def renovar_emprestimo(
    emprestimo_id: int,
    db: Session = Depends(get_db),
):
    try:
        service = EmprestimoService(db)
        return service.renovar_emprestimo(emprestimo_id)

    except ValueError as erro:
        tratar_erro_negocio(erro)


# =========================================================
# PAGAMENTO DE MULTA
# =========================================================

@app.post(
    "/emprestimos/{emprestimo_id}/pagamento-multa",
    response_model=EmprestimoResponse,
    tags=["Empréstimos"],
)
def pagar_multa(
    emprestimo_id: int,
    db: Session = Depends(get_db),
):
    try:
        service = EmprestimoService(db)
        return service.registrar_pagamento_multa(emprestimo_id)

    except ValueError as erro:
        tratar_erro_negocio(erro)
