# --- Importações de Bibliotecas ---
import os
import io
import json
import requests
import google.generativeai as genai
from PIL import Image, UnidentifiedImageError
from typing import List, Optional, Union
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel, HttpUrl
from datetime import datetime

# --- Configuração Inicial ---

load_dotenv()                                                   # Carrega as variáveis de ambiente do arquivo .env (ex: GEMINI_API_KEY)
app = FastAPI(                                                  # Inicializa a aplicação FastAPI com metadados para a documentação
    title="Serviço de Análise com Gemini",
    description="Uma API para intermediar requisições para a API do Google Gemini."
)

DATA_DIR = "analises_json"                                      # Define o diretório onde os resultados das análises (JSONs) serão salvos.
os.makedirs(DATA_DIR, exist_ok=True)                            # O diretório é criado se ainda não existir.

# --- Inicialização do Modelo Generativo (Gemini) ---
try:
    api_key = os.getenv("GEMINI_API_KEY")                       # Busca a chave da API a partir das variáveis de ambiente
    if not api_key:
        raise ValueError("Chave da API do Google não encontrada no .env")
    
    genai.configure(api_key=api_key)                            # Configura a biblioteca do Google AI com a chave fornecida
    model = genai.GenerativeModel('gemini-2.5-flash-lite')      # Instancia o modelo generativo que será utilizado nas requisições

except Exception as e:                                          # Em caso de falha na inicialização, a API não funcionará corretamente.
    print(f"ERRO CRÍTICO ao inicializar o modelo Gemini: {e}")  # Loga um erro crítico e define o modelo como None.
    model = None

# --- Modelos de Dados ---

# Define um prompt padrão e detalhado para guiar a IA a retornar um JSON estruturado.
prompt_padrao_imagem = """
Parse the image and return ONLY a JSON object as a response.
The JSON must contain a main list named 'food'.
Each item in the 'food' list must have the following attributes:
- 'name': Food name in pt-br (if it has a portuguese name).
- 'amount': Food amount in g.
- 'carbohydrates': Carbohydrates amount in g.
- 'proteins': Proteins amount in g.
- 'fats': Fat (lipids) amount in g.

If a macronutrient is not applicable or cannot be estimated, return a value of 0.
If the image contains no food, return an empty 'food' list.
"""

# Modelo para o endpoint de texto simples
class PromptRequest(BaseModel):
    prompt: str

# Modelo para endpoint de URLs de imagens
class ImageAnalysisRequest(BaseModel):
    image_urls: List[HttpUrl]                                   # Garante que a lista contém apenas URLs válidas
    
def process_and_save_gemini_response(response_text: str):       # Processa a resposta, converte para JSON e salva em um arquivo.
    # Args: response_text (str): A string de resposta bruta recebida do modelo Gemini.
    # Returns: dict: O dicionário Python representando o JSON processado, ou um dicionário de erro.
    try:
        # Limpa a resposta, removendo marcações como (```json ... ```)
        cleaned_text = response_text.strip().strip('```json').strip('```').strip()

        # Converte a string de texto limpa para um objeto Python (dicionário)
        data = json.loads(cleaned_text)                        
        
        # Gera um nome de arquivo com base na data e hora atual
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_analise.json"
        filepath = os.path.join(DATA_DIR, filename)
        
        # Salva o objeto Python no arquivo JSON, com formatação legível (indent=4)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        # Retorna os dados já parseados
        print(f"✅ Análise salva com sucesso em: {filepath}")
        return data
        
    except json.JSONDecodeError:
        print(f"⚠️ Erro: A resposta da IA não era um JSON válido. Resposta recebida: {response_text}")
        return {"error": "A resposta da IA não era um JSON válido.", "raw_response": response_text}
    except Exception as e:
        print(f"❌ Erro ao salvar o arquivo: {e}")
        return {"error": f"Erro ao salvar o arquivo: {e}", "raw_response": response_text}

# --- Endpoint da API ---
@app.post("/prompt-text", tags=["text"])                        # Endpoint para enviar um prompt de texto simples para o Gemini
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

@app.post("/prompt-img-link", tags=["image"])                   # Endpoint para analisar uma ou mais imagens a partir de URLs fornecidas.
async def analisar_prompt(request: ImageAnalysisRequest):
    if not model:
        raise HTTPException(status_code=500, detail="Modelo de IA não inicializado corretamente.")

    content_parts = [prompt_padrao_imagem]                      # Conteúdo para a API do Gemini.
    
    try:
        for image_url in request.image_urls:                    # Itera sobre as URLs das imagens recebidas
           
            # Faz o download da imagem a partir do URL
            response = requests.get(str(image_url), stream=True)
            response.raise_for_status()                         # Lança um erro se o download falhar (ex: 404)
            
            # Abre a imagem a partir dos dados em memória
            img = Image.open(io.BytesIO(response.content))
            
            # Adiciona o objeto de imagem à lista de partes
            content_parts.append(img)
            
        print(f"Enviando para o Gemini com {len(content_parts)} partes (1 texto + {len(request.image_urls)} imagens).")

        # Envia o conteúdo (prompt + imagens) para o modelo Gemini
        response = model.generate_content(content_parts)
        print("Resposta gerada com sucesso.")

        # Processa e salva a resposta JSON
        processed_data = process_and_save_gemini_response(response.text)
        return processed_data
        
    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar a imagem: {e}")
        raise HTTPException(status_code=400, detail=f"Não foi possível baixar a imagem do URL fornecido: {e}")
    except Exception as e:
        print(f"Erro ao chamar a API do Gemini: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar o prompt: {e}")

@app.post("/prompt-img-file", tags=["image"])                   # Endpoint para analisar uma ou mais imagens enviadas como arquivos (upload).
async def analisar_prompt_imagem_arquivo(files: List[UploadFile] = File(...)):
    if not model:
        raise HTTPException(status_code=500, detail="Modelo de IA não inicializado corretamente.")

    content_parts = [prompt_padrao_imagem]                      # Conteúdo para a API do Gemini.

    if not files:
        raise HTTPException(status_code=400, detail="Nenhum arquivo foi enviado.")

    try:
        for file in files:                                      # Itera sobre cada arquivo enviado na requisição
            contents = await file.read()                        # Lê o conteúdo do arquivo em bytes
            
            try:                                                # Tenta abrir os bytes como uma imagem para validar o formato
                img = Image.open(io.BytesIO(contents))
                content_parts.append(img)
            except UnidentifiedImageError:                      # Se a PIL não conseguir identificar a imagem, retorna um erro claro.
                raise HTTPException(
                    status_code=400, 
                    detail=f"O arquivo '{file.filename}' não é um formato de imagem válido."
                )

        print(f"Enviando para o Gemini com {len(content_parts)} partes (1 texto + {len(files)} imagens).")
        
        # Envia o conteúdo (prompt + imagens) para o modelo Gemini
        response = model.generate_content(content_parts)
        print("Resposta gerada com sucesso.")

        # Processa, salva e retorna a resposta JSON
        processed_data = process_and_save_gemini_response(response.text)
        return processed_data

    except Exception as e:
        print(f"Erro ao processar a imagem ou chamar a API do Gemini: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar o prompt: {e}")

@app.get("/", tags=["Health Check"])                            # Endpoint de verificação de saúde (health check) para confirmar que a API está online.
async def root():
    return {"status": "API online"}