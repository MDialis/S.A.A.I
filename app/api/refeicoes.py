import io
import requests

from PIL import Image, UnidentifiedImageError
# from typing import List
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..services import analise_service
from ..schemas.schemas import ImageUrlAnalysisRequest
# from ..schemas.schemas import PromptRequest, ImageAnalysisRequest

router = APIRouter( 
    prefix="/refeicoes",
    tags=["Refeições"]
)

# --- Endpoint da API ---
@router.post("/analisar-imagem/{usuario_id}", status_code=201)
async def analisar_refeicao_upload(
    usuario_id: int,
    db: Session = Depends(get_db),
    file: UploadFile = File(...)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="O arquivo enviado não é uma imagem.")

    try:
        contents = await file.read()
        imagem_pil = Image.open(io.BytesIO(contents))

        refeicao_salva = analise_service.analisar_imagem_e_salvar(
            db=db, 
            usuario_id=usuario_id, 
            imagem_pil=imagem_pil
        )

        return refeicao_salva                                       # Salva e retorna a refeição analisada

    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Formato de imagem inválido.")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        print(f"🚨 Erro inesperado no endpoint de análise: {e}")
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro inesperado: {str(e)}")
    
@router.post("/analisar-url/{usuario_id}", status_code=201)
async def analisar_refeicao_por_url(
    usuario_id: int,
    request: ImageUrlAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Recebe um LINK (URL) de uma imagem, baixa, analisa com a LLM e salva no banco.
    """
    try:
        # --- Lógica para baixar a imagem do link ---
        response = requests.get(request.image_url)
        response.raise_for_status() # Lança um erro se a URL for inválida (ex: 404)
        
        imagem_pil = Image.open(io.BytesIO(response.content))
        # ---------------------------------------------

        refeicao_salva = analise_service.analisar_imagem_e_salvar(
            db=db, 
            usuario_id=usuario_id, 
            imagem_pil=imagem_pil
        )
        return refeicao_salva

    except requests.exceptions.RequestException:
        raise HTTPException(status_code=400, detail="Não foi possível baixar a imagem do link fornecido.")
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="O link não continha um formato de imagem válido.")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        print(f"🚨 Erro inesperado no endpoint de URL: {e}")
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro inesperado: {str(e)}")
    
"""
@router.post("/prompt-text", tags=["text"])                        # Endpoint para enviar um prompt de texto simples para o Gemini
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

@router.post("/prompt-img-link", tags=["image"])                   # Endpoint para analisar uma ou mais imagens a partir de URLs fornecidas.
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

@router.post("/prompt-img-file", tags=["image"])                   # Endpoint para analisar uma ou mais imagens enviadas como arquivos (upload).
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
"""        
