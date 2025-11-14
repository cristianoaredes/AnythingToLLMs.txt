"""
Configuração de logging centralizada para o projeto.

Suporta dois formatos:
- text: Log legível para humanos (desenvolvimento)
- json: Log estruturado para parsing automatizado (produção)
"""
import os
import json
import logging
from datetime import datetime

DEFAULT_LOG_LEVEL = logging.INFO


class JSONFormatter(logging.Formatter):
    """Formatter que converte logs em JSON estruturado."""

    def format(self, record):
        """Converte LogRecord em JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Adicionar informações de exceção se houver
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Adicionar campos extras se houver
        if hasattr(record, "extra"):
            log_data["extra"] = record.extra

        return json.dumps(log_data, ensure_ascii=False)


def setup_logger(name=None, log_level=None):
    """
    Configura e retorna um logger com formatação padronizada.

    Suporta dois formatos via env var LOG_FORMAT:
    - "text": Log tradicional legível (padrão)
    - "json": Log estruturado JSON para produção

    Args:
        name (str): Nome do logger (geralmente o nome do módulo)
        log_level (int): Nível de logging (DEBUG, INFO, etc)

    Returns:
        logging.Logger: Logger configurado
    """
    # Nome do logger (módulo chamador se não especificado)
    if name is None:
        name = "anything-to-llms-txt"

    # Criar logger
    logger = logging.getLogger(name)

    # Definir nível conforme parâmetro ou variável de ambiente ou padrão
    level = log_level
    if level is None:
        env_level = os.environ.get('LLMS_LOG_LEVEL', '').upper()
        if env_level in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'):
            level = getattr(logging, env_level)
        else:
            level = DEFAULT_LOG_LEVEL

    logger.setLevel(level)

    # Evitar duplicação de handlers se o logger já foi configurado
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        # Escolher formato baseado em variável de ambiente
        log_format = os.environ.get('LOG_FORMAT', 'text').lower()

        if log_format == 'json':
            # Formato JSON estruturado (produção)
            formatter = JSONFormatter()
        else:
            # Formato texto legível (desenvolvimento)
            formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)s - %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

        console_handler.setFormatter(formatter)

        # Adicionar handler ao logger
        logger.addHandler(console_handler)

        # Se estiver em DEBUG, adicionar também um file handler
        if level == logging.DEBUG:
            # Garantir que o diretório de logs existe
            os.makedirs('logs', exist_ok=True)

            # Nome do arquivo baseado na data
            log_file = f'logs/llms-txt_{datetime.now().strftime("%Y%m%d")}.log'

            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger
