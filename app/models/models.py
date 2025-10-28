from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

import enum

class SexoEnum(str, enum.Enum):
    MASCULINO = "MASCULINO"
    FEMININO = "FEMININO"
    OUTRO = "OUTRO"

# NOVO: Um enum para o status do relatório
class StatusRelatorioEnum(str, enum.Enum):
    PENDENTE = "PENDENTE"
    REVISADO = "REVISADO"
    APROVADO = "APROVADO"

# NOVO: A tabela para os Relatórios
class Relatorio(Base):
    __tablename__ = "relatorios"

    id = Column(Integer, primary_key=True, index=True)
    usuario_comum_id = Column(Integer, ForeignKey("usuarios_comuns.id"))
    nutricionista_id = Column(Integer, ForeignKey("nutricionistas.id"))
    
    periodo_inicio = Column(Date, nullable=False)
    periodo_fim = Column(Date, nullable=False)
    
    # Este é o relatório gerado automaticamente pela IA/sistema
    resumo_automatico = Column(Text, nullable=True) 
    
    # Este é o campo que o nutricionista edita
    comentarios_nutricionista = Column(Text, nullable=True)
    
    status = Column(Enum(StatusRelatorioEnum), default=StatusRelatorioEnum.PENDENTE)
    data_criacao = Column(DateTime, default=datetime.utcnow)
    data_aprovacao = Column(DateTime, nullable=True)

    # Relacionamentos
    usuario_comum = relationship("UsuarioComum")
    nutricionista = relationship("Nutricionista")

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
#   relatorios_gerados = relationship("Relatorio", back_populates="nutricionista")

class Refeicao(Base):
    __tablename__ = "refeicoes"

    id = Column(Integer, primary_key=True, index=True)
    usuario_comum_id = Column(Integer, ForeignKey("usuarios_comuns.id"))
    data_hora = Column(DateTime, default=datetime.utcnow)
    imagem_url = Column(String, nullable=True) # URL onde a imagem está armazenada
    llm_raw_response = Column(JSONB, nullable=True) # Para salvar o JSON bruto da IA
    
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