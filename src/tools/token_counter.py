import tiktoken
from src.utils.logging_config import setup_logger

# Configurar logger para este módulo
logger = setup_logger(__name__)

def count_tokens(text, model_name: str = "gpt-3.5-turbo") -> int:
    """
    Retorna o número de tokens para o texto dado usando tiktoken.

    Args:
        text: Texto a ser analisado
        model_name: Nome do modelo para usar encoding correto

    Returns:
        int: Número de tokens

    Raises:
        ValueError: Se o modelo não for reconhecido e nenhum fallback funcionar
    """
    try:
        logger.debug(f"Contando tokens para modelo: {model_name}")
        encoding = tiktoken.encoding_for_model(model_name)
    except KeyError:
        # Modelo não reconhecido, tentar fallbacks
        logger.warning(f"Modelo {model_name} não reconhecido, usando fallback cl100k_base")
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.error(f"Falha ao obter encoding: {str(e)}")
            raise ValueError(f"Não foi possível obter encoding para {model_name}")

    if not text:
        logger.debug("Texto vazio, retornando 0 tokens")
        return 0

    # Converter para string se não for string
    if not isinstance(text, str):
        try:
            text = str(text)
            logger.debug(f"Convertido entrada não-string para string: {text}")
        except Exception as e:
            logger.error(f"Erro ao converter para string: {str(e)}")
            return 0

    try:
        tokens = encoding.encode(text)
        token_count = len(tokens)
        logger.debug(f"Contagem concluída: {token_count} tokens")
        return token_count
    except Exception as e:
        logger.error(f"Erro ao codificar texto: {str(e)}")
        # Em caso de erro, tentar fazer contagem aproximada
        logger.warning("Usando estimativa aproximada de tokens (4 caracteres = 1 token)")
        try:
            return len(text) // 4  # Aproximação grosseira
        except Exception:
            logger.error("Falha na estimativa aproximada de tokens")
            return 1  # Retornar valor mínimo