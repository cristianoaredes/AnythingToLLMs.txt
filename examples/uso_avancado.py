#!/usr/bin/env python
"""
Exemplo de uso avançado do Anything to LLMs.txt

Este script demonstra como utilizar recursos avançados do Anything to LLMs.txt,
incluindo múltiplos motores de OCR, múltiplos formatos de saída, chunking inteligente
e integração com frameworks de IA como LangChain e LlamaIndex.
"""

import os
import sys
import json
from pathlib import Path

# Adicionar diretório pai ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.document_converter import DocumentConverterTool
from src.tools.token_analyzer import TokenAnalyzer
from src.tools.token_counter import count_tokens
from src.tools.smoldocling_processor import SmolDoclingProcessor
from src.utils.logging_config import setup_logger

# Configurar logger
logger = setup_logger(__name__, log_level="DEBUG")

def exemplo_conversao_basica():
    """
    Exemplo de conversão básica de um documento PDF para formato LLMs.txt
    """
    print("\n===== Exemplo de Conversão Básica =====")
    
    # Inicializar conversor
    converter = DocumentConverterTool()
    
    # Arquivo de exemplo
    arquivo = "data/test_files/CF88_Livro_EC91_2016.pdf"
    
    # Processar documento
    resultado = converter.run(
        arquivo,
        save_output=True,
        profile="llms-full"
    )
    
    # Exibir preview do resultado
    if "llms" in resultado["formats"]:
        preview = resultado["formats"]["llms"][:500] + "..." if len(resultado["formats"]["llms"]) > 500 else resultado["formats"]["llms"]
        print(f"\nPreview do resultado:\n{preview}")
    
    print("\nConversão básica concluída!")

def exemplo_ocr_avancado():
    """
    Exemplo de uso de diferentes motores de OCR
    """
    print("\n===== Exemplo de OCR Avançado =====")
    
    # Inicializar conversor
    converter = DocumentConverterTool()
    
    # Arquivo de exemplo (de preferência uma imagem ou PDF escaneado)
    # Usar um arquivo que sabidamente contém texto em imagem
    arquivo = "data/test_files/CF88_Livro_EC91_2016.pdf"  # Substitua por um PDF escaneado real
    
    # Lista de motores OCR disponíveis
    motores_ocr = ["easyocr", "tesseract_cli"]
    
    for motor in motores_ocr:
        print(f"\nProcessando com motor OCR: {motor}")
        
        # Processar documento com motor OCR específico
        resultado = converter.run(
            arquivo,
            save_output=True,
            profile="llms-min",
            ocr_engine=motor,
            force_ocr=True
        )
        
        # Exibir preview do resultado
        if "llms" in resultado["formats"]:
            preview = resultado["formats"]["llms"][:200] + "..." if len(resultado["formats"]["llms"]) > 200 else resultado["formats"]["llms"]
            print(f"Preview do resultado com {motor}:\n{preview}")
    
    print("\nExemplo de OCR avançado concluído!")

def exemplo_multiplos_formatos():
    """
    Exemplo de exportação em múltiplos formatos
    """
    print("\n===== Exemplo de Múltiplos Formatos de Exportação =====")
    
    # Inicializar conversor
    converter = DocumentConverterTool()
    
    # Arquivo de exemplo
    arquivo = "data/test_files/CF88_Livro_EC91_2016.pdf"
    
    # Processar documento com múltiplos formatos de saída
    resultado = converter.run(
        arquivo,
        save_output=True,
        profile="llms-full",
        export_formats=["md", "json", "html"]
    )
    
    # Exibir informações sobre os formatos gerados
    formatos = resultado["formats"]
    for formato, conteudo in formatos.items():
        tamanho = len(conteudo) if isinstance(conteudo, str) else (len(json.dumps(conteudo)) if isinstance(conteudo, dict) else 0)
        print(f"Formato {formato}: {tamanho} caracteres")
    
    print("\nExemplo de múltiplos formatos concluído!")

def exemplo_chunking_inteligente():
    """
    Exemplo de chunking inteligente para diferentes modelos de LLM
    """
    print("\n===== Exemplo de Chunking Inteligente =====")
    
    # Inicializar conversor
    converter = DocumentConverterTool()
    
    # Arquivo de exemplo
    arquivo = "data/test_files/CF88_Livro_EC91_2016.pdf"
    
    # Processar documento
    resultado = converter.run(
        arquivo,
        save_output=True,
        profile="llms-min"
    )
    
    # Obter documento
    doc = resultado["doc"]
    
    # Testar chunking para diferentes modelos
    modelos = ["gpt-3.5-turbo", "gpt-4", "claude-3-sonnet"]
    tamanhos_chunk = [1000, 4000, 8000]
    
    for modelo, tamanho in zip(modelos, tamanhos_chunk):
        print(f"\nCriando chunks para modelo {modelo} com tamanho máximo de {tamanho} tokens")
        
        # Criar chunks otimizados para o modelo
        chunks = converter.criar_chunks(doc, modelo, tamanho)
        
        if chunks:
            print(f"Criados {len(chunks)} chunks")
            
            # Exibir preview do primeiro chunk
            if chunks:
                preview = chunks[0][:200] + "..." if len(chunks[0]) > 200 else chunks[0]
                print(f"Preview do primeiro chunk:\n{preview}")
                
                # Contar tokens
                tokens = count_tokens(chunks[0], modelo)
                print(f"Tokens no primeiro chunk: {tokens}")
        else:
            print("Não foi possível criar chunks")
    
    print("\nExemplo de chunking inteligente concluído!")

def exemplo_integracao_frameworks():
    """
    Exemplo de integração com frameworks de IA como LangChain
    """
    print("\n===== Exemplo de Integração com Frameworks de IA =====")
    
    # Inicializar conversor
    converter = DocumentConverterTool()
    
    # Arquivo de exemplo
    arquivo = "data/test_files/CF88_Livro_EC91_2016.pdf"
    
    # Processar documento
    resultado = converter.run(
        arquivo,
        save_output=True,
        profile="llms-min"
    )
    
    # Obter documento
    doc = resultado["doc"]
    
    # Verificar se LangChain está disponível
    try:
        langchain_docs = converter.exportar_para_langchain(doc)
        if langchain_docs:
            print(f"\nExportado para LangChain: {len(langchain_docs)} documentos")
            if langchain_docs:
                print(f"Metadados do primeiro documento LangChain: {langchain_docs[0].metadata}")
        else:
            print("\nNão foi possível exportar para LangChain (verifique se langchain-core está instalado)")
    except Exception as e:
        print(f"\nErro ao exportar para LangChain: {str(e)}")
    
    print("\nExemplo de integração com frameworks concluído!")

def exemplo_analise_tokens():
    """
    Exemplo de análise de tokens para otimização de documentos
    """
    print("\n===== Exemplo de Análise de Tokens =====")
    
    # Inicializar conversor
    converter = DocumentConverterTool()
    
    # Arquivo de exemplo
    arquivo = "data/test_files/CF88_Livro_EC91_2016.pdf"
    
    # Processar documento
    resultado = converter.run(
        arquivo,
        save_output=True,
        profile="llms-full"
    )
    
    # Obter texto LLMs.txt
    llms_text = resultado["formats"]["llms"]
    
    # Inicializar analisador de tokens
    analyzer = TokenAnalyzer("gpt-3.5-turbo")
    
    # Analisar tokens
    import re
    
    # Extrair seções
    sections = re.split(r'(^# .+)', llms_text, flags=re.MULTILINE)
    section_map = {}
    current = None
    for part in sections:
        if part.strip().startswith('# '):
            current = part.strip()
            section_map[current] = ''
        elif current:
            section_map[current] += part
    
    # Contar tokens por seção
    section_tokens = {sec: count_tokens(txt, "gpt-3.5-turbo") for sec, txt in section_map.items()}
    
    # Exibir contagem por seção
    for sec, tokens in section_tokens.items():
        print(f"{sec}: {tokens} tokens")
    
    # Análise e recomendações
    analysis = analyzer.analyze_sections(section_tokens)
    recommendations = analyzer.get_recommendations_text(analysis)
    print(f"\n{recommendations}")
    
    print("\nExemplo de análise de tokens concluído!")

def exemplo_smoldocling():
    """
    Exemplo de uso do SmolDocling para processamento de imagens e PDFs
    """
    print("\n===== Exemplo de SmolDocling =====")
    
    # Inicializar processador SmolDocling
    processor = SmolDoclingProcessor()
    
    # Verificar se SmolDocling está disponível
    features = processor.get_features()
    if not features["available"]:
        print("SmolDocling não está disponível. Instale torch e transformers para usar esta funcionalidade.")
        return
    
    print(f"SmolDocling disponível: {features['available']}")
    print(f"Dispositivo: {features['device']}")
    print("Capacidades:")
    for cap in features["capabilities"]:
        print(f"- {cap}")
    
    # Tentar processar uma imagem ou PDF, se disponível
    # Usar uma imagem de teste se disponível
    image_test_files = [
        "data/test_files/CF88_Livro_EC91_2016.pdf",  # Tenta primeiro o PDF de exemplo
        # Adicionar outros caminhos de imagens de teste aqui
    ]
    
    for test_file in image_test_files:
        if os.path.exists(test_file):
            print(f"\nProcessando {test_file} com SmolDocling...")
            
            # Processar imagem/PDF
            try:
                doc = processor.process_document(test_file)
                if doc:
                    print("Documento processado com sucesso!")
                    
                    # Exportar para markdown
                    if hasattr(doc, 'export_to_markdown'):
                        md_text = doc.export_to_markdown()
                        preview = md_text[:500] + "..." if len(md_text) > 500 else md_text
                        print(f"\nPreview do resultado:\n{preview}")
                    else:
                        print("Documento não tem método export_to_markdown")
                else:
                    print("Falha ao processar documento")
            except Exception as e:
                print(f"Erro ao processar documento: {str(e)}")
            
            # Processar apenas o primeiro arquivo encontrado
            break
    else:
        print("Nenhum arquivo de teste encontrado para processamento com SmolDocling")
    
    print("\nExemplo de SmolDocling concluído!")

def exemplo_processamento_lote():
    """
    Exemplo de processamento em lote de múltiplos arquivos
    """
    print("\n===== Exemplo de Processamento em Lote =====")
    
    # Pasta de exemplo
    pasta = "data/test_files"
    
    # Verificar se pasta existe
    if not os.path.isdir(pasta):
        print(f"Pasta {pasta} não encontrada")
        return
    
    # Coletar arquivos compatíveis
    arquivos = []
    extensoes = ['.pdf', '.docx', '.html', '.txt', '.md']
    
    for arquivo in os.listdir(pasta):
        if any(arquivo.lower().endswith(ext) for ext in extensoes):
            arquivos.append(os.path.join(pasta, arquivo))
    
    if not arquivos:
        print(f"Nenhum arquivo compatível encontrado em {pasta}")
        return
    
    print(f"Encontrados {len(arquivos)} arquivos compatíveis:")
    for arquivo in arquivos:
        print(f"- {os.path.basename(arquivo)}")
    
    # Inicializar conversor
    converter = DocumentConverterTool()
    
    # Processar cada arquivo
    for i, arquivo in enumerate(arquivos):
        print(f"\n[{i+1}/{len(arquivos)}] Processando {os.path.basename(arquivo)}...")
        
        try:
            resultado = converter.run(
                arquivo,
                save_output=True,
                profile="llms-min"
            )
            
            if "llms" in resultado["formats"]:
                tokens = count_tokens(resultado["formats"]["llms"], "gpt-3.5-turbo")
                print(f"Documento processado: {tokens} tokens")
        except Exception as e:
            print(f"Erro ao processar {os.path.basename(arquivo)}: {str(e)}")
    
    print("\nProcessamento em lote concluído!")

if __name__ == "__main__":
    print("Exemplos de uso avançado do Anything to LLMs.txt")
    
    # Executar exemplos
    try:
        exemplo_conversao_basica()
    except Exception as e:
        print(f"Erro no exemplo de conversão básica: {str(e)}")
    
    try:
        exemplo_ocr_avancado()
    except Exception as e:
        print(f"Erro no exemplo de OCR avançado: {str(e)}")
    
    try:
        exemplo_multiplos_formatos()
    except Exception as e:
        print(f"Erro no exemplo de múltiplos formatos: {str(e)}")
    
    try:
        exemplo_chunking_inteligente()
    except Exception as e:
        print(f"Erro no exemplo de chunking inteligente: {str(e)}")
    
    try:
        exemplo_integracao_frameworks()
    except Exception as e:
        print(f"Erro no exemplo de integração com frameworks: {str(e)}")
    
    try:
        exemplo_analise_tokens()
    except Exception as e:
        print(f"Erro no exemplo de análise de tokens: {str(e)}")
    
    try:
        exemplo_processamento_lote()
    except Exception as e:
        print(f"Erro no exemplo de processamento em lote: {str(e)}")
    
    # O exemplo SmolDocling é opcional e depende de dependências adicionais
    try:
        exemplo_smoldocling()
    except Exception as e:
        print(f"Erro no exemplo de SmolDocling: {str(e)}")
    
    print("\nTodos os exemplos foram executados!")
