import os
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
from fastapi import HTTPException, status
from typing import Optional

import google.generativeai as genai
from ..models import models as db_models
from ..schemas import schemas as schemas

try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Chave da API do Google não encontrada no .env")
    
    genai.configure(api_key=api_key)
    # Usamos um modelo focado em texto para esta tarefa
    model_texto = genai.GenerativeModel('gemini-2.5-flash') 

except Exception as e:
    print(f"ERRO CRÍTICO ao inicializar o modelo Gemini (texto): {e}")
    model_texto = None
    
prompt_sugestao_nutricionista = """
Act like an professional nutricionist and based on the info about his diet, write a very short feedback for the user (in português-BR).
The feedback must try to reinforce positive behavior and point out what the pacient should do to achieve a healthier diet.
The feedback should also be on point and professional instead of extense, do not do chit chat
Avoid technical jargon, to try engage the patient.

SUMMARY:
{resumo}

SUGESTED COMMENT:
"""

def processar_periodo(data_inicio, data_fim):
    hoje = date.today()
    
    if data_fim is None:
        data_fim = hoje

    if data_inicio is None:
        data_inicio = data_fim - timedelta(days=14)
        
    if data_inicio > hoje:
        raise ValueError("Data inválida: A data de início não pode ser no futuro.")
    
    if data_inicio > data_fim:
        raise ValueError("Data inválida: A data de início não pode ser após a data final.")
        
    return data_inicio, data_fim

def gerar_sugestao_llm(db: Session, relatorio_id: int) -> schemas.SugestaoRelatorioResponse:
    """
    Gera um comentário de sugestão para o nutricionista usando a LLM.
    """
    if not model_texto:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Modelo de IA de texto não inicializado."
        )

    # 1. Buscar o relatório
    db_relatorio = db.query(db_models.Relatorio).filter(db_models.Relatorio.id == relatorio_id).first()
    
    if not db_relatorio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relatório não encontrado")
        
    if not db_relatorio.resumo_automatico:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Relatório não contém resumo para análise.")

    # 2. Preparar o prompt
    prompt_completo = prompt_sugestao_nutricionista.format(resumo=db_relatorio.resumo_automatico)

    # 3. Chamar a IA
    try:
        response = model_texto.generate_content(prompt_completo)
        sugestao = response.text
        
        # Limpa a resposta (remove markdown, etc.)
        sugestao_limpa = sugestao.strip().strip("```").strip()

        return schemas.SugestaoRelatorioResponse(sugestao_texto=sugestao_limpa)
        
    except Exception as e:
        print(f"Erro ao chamar a API do Gemini: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro da IA: {e}")
    
def criar_relatorio(
    db: Session, 
    usuario_id: int,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None
    ):      

    try:
        periodo_inicio, periodo_fim = processar_periodo(data_inicio, data_fim)
    except HTTPException as e:
        raise e

    relatorio_existente = db.query(db_models.Relatorio).filter(
        db_models.Relatorio.usuario_comum_id == usuario_id,
        db_models.Relatorio.periodo_inicio == periodo_inicio,
        db_models.Relatorio.periodo_fim == periodo_fim,
        db_models.Relatorio.status == db_models.StatusRelatorioEnum.PENDENTE
    ).first()

    if relatorio_existente:
        print(f"Relatório {relatorio_existente.id} já existe, retornando...")
        return relatorio_existente

    refeicoes = db.query(db_models.Refeicao).filter(
        db_models.Refeicao.usuario_comum_id == usuario_id,
        db_models.Refeicao.data_hora >= datetime.combine(periodo_inicio, datetime.min.time()),
        db_models.Refeicao.data_hora <= datetime.combine(periodo_fim, datetime.max.time())
    ).all()
    
    total_calorias = 0
    total_proteinas = 0
    total_carboidratos = 0
    total_gordura = 0
    
    for refeicao in refeicoes:
        for item in refeicao.itens:
            total_calorias += item.calorias or 0
            total_proteinas += item.proteinas or 0
            total_carboidratos += item.carboidratos or 0
            total_gordura += item.gordura or 0

    resumo_automatico = f"""
        Relatório do período: {periodo_inicio.strftime('%d/%m/%Y')} a {periodo_fim.strftime('%d/%m/%Y')}
        Total de refeições registradas: {len(refeicoes)}
        Resumo de Macronutrientes (Total):
        - Calorias Totais: {total_calorias:.2f} kcal
        - Proteínas Totais: {total_proteinas:.2f} g
        - Carboidratos Totais: {total_carboidratos:.2f} g
        - Gorduras Totais: {total_gordura:.2f} g
        (Aqui entrariam os gráficos e tabelas gerados)
        """

    novo_relatorio = db_models.Relatorio(
        usuario_comum_id=usuario_id,
        periodo_inicio=periodo_inicio,
        periodo_fim=periodo_fim,
        resumo_automatico=resumo_automatico,
        status=db_models.StatusRelatorioEnum.PENDENTE
        # nutricionista_id será preenchido quando ele aprovar
    )
    
    db.add(novo_relatorio)
    db.commit()
    db.refresh(novo_relatorio)
    
    print(f"Novo relatório {novo_relatorio.id} criado para usuário {usuario_id}.")
    return novo_relatorio

def aprovar_relatorio(db: Session, relatorio_id: int, update_data: schemas.RelatorioUpdate, nutricionista_id: int):
    """
    Atualiza um relatório com os comentários do nutricionista e o aprova.
    """
    
    db_relatorio = db.query(db_models.Relatorio).filter(db_models.Relatorio.id == relatorio_id).first()
    
    if not db_relatorio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relatório não encontrado")
            
    comentario_final_processado = update_data.comentarios_nutricionista

    db_relatorio.comentarios_nutricionista = comentario_final_processado
    db_relatorio.nutricionista_id = nutricionista_id # Associa o nutricionista
    db_relatorio.status = db_models.StatusRelatorioEnum.APROVADO
    db_relatorio.data_aprovacao = datetime.utcnow()
    
    db.commit()
    db.refresh(db_relatorio)
    
    print(f"Relatório {relatorio_id} aprovado pelo nutricionista {nutricionista_id}.")
    return db_relatorio

def get_relatorios_aprovados_usuario(db: Session, usuario_id: int):
    """
    Busca todos os relatórios APROVADOS de um usuário comum.
    """
    
    relatorios = db.query(db_models.Relatorio).filter(
        db_models.Relatorio.usuario_comum_id == usuario_id,
        db_models.Relatorio.status == db_models.StatusRelatorioEnum.APROVADO
    ).order_by(db_models.Relatorio.data_aprovacao.desc()).all()
    
    return relatorios