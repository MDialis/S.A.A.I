# --- Importações de Bibliotecas ---
#   from typing import List
#   from dotenv import load_dotenv
#   from pydantic import BaseModel, HttpUrl

import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .database import engine
from .models import models as models_db
from .api import refeicoes, relatorios

models_db.Base.metadata.create_all(bind=engine)

os.makedirs("uploads", exist_ok=True)

app = FastAPI(                                                  # Inicializa a aplicação FastAPI com metadados para a documentação
    title="Sistema de Acompanhamento Alimentar Inteligente",
    description="Backend para o TCC de Análise e Desenvolvimento de Sistemas.",
    version="1.0.0"
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(refeicoes.router)
app.include_router(relatorios.router)

@app.get("/", tags=["Health Check"])                            # Endpoint de verificação de saúde (health check) para confirmar que a API está online.
async def root():
    return {"status": "API online e conectada ao banco de dados"}

""" 
# --- Configuração Inicial ---
load_dotenv()                                                   # Carrega as variáveis de ambiente do arquivo .env (ex: GEMINI_API_KEY)

DATA_DIR = "analises_json"                                      # Define o diretório onde os resultados das análises (JSONs) serão salvos.
os.makedirs(DATA_DIR, exist_ok=True)                            # O diretório é criado se ainda não existir.

# --- Modelos de Dados ---

# Modelo para o endpoint de texto simples
class PromptRequest(BaseModel):
    prompt: str

# Modelo para endpoint de URLs de imagens
class ImageAnalysisRequest(BaseModel):
    image_urls: List[HttpUrl]                                   # Garante que a lista contém apenas URLs válidas
"""