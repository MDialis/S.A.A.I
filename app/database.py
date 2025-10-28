import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

# Cria uma SessionLocal que usaremos para interagir com o banco
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para nossos modelos declarativos do SQLAlchemy
Base = declarative_base()

# Função para injetar a dependência da sessão do banco de dados nos endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()