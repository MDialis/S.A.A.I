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