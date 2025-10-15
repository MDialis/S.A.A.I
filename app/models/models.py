from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from ..database import Base

class SexoEnum(str, enum.Enum):
    MASCULINO = "MASCULINO"
    FEMININO = "FEMININO"
    OUTRO = "OUTRO"

# A classe Pessoa não será uma tabela, mas uma classe base para herança.
# No DER, você modelou tabelas separadas com FK, o que é ótimo. Vamos seguir isso.

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    telefone = Column(String, nullable=True)
    data_nascimento = Column(Date)
    data_cadastro = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamento para identificar o tipo de usuário (comum ou nutricionista)
    usuario_comum = relationship("UsuarioComum", back_populates="usuario", uselist=False)
    nutricionista = relationship("Nutricionista", back_populates="usuario", uselist=False)

class UsuarioComum(Base):
    __tablename__ = "usuarios_comuns"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    sexo = Column(Enum(SexoEnum))
    altura = Column(Float) # em cm
    peso = Column(Float)   # em kg
    
    usuario = relationship("Usuario", back_populates="usuario_comum")
    refeicoes = relationship("Refeicao", back_populates="usuario_comum")

class Nutricionista(Base):
    __tablename__ = "nutricionistas"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    cpf = Column(String, unique=True, index=True)
    crn = Column(String, unique=True, index=True) # Conselho Regional de Nutricionistas
    
    usuario = relationship("Usuario", back_populates="nutricionista")
    relatorios_gerados = relationship("Relatorio", back_populates="nutricionista")

class Refeicao(Base):
    __tablename__ = "refeicoes"

    id = Column(Integer, primary_key=True, index=True)
    usuario_comum_id = Column(Integer, ForeignKey("usuarios_comuns.id"))
    data_hora = Column(DateTime, default=datetime.utcnow)
    imagem_url = Column(String, nullable=True) # URL onde a imagem está armazenada
    
    usuario_comum = relationship("UsuarioComum", back_populates="refeicoes")
    itens = relationship("RefeicaoItem", back_populates="refeicao", cascade="all, delete-orphan")

class RefeicaoItem(Base):
    __tablename__ = "refeicao_itens"

    id = Column(Integer, primary_key=True, index=True)
    refeicao_id = Column(Integer, ForeignKey("refeicoes.id"))
    nome_alimento = Column(String, index=True)
    quantidade = Column(Float)
    calorias = Column(Float)
    proteinas = Column(Float)
    carboidratos = Column(Float)
    gordura = Column(Float)
    
    refeicao = relationship("Refeicao", back_populates="itens")

# A tabela de Relatório pode ser adicionada depois, para focar nos primeiros passos.