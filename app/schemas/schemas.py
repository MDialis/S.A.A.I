# app/schemas/schemas.py
from pydantic import BaseModel, HttpUrl
from typing import List

# Modelo para o endpoint de texto simples
class PromptRequest(BaseModel):
    prompt: str

# Modelo para endpoint de URLs de imagens
class ImageAnalysisRequest(BaseModel):
    image_urls: List[HttpUrl]