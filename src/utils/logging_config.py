"""
Configuração de logging centralizada para o projeto.
"""
import os
import logging
from datetime import datetime

DEFAULT_LOG_LEVEL = logging.INFO

def setup_logger(name=None, log_level=None):
    """
    Configura e retorna um logger com formatação padronizada.
    
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
        
        # Formato: [TIMESTAMP] LEVEL - MODULE: MESSAGE
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