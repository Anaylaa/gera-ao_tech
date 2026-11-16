
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Carrega as variáveis do arquivo .env
load_dotenv()

# Obtém a URL de conexão com o banco
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("A variável DATABASE_URL não foi configurada.")

# Cria a conexão com o PostgreSQL
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

# Cria uma fábrica de sessões
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Classe base para os modelos do banco
class Base(DeclarativeBase):
    pass


# Disponibiliza uma sessão para as rotas
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
