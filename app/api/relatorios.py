from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from ..database import get_db
from ..services import relatorio_service
from ..schemas import schemas
from ..models import models

router = APIRouter(
    prefix="/relatorios",
    tags=["Relatórios"]
)

@router.get("/{usuario_id}", response_model=schemas.Relatorio)
async def gerar_ou_buscar_relatorio_para_nutricionista(
    usuario_id: int,
    db: Session = Depends(get_db),
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None
):
    """
    1. Busca ou cria um relatório PENDENTE para o usuario_id.
    2. Por padrão, busca os últimos 14 dias (lógica no serviço).
    3. Aceita 'data_inicio' e 'data_fim' (formato YYYY-MM-DD) como query params.
    4. Retorna o relatório (com o resumo automático).
    """
    try:
        relatorio = relatorio_service.criar_relatorio(
            db=db, 
            usuario_id=usuario_id,
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        return relatorio
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{relatorio_id}/sugestao-ia", response_model=schemas.SugestaoRelatorioResponse)
async def gerar_sugestao_para_nutricionista(
    relatorio_id: int,
    db: Session = Depends(get_db)
):
    """
    Endpoint para o Nutricionista.
    1. Pega o resumo de um relatório PENDENTE.
    2. Envia para a LLM gerar um comentário de sugestão.
    3. Retorna o texto da sugestão para o nutricionista editar.
    """
    try:
        sugestao = relatorio_service.gerar_sugestao_llm(db=db, relatorio_id=relatorio_id)
        return sugestao
    except HTTPException as e:
        raise e # Repassa erros 404, 400, etc.
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.put("/{relatorio_id}/aprovar", response_model=schemas.Relatorio)
async def aprovar_relatorio(
    relatorio_id: int,
    update_data: schemas.RelatorioUpdate, # <-- Recebe o body com os comentários
    nutricionista_id: int, # <-- Recebe o ID do nutricionista (ex: via query param)
    db: Session = Depends(get_db)
):
    """
    Endpoint para o Nutricionista.
    1. Recebe os comentários do nutricionista.
    2. Atualiza o 'Relatorio' no banco e muda o status para 'APROVADO'.
    3. Retorna o relatório atualizado.
    """
    try:
        relatorio_aprovado = relatorio_service.aprovar_relatorio(
            db=db, 
            relatorio_id=relatorio_id, 
            update_data=update_data, 
            nutricionista_id=nutricionista_id
        )
        return relatorio_aprovado
    except HTTPException as e:
        raise e # Repassa exceções HTTP (como 404)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/aprovados/{usuario_id}", response_model=List[schemas.Relatorio])
async def buscar_relatorios_aprovados(
    usuario_id: int,
    db: Session = Depends(get_db)
):
    """
    Endpoint para o Usuário Comum.
    1. Busca no banco todos os relatórios do usuario_id com status 'APROVADO'.
    2. Retorna a lista de relatórios (com os comentários do nutricionista).
    """
    try:
        relatorios = relatorio_service.get_relatorios_aprovados_usuario(
            db=db, 
            usuario_id=usuario_id
        )
        return relatorios
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))