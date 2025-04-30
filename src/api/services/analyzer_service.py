"""
Serviço de análise de tokens para a API REST.
"""

import re
from typing import Dict, List, Any, Optional
from src.tools.token_analyzer import TokenAnalyzer
from src.tools.token_counter import count_tokens
from src.utils.logging_config import setup_logger

# Configurar logger
logger = setup_logger(__name__)


async def analyze_token_usage(content: str, model_name: str = "gpt-3.5-turbo") -> Dict[str, Any]:
    """
    Analisa o uso de tokens em um texto.
    
    Args:
        content: Texto a ser analisado
        model_name: Nome do modelo para contagem de tokens
        
    Returns:
        dict: Resultado da análise de tokens
    """
    try:
        # Inicializar analisador
        analyzer = TokenAnalyzer(model_name)
        
        # Contar tokens totais
        total_tokens = count_tokens(content, model_name)
        
        # Inicializar resultado
        result = {
            "total_tokens": total_tokens,
            "model_name": model_name
        }
        
        # Para conteúdo no formato LLMs.txt, fazer análise por seção
        if content.startswith("# "):
            # Extrair seções
            sections = re.split(r'(^# .+)', content, flags=re.MULTILINE)
            section_map = {}
            current = None
            for part in sections:
                if part.strip().startswith('# '):
                    current = part.strip()
                    section_map[current] = ''
                elif current:
                    section_map[current] += part
            
            if section_map:
                # Contar tokens por seção
                section_tokens = {sec: count_tokens(txt, model_name) for sec, txt in section_map.items()}
                result["sections"] = section_tokens
                
                # Analisar distribuição e fazer recomendações
                analysis = analyzer.analyze_sections(section_tokens)
                
                # Detectar tipo de conteúdo
                content_sample = analyzer._extract_content_sample(content, section_map)
                content_type = analyzer._detect_content_type(content_sample, section_map)
                
                if content_type:
                    analysis["content_type"] = content_type
                    chunking = analyzer.chunking_by_content.get(content_type)
                    if chunking:
                        analysis["chunking_recommendation"] = chunking
                
                # Adicionar ao resultado
                result.update(analysis)
        
        return result
    
    except Exception as e:
        logger.error(f"Erro na análise de tokens: {str(e)}")
        # Retornar contagem básica em caso de erro
        return {
            "total_tokens": count_tokens(content, model_name),
            "model_name": model_name,
            "error": str(e)
        }
