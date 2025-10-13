import os
import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Union
import requests
import io
from PIL import Image

# --- Configuração Inicial ---
load_dotenv()
app = FastAPI(
    title="Serviço de Análise com Gemini",
    description="Uma API para intermediar requisições para a API do Google Gemini."
)

try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Chave da API do Google não encontrada no .env")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash-lite')

except Exception as e:
    print(f"ERRO CRÍTICO ao inicializar o modelo Gemini: {e}")
    model = None

# --- Modelos de Dados ---

# Modelo para o endpoint de texto simples
class PromptRequest(BaseModel):
    prompt: str

# NOVO MODELO: Apenas para receber URLs de imagens
class ImageAnalysisRequest(BaseModel):
    image_urls: List[HttpUrl]

# --- Endpoint da API ---
@app.post("/prompt-text", tags=["text"])
async def analisar_prompt(request: PromptRequest):
    if not model:
        raise HTTPException(status_code=500, detail="Modelo de IA não inicializado corretamente.")

    try:
        print(f"Recebido prompt: {request.prompt}")
        response = model.generate_content(request.prompt)
        print("Resposta gerada com sucesso.")
        return {"resposta": response.text}
    except Exception as e:
        print(f"Erro ao chamar a API do Gemini: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar o prompt: {e}")

@app.post("/prompt-img-link", tags=["image"])
async def analisar_prompt(request: ImageAnalysisRequest):    
    if not model:
        raise HTTPException(status_code=500, detail="Modelo de IA não inicializado corretamente.")

    # Define o prompt padrão diretamente no código
    prompt_padrao = "Responda com uma única palavra que melhor descreve a imagem."
    content_parts = [prompt_padrao]
    
    try:
        # Itera sobre as URLs das imagens recebidas
        for image_url in request.image_urls:
            # Faz o download da imagem a partir do URL
            response = requests.get(str(image_url), stream=True)
            response.raise_for_status()
            
            # Abre a imagem a partir dos dados baixados (bytes) em memória
            img = Image.open(io.BytesIO(response.content))
            
            # Adiciona o objeto de imagem à lista de partes
            content_parts.append(img)
            
        print(f"Enviando para o Gemini com {len(content_parts)} partes (1 texto + {len(request.image_urls)} imagens).")
        response = model.generate_content(content_parts)
        print("Resposta gerada com sucesso.")
        return {"resposta": response.text}
        
    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar a imagem: {e}")
        raise HTTPException(status_code=400, detail=f"Não foi possível baixar a imagem do URL fornecido: {e}")
    except Exception as e:
        print(f"Erro ao chamar a API do Gemini: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar o prompt: {e}")

@app.get("/", tags=["Health Check"])
async def root():
    return {"status": "API online"}