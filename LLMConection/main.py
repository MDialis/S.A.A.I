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
    # Se a configuração falhar, a API não deve iniciar corretamente.
    # Em um sistema real, logaríamos este erro.
    print(f"ERRO CRÍTICO ao inicializar o modelo Gemini: {e}")
    model = None

# --- Modelo de Dados para a Requisição ---
class PromptRequest(BaseModel):
    prompt: str
    
class ImagePart(BaseModel):
    image_url: HttpUrl                                                  # Usamos HttpUrl do pydantic para validar que é uma URL válida

class TextPart(BaseModel):
    text: str

class MultimodalPromptRequest(BaseModel):
    # Optional[str] é para o prompt de texto, se for enviado separadamente das 'parts'
    parts: List[Union[TextPart, ImagePart]]
    
    # Um prompt de texto geral para a imagem, se houver
    global_text_prompt: Optional[str] = 'Answer with 1 word, the word that best describes the image you received or "pancakes" if you received no images in this prompt.'

# --- Função Auxiliar para Carregar Imagens ---
def create_image_part_from_url(image_url: HttpUrl):
    # Opcional: Você pode adicionar uma validação aqui para garantir que o URL está acessível.
    return {'mime_type': 'image/jpeg', 'file_uri': str(image_url)}      # Gemini pode inferir o mime_type

# --- Endpoint da API ---
@app.post("/testa-prompt", tags=["teste"])
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
        
        # Lança um erro HTTP 500 (Internal Server Error)
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar o prompt: {e}")

@app.post("/analisa-imagem", tags=["gemini"])
async def analisar_prompt(request: MultimodalPromptRequest):    
    if not model:
        raise HTTPException(status_code=500, detail="Modelo de IA não inicializado corretamente.")

    content_parts = []    
    try:
        if request.global_text_prompt:                                  # Adiciona o prompt de texto global, se existir
            content_parts.append(request.global_text_prompt)

        for part in request.parts:
            if isinstance(part, TextPart):
                content_parts.append(part.text)
            elif isinstance(part, ImagePart):
                image_url = str(part.image_url)
                
                response = requests.get(image_url, stream=True)         # Faz o download da imagem a partir do URL
                response.raise_for_status()
                
                img = Image.open(io.BytesIO(response.content))          # Abre a imagem a partir dos dados baixados (bytes) em memória
                
                content_parts.append(img)                               # Adiciona o objeto de imagem à lista de partes

                #content_parts.append(genai.upload_file(path=str(part.image_url), mime_type="image/jpeg")) # Use upload_file para URLs externas
                
        print(f"Enviando para o Gemini com {len(content_parts)} partes.")
        response = model.generate_content(content_parts)
        print("Resposta gerada com sucesso.")
        return {"resposta": response.text}
        
    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar a imagem: {e}")
        raise HTTPException(status_code=400, detail=f"Não foi possível baixar a imagem do URL fornecido: {e}")
    except Exception as e:
        print(f"Erro ao chamar a API do Gemini: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar o prompt: {e}")


        print(f"Recebendo prompt multimodal com {len(content_parts)} partes.")

        # Envia as partes (texto e imagem) para a IA
        response = model.generate_content(content_parts)
        print("Resposta gerada com sucesso.")

        return {"resposta": response.text}
    except Exception as e:
        print(f"Erro ao chamar a API do Gemini: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar o prompt: {e}")

@app.get("/", tags=["Health Check"])
async def root():
    return {"status": "API online"}