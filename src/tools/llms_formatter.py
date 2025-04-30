"""
Formatador de documentos no padrão LLMs.txt.

Este módulo formata documentos processados pelo Docling no formato LLMs.txt,
que é otimizado para modelos de linguagem.
"""

import re
from datetime import datetime
from src.utils.logging_config import setup_logger
from src.tools.token_counter import count_tokens

# Configurar logger para este módulo
logger = setup_logger(__name__)

class LLMSFormatter:
    """
    Classe para formatar documentos no padrão LLMs.txt.
    """
    
    def __init__(self):
        """
        Inicializa o formatador.
        """
        logger.debug("Inicializando LLMSFormatter")
        
    def format(self, doc, title="", date="", source="", profile="llms-full", modelo_llm="gpt-3.5-turbo"):
        """
        Formata um documento Docling no padrão LLMs.txt.
        
        Args:
            doc: Documento processado pelo Docling
            title (str): Título do documento
            date (str): Data do documento
            source (str): Fonte do documento
            profile (str): Perfil de formatação ('llms-full', 'llms-min', etc)
            modelo_llm (str): Nome do modelo para contagem de tokens
            
        Returns:
            str: Texto formatado no padrão LLMs.txt
            
        Raises:
            ValueError: Se o perfil não for reconhecido
        """
        try:
            logger.info(f"Formatando documento usando perfil '{profile}'")
            
            # Validar perfil
            valid_profiles = ["llms-min", "llms-ctx", "llms-tables", "llms-images", "llms-raw", "llms-full"]
            if profile not in valid_profiles:
                logger.warning(f"Perfil '{profile}' não reconhecido. Usando 'llms-full'.")
                profile = "llms-full"
            
            # Metadados mais detalhados
            metadados = {}
            
            # Metadados básicos
            if title:
                metadados["Title"] = title
            if date:
                metadados["Date"] = date
            if source:
                metadados["Source"] = source
                
            # Detectar autor se disponível
            if hasattr(doc, "metadata") and doc.metadata:
                if "author" in doc.metadata:
                    metadados["Author"] = doc.metadata["author"]
                elif "creator" in doc.metadata:
                    metadados["Author"] = doc.metadata["creator"]
                    
                # Adicionar outros metadados relevantes
                for key in ["subject", "keywords", "language", "created", "modified"]:
                    if key in doc.metadata:
                        metadados[key.title()] = doc.metadata[key]
            
            # Iniciar com metadados
            result = []
            for key, value in metadados.items():
                if value:
                    result.append(f"# {key}: {value}")
            
            # Extrair e formatar summary
            try:
                # Verificar se tem summary explícito
                if hasattr(doc, 'summary') and doc.summary:
                    summary = doc.summary
                    result.append("# Summary")
                    result.append(summary)
                    logger.debug("Adicionado summary ao documento formatado")
                # Se não tem summary, gerar a partir do conteúdo
                elif profile in ["llms-ctx", "llms-full"]:
                    # Extrair primeiro parágrafo significativo
                    summary = self._gerar_sumario_automatico(doc)
                    if summary:
                        result.append("# Summary")
                        result.append(summary)
                        logger.debug("Adicionado summary automático ao documento formatado")
            except Exception as e:
                logger.warning(f"Erro ao extrair summary: {str(e)}")
            
            # Formatar conteúdo principal
            try:
                result.append("# Content")
                # Obter texto principal do documento
                if hasattr(doc, 'export_to_markdown'):
                    # Método recomendado para obter conteúdo formatado
                    content = doc.export_to_markdown()
                    # Limpar marcação de imagens embutidas
                    content = re.sub(r'!\[.*?\]\(data:image/.*?\)', '[IMAGEM]', content)
                    result.append(content)
                else:
                    # Método legado
                    for chunk in doc.chunks:
                        if hasattr(chunk, 'text') and chunk.text:
                            result.append(chunk.text)
                logger.debug("Adicionado conteúdo principal ao documento formatado")
            except Exception as e:
                logger.error(f"Erro ao formatar conteúdo principal: {str(e)}")
                result.append("Erro ao processar conteúdo principal.")
            
            # Adicionar tabelas se perfil adequado
            if profile in ["llms-tables", "llms-full"]:
                try:
                    tables = []
                    # Tentar extrair tabelas do documento
                    if hasattr(doc, 'tables'):
                        tables = doc.tables
                    else:
                        # Método legado: extrair das chunks
                        for chunk in doc.chunks:
                            if hasattr(chunk, 'tables') and chunk.tables:
                                for table in chunk.tables:
                                    tables.append(table)
                    
                    if tables:
                        result.append("\n# Tables")
                        for i, table in enumerate(tables):
                            result.append(f"\n## Table {i+1}")
                            # Formatar tabela em markdown
                            if hasattr(table, 'to_markdown'):
                                # Método moderno
                                result.append(table.to_markdown())
                            else:
                                # Método legado
                                result.append(str(table))
                        logger.debug(f"Adicionadas {len(tables)} tabelas ao documento formatado")
                except Exception as e:
                    logger.warning(f"Erro ao processar tabelas: {str(e)}")
            
            # Adicionar imagens se perfil adequado
            if profile in ["llms-images", "llms-full"]:
                try:
                    images = []
                    # Tentar extrair imagens do documento
                    if hasattr(doc, 'images'):
                        images = doc.images
                    else:
                        # Método legado: extrair das chunks
                        for chunk in doc.chunks:
                            if hasattr(chunk, 'images') and chunk.images:
                                for img in chunk.images:
                                    images.append(img)
                    
                    if images:
                        result.append("\n# Images")
                        for i, img in enumerate(images):
                            result.append(f"\n## Image {i+1}")
                            # Extrair caption ou descrição
                            if hasattr(img, 'caption') and img.caption:
                                result.append(img.caption)
                            elif hasattr(img, 'description') and img.description:
                                result.append(img.description)
                            else:
                                result.append(f"Imagem {i+1} no documento")
                        logger.debug(f"Adicionadas {len(images)} imagens ao documento formatado")
                except Exception as e:
                    logger.warning(f"Erro ao processar imagens: {str(e)}")
            
            # Adicionar conteúdo raw se perfil adequado
            if profile in ["llms-raw", "llms-full"]:
                try:
                    if hasattr(doc, 'raw_text') and doc.raw_text:
                        result.append("\n# Raw")
                        result.append(doc.raw_text)
                        logger.debug("Adicionado conteúdo raw ao documento formatado")
                except Exception as e:
                    logger.warning(f"Erro ao adicionar conteúdo raw: {str(e)}")
            
            # Adicionar análise de tokens se perfil adequado
            if profile in ["llms-full"]:
                formatted_partial = "\n\n".join(result)
                token_count = count_tokens(formatted_partial, modelo_llm)
                
                result.append("\n# Token Analysis")
                result.append(f"Total tokens ({modelo_llm}): {token_count}")
                
                # Adicionar dicas sobre tamanho do documento
                result.append("## Observações:")
                from src.tools.token_analyzer import TokenAnalyzer
                analyzer = TokenAnalyzer(modelo_llm)
                model_limit = analyzer.model_limits.get(modelo_llm, 8000)
                
                if token_count > model_limit:
                    result.append(f"⚠️ Este documento excede o limite do modelo {modelo_llm} ({model_limit} tokens).")
                    result.append(f"Considere usar um modelo com maior capacidade ou dividir o documento em partes menores.")
                else:
                    result.append(f"✅ Este documento está dentro do limite do modelo {modelo_llm} ({model_limit} tokens).")
                    
                    # Calcular percentual de uso
                    usage_pct = (token_count / model_limit) * 100
                    if usage_pct > 80:
                        result.append(f"⚠️ O documento está utilizando {usage_pct:.1f}% da capacidade do modelo.")
                    else:
                        result.append(f"✅ O documento está utilizando apenas {usage_pct:.1f}% da capacidade do modelo.")
            
            # Juntar tudo em uma string
            formatted_text = "\n\n".join(result)
            logger.info(f"Documento formatado com sucesso: {len(formatted_text)} caracteres")
            return formatted_text
            
        except Exception as e:
            logger.error(f"Erro geral na formatação: {str(e)}")
            # Retornar um formato mínimo com mensagem de erro
            return f"# Error\n\nErro ao formatar documento: {str(e)}\n\n# Raw Content\n\n{str(doc)[:1000]}..."
    
    def _gerar_sumario_automatico(self, doc):
        """
        Gera um sumário automático a partir do documento.
        
        Args:
            doc: Documento processado pelo Docling
            
        Returns:
            str: Sumário do documento
        """
        try:
            # Tentar extrair primeiros parágrafos significativos
            summary = ""
            
            # Método 1: Usar export_to_markdown e extrair início
            if hasattr(doc, 'export_to_markdown'):
                content = doc.export_to_markdown()
                
                # Remover linhas vazias e quebras
                content = re.sub(r'\n\s*\n', '\n\n', content)
                
                # Extrair título se existir (primeira linha com #)
                title_match = re.search(r'^#+\s+(.+)$', content, re.MULTILINE)
                if title_match:
                    title = title_match.group(1)
                    summary += f"{title}\n\n"
                
                # Dividir em parágrafos e pegar os primeiros significativos
                paragraphs = content.split('\n\n')
                significant_paragraphs = []
                
                for p in paragraphs:
                    # Pular linhas com # (títulos) já processados
                    if p.strip().startswith('#'):
                        continue
                    
                    # Pular linhas muito curtas (menos de 40 caracteres)
                    if len(p.strip()) < 40:
                        continue
                    
                    # Adicionar parágrafo significativo
                    significant_paragraphs.append(p.strip())
                    
                    # Limitar a 2 parágrafos significativos
                    if len(significant_paragraphs) >= 2:
                        break
                
                # Juntar parágrafos significativos
                if significant_paragraphs:
                    summary += "\n\n".join(significant_paragraphs)
            
            # Método 2 (fallback): Extrair das chunks
            if not summary and hasattr(doc, 'chunks'):
                text_chunks = []
                
                for chunk in doc.chunks:
                    if hasattr(chunk, 'text') and chunk.text:
                        # Pular chunks muito curtos
                        if len(chunk.text.strip()) < 40:
                            continue
                        
                        text_chunks.append(chunk.text.strip())
                        
                        # Limitar a 2 chunks significativos
                        if len(text_chunks) >= 2:
                            break
                
                if text_chunks:
                    summary = "\n\n".join(text_chunks)
            
            # Limitar tamanho do sumário
            if summary:
                # Limitar a 1000 caracteres
                if len(summary) > 1000:
                    # Truncar no final do último parágrafo completo
                    last_paragraph_end = summary[:1000].rfind('\n\n')
                    if last_paragraph_end > 0:
                        summary = summary[:last_paragraph_end]
                    else:
                        # Se não encontrar parágrafo, truncar na última frase completa
                        last_sentence_end = max(
                            summary[:1000].rfind('. '), 
                            summary[:1000].rfind('! '), 
                            summary[:1000].rfind('? ')
                        )
                        if last_sentence_end > 0:
                            summary = summary[:last_sentence_end+1]
                        else:
                            # Último recurso: truncar em 1000 caracteres
                            summary = summary[:1000] + "..."
            
            return summary
            
        except Exception as e:
            logger.warning(f"Erro ao gerar sumário automático: {str(e)}")
            return None
    
    def _limpar_markdown(self, content):
        """
        Limpa e normaliza o markdown para formato LLMs.txt.
        
        Args:
            content (str): Texto em formato markdown
            
        Returns:
            str: Texto limpo e normalizado
        """
        # Remover URLs de imagens
        content = re.sub(r'!\[.*?\]\(.*?\)', '[IMAGEM]', content)
        
        # Limpar URLs longas
        content = re.sub(r'\[([^\]]+)\]\(https?:\/\/[^\s]{60,}\)', r'\1', content)
        
        # Normalizar quebras de linha
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content
