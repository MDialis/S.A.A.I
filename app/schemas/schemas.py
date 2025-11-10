from pydantic import BaseModel, HttpUrl, ConfigDict
from typing import List, Optional
from datetime import datetime, date
import enum

# --- Enums (para validação de dados) ---
# É uma boa prática redefinir os Enums aqui para 
# que seus schemas não precisem importar dos models.
class StatusRelatorioEnum(str, enum.Enum):
    PENDENTE = "PENDENTE"
    REVISADO = "REVISADO"
    APROVADO = "APROVADO"

# --- Schemas de Input (O que você já tinha) ---

class ImageUrlAnalysisRequest(BaseModel):
    image_url: HttpUrl # Garante que é um URL válido

# Você pode manter ou remover estes se não for mais usá-los
class PromptRequest(BaseModel):
    prompt: str

class ImageAnalysisRequest(BaseModel):
    image_urls: List[HttpUrl]

# --- Schemas de Output (Novos) ---
# Estes são para ENVIAR dados do banco para o frontend (ex: em um GET)

class RefeicaoItem(BaseModel):
    # Dita como um item de refeição (alimento) deve ser enviado
    nome_alimento: str
    quantidade: float
    calorias: float
    proteinas: float
    carboidratos: float
    gordura: float

    model_config = ConfigDict(from_attributes=True)

class Refeicao(BaseModel):
    # Dita como uma refeição completa deve ser enviada
    id: int
    data_hora: datetime
    imagem_url: Optional[str] = None
    llm_raw_response: Optional[dict] = None # O JSON bruto da IA
    itens: List[RefeicaoItem] = [] # Uma lista de alimentos

    model_config = ConfigDict(from_attributes=True)
    
class SugestaoRelatorioResponse(BaseModel):
    # O texto de sugestão gerado pela IA
    sugestao_texto: str

class Relatorio(BaseModel):
    # Dita como um objeto de relatório deve ser enviado
    id: int
    usuario_comum_id: int
    nutricionista_id: Optional[int] = None
    periodo_inicio: date
    periodo_fim: date
    resumo_automatico: Optional[str] = None
    comentarios_nutricionista: Optional[str] = None
    status: StatusRelatorioEnum
    data_criacao: datetime
    data_aprovacao: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- Schemas de Input (Novos) ---
# Estes são para RECEBER dados do frontend (ex: em um PUT ou POST)

class RelatorioUpdate(BaseModel):
    # O que o nutricionista envia ao aprovar/editar um relatório
    # Esta é a resposta para sua Função #2
    comentarios_nutricionista: str