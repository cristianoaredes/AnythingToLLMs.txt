"""
Configurações centralizadas para Anything to LLMs.txt.

Este arquivo contém todas as constantes e configurações do projeto.
Valores podem ser sobrescritos via variáveis de ambiente.
"""

import os

# ========================================
# Configurações da API
# ========================================

# CORS - Origens permitidas (separadas por vírgula)
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080")

# API Key para autenticação
API_KEY = os.getenv("LLMS_API_KEY", "")

# Rate Limiting (requisições por minuto)
RATE_LIMIT = int(os.getenv("LLMS_RATE_LIMIT", "60"))

# Ambiente (development ou production)
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# ========================================
# Configurações do Redis
# ========================================

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# TTL para jobs (em segundos)
JOB_TTL_PROCESSING = int(os.getenv("JOB_TTL_PROCESSING", "3600"))  # 1 hora
JOB_TTL_COMPLETED = int(os.getenv("JOB_TTL_COMPLETED", "86400"))   # 24 horas
JOB_TTL_FAILED = int(os.getenv("JOB_TTL_FAILED", "86400"))         # 24 horas

# ========================================
# Configurações de Upload
# ========================================

# Tamanho máximo de arquivo (em bytes)
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(50 * 1024 * 1024)))  # 50MB

# Formatos suportados
SUPPORTED_FORMATS = [
    'pdf', 'docx', 'html', 'txt', 'md', 'xml',
    'epub', 'json', 'jpg', 'jpeg', 'png', 'tiff', 'tif'
]

# Diretório temporário para uploads
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "temp/uploads")

# ========================================
# Configurações do Formatador
# ========================================

# Comprimento mínimo de parágrafo para ser considerado significativo
MIN_PARAGRAPH_LENGTH = int(os.getenv("MIN_PARAGRAPH_LENGTH", "40"))

# Número máximo de parágrafos para resumo
MAX_SUMMARY_PARAGRAPHS = int(os.getenv("MAX_SUMMARY_PARAGRAPHS", "2"))

# Comprimento máximo do resumo (em caracteres)
MAX_SUMMARY_LENGTH = int(os.getenv("MAX_SUMMARY_LENGTH", "1000"))

# ========================================
# Configurações de OCR
# ========================================

# Engine OCR padrão
DEFAULT_OCR_ENGINE = os.getenv("DEFAULT_OCR_ENGINE", "tesseract")

# Engine OCR de fallback
FALLBACK_OCR_ENGINE = os.getenv("FALLBACK_OCR_ENGINE", "easyocr")

# Idioma padrão para OCR
DEFAULT_OCR_LANGUAGE = os.getenv("DEFAULT_OCR_LANGUAGE", "por")

# ========================================
# Configurações de Classificação de Imagens
# ========================================

# Modelo padrão para classificação de imagens
DEFAULT_IMAGE_CLASSIFIER = os.getenv("DEFAULT_IMAGE_CLASSIFIER", "google/vit-base-patch16-224")

# Limite de confiança mínima para classificação
MIN_CLASSIFICATION_CONFIDENCE = float(os.getenv("MIN_CLASSIFICATION_CONFIDENCE", "0.5"))

# Tamanho de redimensionamento de imagem para classificação
IMAGE_RESIZE_SIZE = int(os.getenv("IMAGE_RESIZE_SIZE", "224"))

# ========================================
# Configurações de Logging
# ========================================

# Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = os.getenv("LLMS_LOG_LEVEL", "INFO")

# Formato de log (text ou json)
LOG_FORMAT = os.getenv("LOG_FORMAT", "text")

# ========================================
# Configurações de Servidor
# ========================================

# Host do servidor
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")

# Porta do servidor
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

# ========================================
# Validações
# ========================================

def validate_config():
    """Valida as configurações ao iniciar."""
    issues = []

    if not API_KEY and ENVIRONMENT == "production":
        issues.append("⚠️  LLMS_API_KEY não configurada em produção!")

    if CORS_ORIGINS == "*":
        issues.append("⚠️  CORS configurado para aceitar todas origens!")

    if MAX_FILE_SIZE > 100 * 1024 * 1024:  # 100MB
        issues.append(f"⚠️  Tamanho máximo de arquivo muito alto: {MAX_FILE_SIZE / 1024 / 1024}MB")

    return issues


if __name__ == "__main__":
    # Teste de configuração
    print("=== Configuração Atual ===\n")
    print(f"Ambiente: {ENVIRONMENT}")
    print(f"CORS Origins: {CORS_ORIGINS}")
    print(f"Redis URL: {REDIS_URL}")
    print(f"Max File Size: {MAX_FILE_SIZE / 1024 / 1024}MB")
    print(f"Supported Formats: {', '.join(SUPPORTED_FORMATS)}")
    print(f"Min Paragraph Length: {MIN_PARAGRAPH_LENGTH}")
    print(f"Max Summary Length: {MAX_SUMMARY_LENGTH}")
    print(f"Log Level: {LOG_LEVEL}")

    print("\n=== Validação ===\n")
    issues = validate_config()
    if issues:
        for issue in issues:
            print(issue)
    else:
        print("✅ Todas as configurações estão OK!")
