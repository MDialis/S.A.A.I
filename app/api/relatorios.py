# app/api/relatorios.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db

router = APIRouter(
    prefix="/relatorios",
    tags=["Relatórios"]
)

@router.get("/{usuario_id}", status_code=200)
async def gerar_ou_buscar_relatorio_para_nutricionista(
    usuario_id: int,
    db: Session = Depends(get_db)
):
    """
    (LÓGICA A IMPLEMENTAR)
    Endpoint para o Nutricionista.
    1. Busca todas as refeições do usuario_id em um período (ex: última semana).
    2. Gera um resumo (pode ser uma simples lista de refeições por enquanto).
    3. Salva/Atualiza um registro na tabela 'Relatorio'.
    4. Retorna o relatório para o nutricionista.
    """
    print(f"Nutricionista está solicitando relatório para o usuário {usuario_id}")
    # (Lógica simplificada por enquanto)
    return {"message": f"Relatório para usuário {usuario_id} está sendo gerado", "status": "PENDENTE"}


@router.put("/{relatorio_id}/aprovar", status_code=200)
async def aprovar_relatorio(
    relatorio_id: int,
    db: Session = Depends(get_db)
    # (body com 'comentarios_nutricionista')
):
    """
    (LÓGICA A IMPLEMENTAR)
    Endpoint para o Nutricionista.
    1. Recebe os comentários/edições do nutricionista.
    2. Atualiza o 'Relatorio' no banco de dados.
    3. Muda o status para 'APROVADO'.
    """
    print(f"Nutricionista está aprovando o relatório {relatorio_id}")
    return {"message": f"Relatório {relatorio_id} aprovado com sucesso"}


@router.get("/aprovados/{usuario_id}", status_code=200)
async def buscar_relatorios_aprovados(
    usuario_id: int,
    db: Session = Depends(get_db)
):
    """
    (LÓGICA A IMPLEMENTAR)
    Endpoint para o Usuário Comum.
    1. Busca no banco todos os relatórios do usuario_id com status 'APROVADO'.
    2. Retorna a lista de relatórios (com os comentários do nutricionista).
    """
    print(f"Usuário {usuario_id} está buscando seus relatórios aprovados.")
    return {"message": "Buscando relatórios...", "relatorios_aprovados": []}