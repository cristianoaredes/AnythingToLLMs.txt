"""
Modelos Pydantic para a API REST do Anything to LLMs.txt.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class OcrEngine(str, Enum):
    AUTO = "auto"
    TESSERACT = "tesseract"
    TESSERACT_CLI = "tesseract_cli"
    EASYOCR = "easyocr"
    RAPIDOCR = "rapidocr"
    MAC = "mac"


class ProfileType(str, Enum):
    MIN = "llms-min"
    CTX = "llms-ctx"
    TABLES = "llms-tables"
    IMAGES = "llms-images"
    RAW = "llms-raw"
    FULL = "llms-full"


class OutputFormat(str, Enum):
    LLMS = "llms"
    MARKDOWN = "md"
    JSON = "json"
    HTML = "html"


class ConversionRequest(BaseModel):
    ocr_engine: OcrEngine = Field(default=OcrEngine.AUTO, description="Motor OCR a ser utilizado")
    ocr_language: Optional[str] = Field(default=None, description="Idioma para OCR (ex: por, eng, chi_sim)")
    force_ocr: bool = Field(default=False, description="Força OCR mesmo em documentos com texto")
    profile: ProfileType = Field(default=ProfileType.FULL, description="Perfil de formatação")
    output_formats: List[OutputFormat] = Field(default=[OutputFormat.LLMS], description="Formatos de saída")
    chunk_size: Optional[int] = Field(default=None, description="Tamanho do chunk para processamento")
    chunk_overlap: Optional[int] = Field(default=None, description="Sobreposição entre chunks")
    model_name: str = Field(default="gpt-3.5-turbo", description="Modelo LLM para análise de tokens")
    to_langchain: bool = Field(default=False, description="Exportar para formato LangChain (não implementado ainda)")


class ConversionResponse(BaseModel):
    job_id: str = Field(..., description="ID único do job de processamento")
    status: str = Field(default="processing", description="Status do processamento")


class ConversionResult(BaseModel):
    formats: Dict[str, str] = Field(..., description="Conteúdo em diferentes formatos")
    token_count: Optional[int] = Field(default=None, description="Contagem de tokens")
    analysis: Optional[Dict[str, Any]] = Field(default=None, description="Análise de tokens")
    processing_time: float = Field(..., description="Tempo de processamento em segundos")


class StatusResponse(BaseModel):
    job_id: str
    status: str
    progress: Optional[float] = None
    result: Optional[ConversionResult] = None
    error: Optional[str] = None


class TokenAnalysisRequest(BaseModel):
    content: str = Field(..., description="Conteúdo a ser analisado")
    model_name: str = Field(default="gpt-3.5-turbo", description="Modelo LLM para análise de tokens")


class TokenAnalysisResponse(BaseModel):
    total_tokens: int = Field(..., description="Total de tokens")
    sections: Optional[Dict[str, int]] = Field(default=None, description="Tokens por seção")
    recommendations: Optional[List[str]] = Field(default=None, description="Recomendações")
    content_type: Optional[str] = Field(default=None, description="Tipo de conteúdo detectado")
    chunking_recommendation: Optional[Dict[str, Any]] = Field(default=None, description="Recomendação de chunking")
