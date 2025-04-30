"""
Módulo para analisar contagem de tokens e sugerir estratégias otimizadas.
"""

from src.tools.token_counter import count_tokens
from src.utils.logging_config import setup_logger

# Configurar logger para este módulo
logger = setup_logger(__name__)

class TokenAnalyzer:
    """
    Analisador de contagem de tokens que sugere estratégias para otimização.
    """
    
    def __init__(self, model_name="gpt-3.5-turbo"):
        logger.debug(f"Inicializando TokenAnalyzer para modelo {model_name}")
        self.model_name = model_name
        # Limites aproximados por modelo
        self.model_limits = {
            # Modelos OpenAI (abril/2025)
            "gpt-3.5-turbo": 16385,  # 16K tokens
            "gpt-3.5-turbo-16k": 16385,  # 16K tokens
            "gpt-4": 8192,  # 8K tokens
            "gpt-4-32k": 32768,  # 32K tokens
            "gpt-4o": 128000,  # 128K tokens
            "gpt-4o-mini": 128000,  # 128K tokens
            "gpt-4.1": 1047576,  # ~1M tokens (exato: 1.047.576)
            "gpt-4.1-mini": 1047576,  # ~1M tokens (exato: 1.047.576)
            "gpt-4.1-nano-2025-04-14": 1047576,  # ~1M tokens (exato: 1.047.576)
            "gpt-4.1-nano": 1047576,  # Alias simplificado
            "gpt-4.5": 1047576,  # Modelo sendo descontinuado em julho/2025
            
            # Modelos Anthropic (abril/2025)
            "claude-3-opus": 200000,  # 200K tokens (até 1M para clientes enterprise)
            "claude-3-sonnet": 200000,  # 200K tokens
            "claude-3.5-sonnet": 200000,  # 200K tokens
            "claude-3-haiku": 200000,  # 200K tokens
            "anthropic.claude-3-haiku": 200000,  # 200K tokens (alias alternativo)
            
            # Modelos Google (abril/2025)
            "gemini-pro": 32000,  # 32K tokens
            "gemini-flash": 32000,  # 32K tokens
            "gemini-1.5-pro": 1000000,  # 1M tokens
            "gemini-1.5-flash": 1000000,  # 1M tokens
            
            # Modelos Meta e Mistral (abril/2025)
            "llama-3-70b": 8192,  # 8K tokens  
            "llama-3-8b": 8192,  # 8K tokens
            "mistral-large": 32768,  # 32K tokens
            "mistral-medium": 32768  # 32K tokens
        }
        # Configurações recomendadas de chunking por tipo de conteúdo
        self.chunking_by_content = {
            "artigo_cientifico": {"chunk_size": 1500, "chunk_overlap": 150, "desc": "textos densos com citações e terminologia específica"},
            "literatura": {"chunk_size": 2000, "chunk_overlap": 200, "desc": "narrativas fluidas com contexto contínuo"},
            "documento_tecnico": {"chunk_size": 1000, "chunk_overlap": 150, "desc": "manuais técnicos com instruções específicas"},
            "conteudo_educacional": {"chunk_size": 1200, "chunk_overlap": 120, "desc": "textos didáticos com conceitos estruturados"},
            "documento_legal": {"chunk_size": 800, "chunk_overlap": 200, "desc": "textos normativos com linguagem formal e referências cruzadas"},
            "email_comunicacao": {"chunk_size": 500, "chunk_overlap": 50, "desc": "comunicações curtas e diretas"}
        }
    
    def analyze_sections(self, sections_dict):
        """
        Analisa um dicionário de seções e suas contagens de tokens.
        
        Args:
            sections_dict: Dict[str, int] - Um dicionário de seção -> contagem de tokens
            
        Returns:
            dict: Análise e recomendações
            
        Raises:
            ValueError: Se o dicionário de seções estiver vazio
        """
        if not sections_dict:
            logger.warning("Dicionário de seções vazio fornecido para análise")
            raise ValueError("O dicionário de seções não pode estar vazio")
            
        try:
            total_tokens = sum(sections_dict.values())
            model_limit = self.model_limits.get(self.model_name, 8000)
            
            logger.debug(f"Analisando documento de {total_tokens} tokens para modelo {self.model_name} (limite: {model_limit})")
            
            # Calcular percentuais
            percentages = {k: (v / total_tokens) * 100 for k, v in sections_dict.items()}
            
            # Ordenar seções por contagem de tokens (decrescente)
            sorted_sections = sorted(sections_dict.items(), key=lambda x: x[1], reverse=True)
            
            # Verificar se ultrapassa o limite do modelo
            exceeds_limit = total_tokens > model_limit
            
            # Identificar seções mais "custosas"
            expensive_sections = [s for s, t in sorted_sections if t > model_limit * 0.25]
            
            # Gerar recomendações
            recommendations = []
            if exceeds_limit:
                recommendations.append(f"O documento excede o limite do modelo {self.model_name} de {model_limit} tokens.")
                
                # Recomendar um modelo com capacidade suficiente
                suitable_models = []
                for model, limit in self.model_limits.items():
                    if limit >= total_tokens:
                        suitable_models.append((model, limit))
                
                if suitable_models:
                    # Ordenar modelos por limite (do menor para o maior suficiente)
                    suitable_models.sort(key=lambda x: x[1])
                    best_model, best_limit = suitable_models[0]
                    recommendations.append(f"Considere usar {best_model} que suporta até {best_limit} tokens.")
                else:
                    recommendations.append("O documento excede o limite de todos os modelos conhecidos. Considere dividir em múltiplos documentos.")
                
                # Recomendar perfis mais leves
                if any(s.lower().endswith('content') for s in sections_dict.keys()):
                    content_size = next((t for s, t in sections_dict.items() if s.lower().endswith('content')), 0)
                    if content_size < model_limit:
                        recommendations.append(f"Use o perfil 'llms-min' para reduzir para ~{content_size} tokens.")
                
                # Sugira chunking se existirem seções grandes
                if expensive_sections:
                    recommendations.append(f"As seções que mais consomem tokens são: {', '.join(expensive_sections)}.")
                    recommendations.append("Considere dividir o documento ou usar um chunking com tamanho menor.")
            else:
                recommendations.append(f"O documento está dentro do limite de {model_limit} tokens do modelo {self.model_name}.")
                
                # Se estiver muito próximo do limite
                if total_tokens > model_limit * 0.8:
                    recommendations.append("O documento está próximo do limite. Considere monitorar o crescimento do documento.")
                    
                # Sugestões de eficiência
                if "# Raw" in sections_dict and sections_dict["# Raw"] > total_tokens * 0.2:
                    recommendations.append("A seção Raw consome muitos tokens. Considere usar '--profile llms-min' para excluí-la.")
            
            logger.debug(f"Análise concluída: {len(recommendations)} recomendações geradas")
            
            return {
                "total_tokens": total_tokens,
                "model_limit": model_limit,
                "exceeds_limit": exceeds_limit,
                "percentages": percentages,
                "expensive_sections": expensive_sections,
                "recommendations": recommendations
            }
        except Exception as e:
            logger.error(f"Erro durante a análise de seções: {str(e)}")
            raise
    
    def analyze_document(self, content):
        """
        Analisa o conteúdo completo de um documento llms.txt.
        
        Args:
            content: str - O conteúdo completo do documento
            
        Returns:
            dict: Análise e recomendações
        """
        import re
        
        # Total de tokens
        total_tokens = count_tokens(content, self.model_name)
        
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
        
        # Contar tokens por seção
        sections_tokens = {sec: count_tokens(txt, self.model_name) for sec, txt in section_map.items()}
        
        # Para documentos muito grandes, extrair amostra representativa para análise
        content_sample = self._extract_content_sample(content, section_map, max_size=50000)
        
        # Identificar tipo de conteúdo baseado em palavras-chave e estrutura
        content_type = self._detect_content_type(content_sample, section_map)
        
        # Análise
        analysis = self.analyze_sections(sections_tokens)
        
        # Adicionar recomendações de chunking específicas
        if content_type:
            chunking = self.chunking_by_content.get(content_type)
            analysis['content_type'] = content_type
            analysis['chunking_recommendation'] = chunking
        
        return analysis

    def _extract_content_sample(self, content, section_map, max_size=50000):
        """
        Extrai uma amostra representativa do documento para análise de tipo.
        
        Args:
            content: Conteúdo completo do documento
            section_map: Mapa de seções extraído
            max_size: Tamanho máximo da amostra em caracteres
            
        Returns:
            str: Amostra representativa do documento
            
        Raises:
            ValueError: Se o conteúdo estiver vazio
        """
        if not content:
            logger.warning("Conteúdo vazio fornecido para extração de amostra")
            raise ValueError("O conteúdo não pode estar vazio")
            
        try:
            sample = []
            
            # Adicionar metadados e titles
            for section in section_map:
                if section.startswith('# Title') or section.startswith('# Date') or section.startswith('# Source'):
                    sample.append(section)
                    sample.append(section_map[section][:1000])  # Limitar a 1000 caracteres
            
            # Adicionar primeiras partes do conteúdo, onde geralmente está o título e introdução
            if '# Content' in section_map and section_map['# Content']:
                content_text = section_map['# Content']
                # Dividir em parágrafos e pegar os primeiros
                paragraphs = content_text.split('\n\n')
                for i, para in enumerate(paragraphs[:20]):  # Pegar até 20 parágrafos
                    if len('\n'.join(sample)) + len(para) < max_size:
                        sample.append(para)
                    else:
                        break
            
            # Garantir que temos palavras-chave do summary
            if '# Summary' in section_map and section_map['# Summary']:
                sample.append(section_map['# Summary'])
                
            # Se ainda não temos amostra suficiente, pegar dos títulos das seções grandes
            total_len = len('\n'.join(sample))
            if total_len < max_size / 2:
                # Extrair títulos e subtítulos (linhas começando com ## ou ###)
                import re
                for section_key, section_content in section_map.items():
                    if section_key in ['# Content', '# Tables']:
                        titles = re.findall(r'^#+\s+.*$', section_content, re.MULTILINE)
                        sample.extend(titles[:100])  # Adicionar até 100 títulos
            
            # Juntar tudo e garantir que não excede o tamanho máximo
            result = '\n'.join(sample)
            if len(result) > max_size:
                result = result[:max_size]
                
            return result
        except Exception as e:
            logger.error(f"Erro durante extração de amostra: {str(e)}")
            # Em caso de erro, retornar uma parte do conteúdo original
            logger.warning("Usando fallback para extração de amostra (primeiros caracteres)")
            return content[:min(max_size, len(content))]
    
    def _detect_content_type(self, content, section_map):
        """
        Detecta o tipo de conteúdo baseado em palavras-chave e estrutura.
        
        Args:
            content: Texto do documento ou amostra representativa
            section_map: Mapa de seções do documento
            
        Returns:
            str: Tipo de conteúdo detectado ou None
        """
        if not content:
            logger.warning("Conteúdo vazio fornecido para detecção de tipo")
            return None
            
        try:
            # Indicadores por tipo
            indicators = {
                "artigo_cientifico": ["abstract", "metodologia", "referências", "citações", "estudo", "pesquisa", "doi", "análise", "conclusão", "bibliografia"],
                "literatura": ["capítulo", "personagens", "história", "narrativa", "romance", "conto", "autor", "obra", "livro", "ficção"],
                "documento_tecnico": ["manual", "instruções", "especificações", "requisitos", "configuração", "implementação", "sistema", "software", "hardware", "versão"],
                "conteudo_educacional": ["aprendizagem", "exercícios", "habilidades", "competências", "bncc", "currículo", "educação", "ensino", "aluno", "professor", "disciplina", "conhecimento", "pedagógico", "escolar", "escola", "avaliação", "estudante", "ministério da educação", "diretrizes"],
                "documento_legal": ["lei", "artigo", "parágrafo", "norma", "normativo", "regulamento", "jurídico", "contrato", "decreto", "legislação", "cláusula", "judicial", "direito"],
                "email_comunicacao": ["assunto", "prezado", "cordialmente", "atenciosamente", "reunião", "informamos", "contato", "prezada", "encaminho", "conforme solicitado"]
            }
            
            # Normaliza o texto para contagem de indicadores
            normalized = content.lower()
            
            # Contagem de indicadores por tipo
            scores = {}
            for content_type, keywords in indicators.items():
                score = sum(1 for keyword in keywords if keyword.lower() in normalized)
                scores[content_type] = score
            
            # Verificações de estrutura específica
            if "BNCC" in content or "Base Nacional" in content or "Ministério da Educação" in content:
                scores["conteudo_educacional"] += 10
                
            if "código" in normalized or "programa" in normalized or "função" in normalized or "biblioteca" in normalized:
                scores["documento_tecnico"] += 5
                
            if "§" in content or "Art." in content or "Artigo" in content:
                scores["documento_legal"] += 5
                
            # Verifica seções específicas
            if "# Abstract" in section_map or "# Introduction" in section_map or "# Methodology" in section_map:
                scores["artigo_cientifico"] += 8
                
            # Debug: imprimir scores para verificar pontuação
            logger.debug("\nDetecção de tipo de conteúdo (scores):")
            for c_type, score in scores.items():
                logger.debug(f"- {c_type}: {score} pontos")
                
            # Determina o tipo com maior pontuação
            if scores:
                max_type = max(scores, key=scores.get)
                if scores[max_type] > 1:
                    logger.info(f"Tipo de conteúdo detectado: {max_type} com {scores[max_type]} pontos")
                    return max_type
                else:
                    logger.info("Pontuação insuficiente para determinar tipo de conteúdo")
            
            return None
        except Exception as e:
            logger.error(f"Erro durante detecção de tipo de conteúdo: {str(e)}")
            return None
            
    def get_recommendations_text(self, analysis):
        """
        Formata as recomendações em texto amigável.
        
        Args:
            analysis: dict - Resultado da análise
            
        Returns:
            str: Texto formatado com análise e recomendações
        """
        result = [
            "## Análise de Tokens",
            f"Total: {analysis['total_tokens']} tokens ({self.model_name})",
            f"Limite do modelo: {analysis['model_limit']} tokens",
            "",
            "### Distribuição por seção:",
        ]
        
        # Adicionar percentuais de cada seção
        for section, pct in analysis['percentages'].items():
            result.append(f"- {section}: {pct:.1f}%")
            
        result.append("")
        result.append("### Recomendações:")
        
        for rec in analysis['recommendations']:
            result.append(f"- {rec}")
            
        # Recomendações de chunking para o tipo de documento
        if 'content_type' in analysis and analysis['content_type']:
            content_type = analysis['content_type']
            chunking = analysis['chunking_recommendation']
            result.append("")
            result.append("### Sugestão de Chunking:")
            result.append(f"Tipo de conteúdo detectado: **{content_type.replace('_', ' ').title()}** ({chunking['desc']})")
            result.append(f"Configuração recomendada:")
            result.append(f"- `--chunk-size {chunking['chunk_size']}`")
            result.append(f"- `--chunk-overlap {chunking['chunk_overlap']}`")
            result.append(f"- Exemplo: `python -m src.main --file seu_arquivo.pdf --chunk-size {chunking['chunk_size']} --chunk-overlap {chunking['chunk_overlap']} --profile llms-full`")
            
        return "\n".join(result)