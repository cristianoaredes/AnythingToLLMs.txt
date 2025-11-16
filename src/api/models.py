"""
Modelos Pydantic para a API REST do Anything to LLMs.txt.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator


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
    chunk_size: Optional[int] = Field(default=None, description="Tamanho do chunk para processamento", ge=100, le=100000)
    chunk_overlap: Optional[int] = Field(default=None, description="Sobreposição entre chunks", ge=0, le=1000)
    model_name: str = Field(default="gpt-3.5-turbo", description="Modelo LLM para análise de tokens", min_length=1, max_length=100)
    to_langchain: bool = Field(default=False, description="Exportar para formato LangChain (não implementado ainda)")

    @field_validator('ocr_language')
    @classmethod
    def validate_ocr_language(cls, v):
        """Valida que o código de idioma OCR tem formato válido."""
        if v is not None:
            # Códigos de idioma geralmente têm 3-7 caracteres (por, eng, chi_sim)
            if not (3 <= len(v) <= 7):
                raise ValueError("Código de idioma OCR inválido (deve ter 3-7 caracteres)")
            # Apenas letras minúsculas e underscore
            if not all(c.islower() or c == '_' for c in v):
                raise ValueError("Código de idioma deve conter apenas letras minúsculas e underscore")
        return v

    @field_validator('output_formats')
    @classmethod
    def validate_output_formats(cls, v):
        """Valida que pelo menos um formato de saída foi especificado."""
        if not v or len(v) == 0:
            raise ValueError("Pelo menos um formato de saída deve ser especificado")
        return v

    @model_validator(mode='after')
    def validate_chunk_overlap(self):
        """Valida que chunk_overlap não é maior que chunk_size."""
        if self.chunk_size is not None and self.chunk_overlap is not None:
            if self.chunk_overlap >= self.chunk_size:
                raise ValueError("chunk_overlap deve ser menor que chunk_size")
        return self


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
    content: str = Field(..., description="Conteúdo a ser analisado", min_length=1, max_length=10_000_000)
    model_name: str = Field(default="gpt-3.5-turbo", description="Modelo LLM para análise de tokens", min_length=1, max_length=100)

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        """Valida que o conteúdo não é apenas espaços em branco."""
        if not v.strip():
            raise ValueError("Conteúdo não pode ser vazio ou apenas espaços em branco")
        return v


class TokenAnalysisResponse(BaseModel):
    total_tokens: int = Field(..., description="Total de tokens")
    sections: Optional[Dict[str, int]] = Field(default=None, description="Tokens por seção")
    recommendations: Optional[List[str]] = Field(default=None, description="Recomendações")
    content_type: Optional[str] = Field(default=None, description="Tipo de conteúdo detectado")
    chunking_recommendation: Optional[Dict[str, Any]] = Field(default=None, description="Recomendação de chunking")
