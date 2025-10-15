import os
import json
import google.generativeai as genai
from fastapi import HTTPException
from sqlalchemy.orm import Session
from ..models import models as db_models

# --- Inicialização do Modelo Generativo (Gemini) ---
try:
    api_key = os.getenv("GEMINI_API_KEY")                           # Busca a chave da API a partir das variáveis de ambiente
    if not api_key:
        raise ValueError("Chave da API do Google não encontrada no .env")
    
    genai.configure(api_key=api_key)                                # Configura a biblioteca do Google AI com a chave fornecida
    model = genai.GenerativeModel('gemini-2.5-flash-lite')          # Instancia o modelo generativo que será utilizado nas requisições

except Exception as e:                                              # Em caso de falha na inicialização, a API não funcionará corretamente.
    print(f"ERRO CRÍTICO ao inicializar o modelo Gemini: {e}")      # Loga um erro crítico e define o modelo como None.
    model = None

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

def process_and_save_gemini_response(response_text: str):           # Processa a resposta, converte para JSON e salva em um arquivo.
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