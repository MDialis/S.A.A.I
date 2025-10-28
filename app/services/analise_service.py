import os
import json
import uuid
import google.generativeai as genai

from fastapi import HTTPException
from sqlalchemy.orm import Session
from PIL import Image
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

def analisar_imagem_e_salvar(db: Session, usuario_id: int, imagem_pil: Image.Image):
    """
    Serviço principal:
    1. Salva a imagem no disco.
    2. Envia para a LLM.
    3. Salva o resultado completo no banco de dados.
    """
    
    if not model:
        raise HTTPException(status_code=500, detail="Modelo de IA não inicializado.")
    
    try:
        # Normaliza extensões de arquivo
        file_extension = imagem_pil.format.lower()
        if file_extension == 'jpeg':
            file_extension = 'jpg'

        unique_filename = f"{uuid.uuid4()}.{file_extension}"        # Gera um nome de arquivo único para evitar sobreposição
        
        filepath = os.path.join("uploads", unique_filename)         # Define o caminho de salvamento no sistema de arquivos
        
        imagem_pil.save(filepath)                                   # Salva a imagem no disco
        
        image_url_path = f"uploads/{unique_filename}"               # Define o caminho da URL que será salvo no banco
        
        # Envia Imagem para a LLM
        response = model.generate_content([prompt_padrao_imagem, imagem_pil])
        
        # "Limpa" a Resposta JSON
        cleaned_text = response.text.strip().strip('```json').strip('```').strip()
        
        data = json.loads(cleaned_text)                             # 'data' é o nosso objeto JSON (dicionário Python)
        
        # Cria a "Refeição" principal
        nova_refeicao = db_models.Refeicao(
            usuario_comum_id=usuario_id,
            llm_raw_response=data,                                  # Salva o JSON bruto da IA
            imagem_url=image_url_path                               # Salva o caminho para a imagem
        )
        db.add(nova_refeicao)
        db.flush()                                                  # Necessário para que 'nova_refeicao' obtenha um ID
        
        # Cria os "Itens da Refeição" (os alimentos)
        for item in data.get("food", []):
            novo_item = db_models.RefeicaoItem(
                refeicao_id=nova_refeicao.id,                       # Vincula ao ID da refeição
                nome_alimento=item.get("name"),
                quantidade=item.get("amount", 0),
                calorias=item.get("calories", 0),                   # Mesmo que o prompt não peça,
                proteinas=item.get("proteins", 0),
                carboidratos=item.get("carbohydrates", 0),
                gordura=item.get("fats", 0)                         # O JSON tem 'fats', o DB tem 'gordura'
            )
            db.add(novo_item)
        
        # Confirma todas as mudanças no banco de dados
        db.commit()
        db.refresh(nova_refeicao) # Atualiza o objeto com os dados do DB
        
        print(f"✅ Refeição ID {nova_refeicao.id} salva. Imagem em: {image_url_path}")
        return nova_refeicao
        
    except json.JSONDecodeError:
        db.rollback() # Desfaz qualquer mudança no banco se o JSON falhar
        raise HTTPException(status_code=500, detail="A resposta da IA não era um JSON válido.")
    except Exception as e:
        db.rollback() # Desfaz qualquer mudança se qualquer outro erro ocorrer
        print(f"❌ Erro no serviço de análise: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar a análise: {str(e)}")