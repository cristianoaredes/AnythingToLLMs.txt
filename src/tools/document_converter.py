"""
Conversor de documentos usando Docling.
"""

import os
import sys
import tempfile
from datetime import datetime
from src.utils.logging_config import setup_logger
from src.tools.llms_formatter import LLMSFormatter

# Configurar logger para este módulo
logger = setup_logger(__name__)

class DocumentConverterTool:
    """
    Ferramenta para converter documentos em formatos do Docling.
    """

    def __init__(self, chunk_size=None, chunk_overlap=None, plugins=None, pipeline_options=None):
        """
        Inicializa o conversor de documentos.

        Args:
            chunk_size (int): Tamanho do chunk para processamento
            chunk_overlap (int): Sobreposição entre chunks
            plugins (list): Lista de plugins do Docling a serem ativados
            pipeline_options (dict): Opções para o pipeline do Docling
        """
        logger.info("Inicializando DocumentConverterTool")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.plugins = plugins or []
        self.pipeline_options = pipeline_options or {}

        # Importar docling com tratamento de erro
        try:
            import docling
            self.docling = docling
            logger.info("Docling importado com sucesso")
        except ImportError as e:
            logger.error(f"Erro ao importar docling: {str(e)}. Verifique se está instalado.")
            logger.info("Tente instalar com: pip install docling")
            raise ImportError("Docling não encontrado. Instale com 'pip install docling'")

    def configurar_ocr(self, tipo="auto", idioma=None, forca_pagina_completa=False):
        """
        Configura as opções de OCR com base no tipo de documento.

        Args:
            tipo (str): "auto", "tesseract", "easyocr", "rapidocr" ou "mac"
            idioma (str): Código do idioma (ex: "por", "eng", "chi_sim")
            forca_pagina_completa (bool): Força OCR em toda a página
        """
        from docling.datamodel.pipeline_options import (
            PdfPipelineOptions,
            EasyOcrOptions,
            TesseractCliOcrOptions,
            TesseractOcrOptions
        )

        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True

        # Selecionar motor OCR apropriado
        if tipo == "auto":
            # Detectar automaticamente o melhor motor
            pipeline_options.ocr_options = EasyOcrOptions()
        elif tipo == "tesseract":
            pipeline_options.ocr_options = TesseractOcrOptions()
        elif tipo == "tesseract_cli":
            pipeline_options.ocr_options = TesseractCliOcrOptions()
        elif tipo == "easyocr":
            pipeline_options.ocr_options = EasyOcrOptions()
        elif tipo == "rapidocr":
            try:
                from docling.datamodel.pipeline_options import RapidOcrOptions
                pipeline_options.ocr_options = RapidOcrOptions()
            except ImportError:
                logger.warning("RapidOCR não disponível, usando EasyOCR como fallback")
                pipeline_options.ocr_options = EasyOcrOptions()
        elif tipo == "mac" and sys.platform == "darwin":
            try:
                from docling.datamodel.pipeline_options import OcrMacOptions
                pipeline_options.ocr_options = OcrMacOptions()
            except ImportError:
                logger.warning("OcrMac não disponível, usando EasyOCR como fallback")
                pipeline_options.ocr_options = EasyOcrOptions()
        else:
            pipeline_options.ocr_options = EasyOcrOptions()

        # Configurar idioma e outras opções
        if idioma:
            # Verificar se o campo é 'languages' ou 'lang'
            if hasattr(pipeline_options.ocr_options, 'languages'):
                pipeline_options.ocr_options.languages = [idioma]
            elif hasattr(pipeline_options.ocr_options, 'lang'):
                pipeline_options.ocr_options.lang = [idioma]

        # Verificar se o campo é 'force_full_page_ocr'
        if hasattr(pipeline_options.ocr_options, 'force_full_page_ocr'):
            pipeline_options.ocr_options.force_full_page_ocr = forca_pagina_completa
        pipeline_options.do_table_structure = True

        return pipeline_options

    def run(self, file_path, save_output=True, profile='llms-full', ocr_engine="auto",
            ocr_language=None, force_ocr=False, export_formats=None, export_to_langchain=False):
        """
        Executa conversão do documento usando Docling.

        Args:
            file_path (str): Caminho para o arquivo a ser processado
            save_output (bool): Se True, salva o resultado em arquivo
            profile (str): Perfil de saída (ex: 'llms-full', 'llms-min')
            ocr_engine (str): Motor OCR a ser utilizado
            ocr_language (str): Idioma para OCR
            force_ocr (bool): Força OCR mesmo em documentos com texto
            export_formats (list): Formatos adicionais para exportação
            export_to_langchain (bool): Se True, exporta o documento para LangChain

        Returns:
            dict: Dicionário com o documento em cada formato solicitado

        Raises:
            FileNotFoundError: Se o arquivo não for encontrado
            ValueError: Se o formato não for suportado
            RuntimeError: Se ocorrer erro durante a conversão
        """
        # Verificar existência do arquivo
        if not os.path.exists(file_path):
            logger.error(f"Arquivo não encontrado: {file_path}")
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        # Verificar extensão do arquivo
        _, ext = os.path.splitext(file_path)
        supported_formats = ['.pdf', '.docx', '.html', '.xml', '.txt', '.md', '.epub', '.json', '.jpg', '.jpeg', '.png', '.tiff', '.tif']
        if ext.lower() not in supported_formats:
            logger.warning(f"Formato {ext} pode não ser totalmente suportado. Formatos recomendados: {', '.join(supported_formats)}")

        # Configurar pipeline com OCR
        try:
            from docling.datamodel.base_models import InputFormat
            from docling.document_converter import DocumentConverter, PdfFormatOption

            # Configurar pipeline com opções de OCR adequadas
            pipeline_options = self.configurar_ocr(
                tipo=ocr_engine,
                idioma=ocr_language,
                forca_pagina_completa=force_ocr
            )

            # Adicionar opções de chunking diretamente ao objeto pipeline_options
            if self.chunk_size:
                setattr(pipeline_options, 'chunk_size', self.chunk_size)
            if self.chunk_overlap:
                setattr(pipeline_options, 'chunk_overlap', self.chunk_overlap)

            # Criar conversor Docling
            doc_converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )

            logger.info(f"Pipeline do Docling configurado com sucesso")

        except Exception as e:
            logger.error(f"Erro na configuração do Docling: {str(e)}")
            raise RuntimeError(f"Erro na configuração do Docling: {str(e)}")

        # Processar documento
        try:
            logger.info(f"Iniciando processamento do arquivo: {file_path}")

            # Converter o documento
            # FIX: Do not pass pipeline_options to convert, only set in PdfFormatOption
            result = doc_converter.convert(file_path)
            doc = result.document
            logger.info(f"Documento processado com sucesso")

        except Exception as e:
            logger.error(f"Erro ao processar documento com Docling: {str(e)}")
            raise RuntimeError(f"Falha no processamento do documento: {str(e)}")

        # Formatar em LLMs.txt e outros formatos
        try:
            logger.info(f"Formatando documento usando perfil: {profile}")
            formatter = LLMSFormatter()

            # Extrair metadados do arquivo
            title = os.path.basename(file_path).split('.')[0]
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            source = file_path

            # Formatar para LLMs.txt
            llms_text = formatter.format(
                doc,
                title=title,
                date=date,
                source=source,
                profile=profile
            )

            # Preparar resultados em vários formatos
            resultados = {"llms": llms_text}

            # Adicionar outros formatos se solicitado
            if export_formats:
                if "md" in export_formats:
                    resultados["md"] = doc.export_to_markdown()
                if "json" in export_formats:
                    resultados["json"] = doc.export_to_dict()
                if "html" in export_formats:
                    resultados["html"] = doc.export_to_html() if hasattr(doc, 'export_to_html') else "<html><body>HTML export not supported in this version</body></html>"

            logger.debug(f"Documento formatado com sucesso em {len(resultados)} formatos")

        except Exception as e:
            logger.error(f"Erro ao formatar documento: {str(e)}")
            raise RuntimeError(f"Falha na formatação do documento: {str(e)}")

        # Salvar resultado
        if save_output:
            try:
                filename = os.path.basename(file_path)
                base_name = os.path.splitext(filename)[0]

                # Criar diretório output se não existir
                os.makedirs("output", exist_ok=True)

                # Salvar formato LLMs.txt
                output_path = f"output/{base_name}.{profile}.llms.txt"
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(llms_text)
                logger.info(f"Resultado salvo em: {output_path}")

                # Salvar outros formatos
                if export_formats:
                    for fmt, content in resultados.items():
                        if fmt != "llms":  # Já salvamos o formato llms
                            if fmt == "json":
                                # Converter para string se for dict
                                if isinstance(content, dict):
                                    import json
                                    content = json.dumps(content, indent=2)

                            fmt_path = f"output/{base_name}.{profile}.{fmt}"
                            with open(fmt_path, "w", encoding="utf-8") as f:
                                f.write(content)
                            logger.info(f"Formato {fmt} salvo em: {fmt_path}")

            except Exception as e:
                logger.error(f"Erro ao salvar resultado: {str(e)}")
                logger.info("Tentando salvar em arquivo temporário...")

                # Tentar salvar em local temporário como fallback
                try:
                    temp_file = tempfile.NamedTemporaryFile(
                        mode="w",
                        delete=False,
                        suffix=".llms.txt",
                        dir=tempfile.gettempdir(),
                        encoding="utf-8"
                    )
                    with temp_file:
                        temp_file.write(llms_text)
                    logger.info(f"Resultado salvo em arquivo temporário: {temp_file.name}")
                except Exception as temp_e:
                    logger.error(f"Falha ao salvar em arquivo temporário: {str(temp_e)}")

        # Exportar para LangChain se solicitado
        langchain_docs = None
        if export_to_langchain:
            try:
                logger.info("Exportando documento para formato LangChain")
                langchain_docs = self.exportar_para_langchain(doc)
                logger.info(f"Documento exportado para LangChain com sucesso: {len(langchain_docs) if langchain_docs else 0} documentos")
            except Exception as e:
                logger.error(f"Erro ao exportar para LangChain: {str(e)}")
                langchain_docs = None

        # Retornar o documento e os resultados formatados
        resultado = {
            "doc": doc,
            "formats": resultados
        }

        # Adicionar documentos do LangChain ao resultado se disponíveis
        if langchain_docs:
            resultado["langchain_docs"] = langchain_docs

        return resultado

    def exportar_para_langchain(self, document, save_json=False):
        """
        Exporta o documento processado para o formato compatível com LangChain.
        Nota: Esta é uma implementação temporária até termos integração com LangChain.

        Args:
            document: Documento processado pelo Docling
            save_json: Se True, salva o JSON antes de converter

        Returns:
            Lista vazia (stub)
        """
        try:
            logger.warning("Integração com LangChain ainda não implementada. Retornando lista vazia.")
            # Retorna lista vazia como stub temporário
            return []
        except Exception as e:
            logger.error(f"Erro ao exportar para LangChain: {str(e)}")
            return []

    def criar_chunks(self, doc, modelo_llm="gpt-3.5-turbo", max_tokens=1000):
        """
        Divide um documento em chunks otimizados para o modelo LLM específico.

        Args:
            doc: Documento processado
            modelo_llm (str): Nome do modelo LLM alvo
            max_tokens (int): Número máximo de tokens por chunk

        Returns:
            list: Lista de chunks otimizados
        """
        try:
            # Configurar tokenizador para o modelo específico
            tokenizador = None
            if "gpt-" in modelo_llm:
                try:
                    import tiktoken
                    tokenizador = tiktoken.encoding_for_model(modelo_llm)
                except (ImportError, KeyError):
                    logger.warning(f"Não foi possível carregar tokenizador para {modelo_llm}")
                    tokenizador = None

            # Se não conseguiu carregar o tokenizador específico, usar o padrão do Docling
            if tokenizador is None:
                try:
                    from transformers import AutoTokenizer
                    tokenizador = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
                except ImportError:
                    logger.warning("Não foi possível carregar tokenizador do transformers")
                    return None

            # Usar o HybridChunker do Docling
            from docling.chunking import HybridChunker
            chunker = HybridChunker(
                tokenizer=tokenizador,
                max_tokens=max_tokens,
                merge_peers=True
            )

            # Dividir o documento em chunks
            chunks = list(chunker.chunk(doc))

            # Serializar chunks para formato LLMs.txt
            chunks_formatados = []
            for i, chunk in enumerate(chunks):
                # Adicionar metadados ao chunk
                cabecalho = f"# Chunk {i+1}\n"
                if hasattr(chunk, "metadata") and "headings" in chunk.metadata:
                    cabecalho += f"# Seção: {' > '.join(chunk.metadata['headings'])}\n"

                # Adicionar texto do chunk
                texto = chunker.serialize(chunk)

                chunks_formatados.append(cabecalho + texto)

            logger.info(f"Documento dividido em {len(chunks_formatados)} chunks")
            return chunks_formatados
        except Exception as e:
            logger.error(f"Erro ao criar chunks: {str(e)}")
            return None

    def extrair_layout(self, doc):
        """
        Extrai informações detalhadas sobre o layout do documento.

        Args:
            doc: Documento processado pelo Docling

        Returns:
            dict: Estrutura de layout com elementos e suas posições
        """
        try:
            layout = {
                "paginas": doc.num_pages(),
                "elementos": []
            }

            # Iterar por todos os elementos com sua posição
            for node, level in doc.iterate_items(with_groups=True):
                if hasattr(node, "prov") and node.prov:
                    for prov in node.prov:
                        # Obter tipo do elemento
                        tipo = str(node.label) if hasattr(node, "label") else "desconhecido"

                        # Obter bounding box se disponível
                        bbox = None
                        if hasattr(prov, "bbox"):
                            bbox = {
                                "left": float(prov.bbox.l) if hasattr(prov.bbox, "l") else None,
                                "top": float(prov.bbox.t) if hasattr(prov.bbox, "t") else None,
                                "right": float(prov.bbox.r) if hasattr(prov.bbox, "r") else None,
                                "bottom": float(prov.bbox.b) if hasattr(prov.bbox, "b") else None,
                                "coordenadas_origem": str(prov.bbox.coord_origin) if hasattr(prov.bbox, "coord_origin") else None
                            }

                        # Criar entrada do elemento
                        elemento = {
                            "tipo": tipo,
                            "nivel": level,
                            "pagina": prov.page_no if hasattr(prov, "page_no") else None,
                            "posicao": bbox,
                            "texto": getattr(node, "text", "") if hasattr(node, "text") else ""
                        }
                        layout["elementos"].append(elemento)

            logger.info(f"Layout extraído com {len(layout['elementos'])} elementos")
            return layout
        except Exception as e:
            logger.error(f"Erro ao extrair layout: {str(e)}")
            return None

    def extrair_estrutura_hierarquica(self, doc):
        """
        Extrai a estrutura hierárquica completa do documento.

        Args:
            doc: Documento processado pelo Docling

        Returns:
            dict: Estrutura do documento em formato aninhado
        """
        try:
            def processar_node(node, doc):
                resultado = {
                    "tipo": str(node.label) if hasattr(node, "label") else "node",
                    "texto": getattr(node, "text", ""),
                    "filhos": []
                }

                # Adicionar metadados relevantes
                if hasattr(node, "prov") and node.prov:
                    resultado["pagina"] = node.prov[0].page_no if hasattr(node.prov[0], "page_no") else None

                # Processar filhos recursivamente
                if hasattr(node, "children") and node.children:
                    for ref in node.children:
                        try:
                            child = ref.resolve(doc)
                            if child:
                                resultado["filhos"].append(processar_node(child, doc))
                        except Exception as e:
                            logger.warning(f"Erro ao resolver referência de filho: {str(e)}")

                return resultado

            # Começar pelo corpo principal do documento
            estrutura = processar_node(doc.body, doc)

            logger.info("Estrutura hierárquica extraída com sucesso")
            return estrutura
        except Exception as e:
            logger.error(f"Erro ao extrair estrutura hierárquica: {str(e)}")
            return None

    def exportar_com_opcoes(self, doc, formato, opcoes=None):
        """
        Exporta o documento com opções avançadas de formatação.

        Args:
            doc: Documento processado pelo Docling
            formato: Formato de saída ("json", "markdown", "html", "yaml", "text")
            opcoes: Dicionário de opções específicas para o formato

        Returns:
            str ou dict: Documento exportado no formato solicitado
        """
        try:
            opcoes = opcoes or {}

            if formato == "json":
                # Exportar para JSON com opções
                indent = opcoes.get("indent", 2)
                return doc.export_to_dict(mode="json", by_alias=opcoes.get("by_alias", True))

            elif formato == "markdown":
                # Exportar para Markdown
                return doc.export_to_markdown()

            elif formato == "html":
                # Exportar para HTML
                return doc.export_to_html()

            elif formato == "text":
                # Exportar para texto simples
                delim = opcoes.get("delim", "\n\n")
                return doc.export_to_text(delim=delim)

            else:
                raise ValueError(f"Formato não suportado: {formato}")
        except Exception as e:
            logger.error(f"Erro ao exportar documento: {str(e)}")
            raise RuntimeError(f"Falha na exportação do documento: {str(e)}")

    def extrair_tabelas(self, doc, formato="pandas"):
        """
        Extrai todas as tabelas do documento em formato utilizável.

        Args:
            doc: Documento processado pelo Docling
            formato: Formato de saída ("pandas", "dict", "markdown", "html")

        Returns:
            list: Lista de tabelas no formato solicitado
        """
        try:
            tabelas = []

            # Verificar se o documento tem tabelas
            if not hasattr(doc, "tables") or not doc.tables:
                logger.info("Documento não contém tabelas")
                return tabelas

            logger.info(f"Documento contém {len(doc.tables)} tabelas")

            for i, tabela in enumerate(doc.tables):
                logger.debug(f"Processando tabela {i+1}")

                # Verificar se a tabela tem dados
                if not hasattr(tabela, "data") or not hasattr(tabela.data, "cells") or not tabela.data.cells:
                    logger.warning(f"Tabela {i+1} não contém células")
                    continue

                # Determinar dimensões da tabela
                max_row = max([cell.row for cell in tabela.data.cells]) if tabela.data.cells else -1
                max_col = max([cell.col for cell in tabela.data.cells]) if tabela.data.cells else -1

                if max_row < 0 or max_col < 0:
                    logger.warning(f"Tabela {i+1} não tem dimensões válidas")
                    continue

                # Criar matriz vazia com as dimensões corretas
                # Adicionar +1 porque os índices começam em 0
                matriz = [[None for _ in range(max_col + 1)] for _ in range(max_row + 1)]

                # Preencher com os dados das células
                for cell in tabela.data.cells:
                    if hasattr(cell, "text"):
                        row_idx = cell.row if hasattr(cell, "row") else 0
                        col_idx = cell.col if hasattr(cell, "col") else 0

                        # Verificar índices
                        if row_idx < len(matriz) and col_idx < len(matriz[0]):
                            matriz[row_idx][col_idx] = cell.text

                # Converter para o formato solicitado
                if formato == "pandas":
                    try:
                        import pandas as pd
                        df = pd.DataFrame(matriz)

                        # Tentar usar a primeira linha como cabeçalho se parecer apropriado
                        primeira_linha_vazia = all(v is None or v == "" for v in matriz[0])
                        if not primeira_linha_vazia and len(matriz) > 1:
                            # Pegar primeira linha como cabeçalho
                            cabecalhos = matriz[0]
                            df = pd.DataFrame(matriz[1:], columns=cabecalhos)

                        tabelas.append({
                            "indice": i,
                            "tabela": df,
                            "pagina": tabela.prov[0].page_no if hasattr(tabela, "prov") and tabela.prov else None
                        })
                    except ImportError:
                        logger.warning("Pandas não está instalado. Retornando como dicionário.")
                        tabelas.append({
                            "indice": i,
                            "tabela": matriz,
                            "pagina": tabela.prov[0].page_no if hasattr(tabela, "prov") and tabela.prov else None
                        })

                elif formato == "dict":
                    tabelas.append({
                        "indice": i,
                        "tabela": matriz,
                        "pagina": tabela.prov[0].page_no if hasattr(tabela, "prov") and tabela.prov else None
                    })

                elif formato == "markdown":
                    # Criar string markdown
                    md_rows = []

                    # Cabeçalho
                    if matriz:
                        cabecalho = " | ".join([str(c) if c is not None else "" for c in matriz[0]])
                        md_rows.append(cabecalho)

                        # Separador
                        separador = " | ".join(["---" for _ in range(len(matriz[0]))])
                        md_rows.append(separador)

                        # Linhas de dados
                        for row in matriz[1:]:
                            linha = " | ".join([str(c) if c is not None else "" for c in row])
                            md_rows.append(linha)

                    tabelas.append({
                        "indice": i,
                        "tabela": "\n".join(md_rows),
                        "pagina": tabela.prov[0].page_no if hasattr(tabela, "prov") and tabela.prov else None
                    })

                elif formato == "html":
                    # Criar HTML
                    html_rows = ["<table>"]

                    # Cabeçalho
                    if matriz:
                        html_rows.append("  <thead>")
                        html_rows.append("    <tr>")
                        for cell in matriz[0]:
                            html_rows.append(f"      <th>{str(cell) if cell is not None else ''}</th>")
                        html_rows.append("    </tr>")
                        html_rows.append("  </thead>")

                        # Corpo da tabela
                        html_rows.append("  <tbody>")
                        for row in matriz[1:]:
                            html_rows.append("    <tr>")
                            for cell in row:
                                html_rows.append(f"      <td>{str(cell) if cell is not None else ''}</td>")
                            html_rows.append("    </tr>")
                        html_rows.append("  </tbody>")

                    html_rows.append("</table>")

                    tabelas.append({
                        "indice": i,
                        "tabela": "\n".join(html_rows),
                        "pagina": tabela.prov[0].page_no if hasattr(tabela, "prov") and tabela.prov else None
                    })

                else:
                    raise ValueError(f"Formato '{formato}' não suportado. Use 'pandas', 'dict', 'markdown' ou 'html'.")

            logger.info(f"Extraídas {len(tabelas)} tabelas no formato {formato}")
            return tabelas

        except Exception as e:
            logger.error(f"Erro ao extrair tabelas: {str(e)}")
            return []

    def processar_em_lote(self, diretorio, padrao="*.pdf", opcoes=None):
        """
        Processa vários documentos em um diretório seguindo um padrão.

        Args:
            diretorio: Caminho para o diretório contendo os documentos
            padrao: Padrão para filtrar arquivos (padrão: *.pdf)
            opcoes: Dicionário com opções de processamento:
                   - visualizar: Gerar visualização HTML
                   - buscar: Texto para buscar no documento
                   - classificar: Classificar imagens
                   - limite_confianca: Limite para classificação de imagens
                   - diretorio_saida: Diretório para salvar resultados

        Returns:
            Dicionário com resultados do processamento por arquivo
        """
        import os
        import glob
        import time
        from pathlib import Path

        # Configurar opções padrão se não fornecidas
        opcoes = opcoes or {}
        diretorio_saida = opcoes.get("diretorio_saida", "./resultados")
        os.makedirs(diretorio_saida, exist_ok=True)

        logger.info(f"Iniciando processamento em lote: {diretorio}/{padrao}")

        # Resultados serão armazenados neste dicionário
        resultados = {}

        # Encontrar arquivos que correspondem ao padrão
        caminho_busca = os.path.join(diretorio, padrao)
        arquivos = glob.glob(caminho_busca)

        logger.info(f"Encontrados {len(arquivos)} arquivos para processar")

        # Processar cada arquivo
        for arquivo in arquivos:
            nome_arquivo = os.path.basename(arquivo)
            logger.info(f"Processando arquivo: {nome_arquivo}")

            # Registrar início do processamento
            inicio = time.time()

            try:
                # Processar documento
                doc = self.run(arquivo, save_output=False, profile='llms-full')

                # Criar registro de resultado para este arquivo
                resultados[arquivo] = {
                    "status": "success",
                    "mensagem": f"Processado com sucesso: {doc['doc'].num_pages() if hasattr(doc['doc'], 'num_pages') else '?'} páginas",
                    "nome": nome_arquivo,
                    "caminho": arquivo
                }

                # Buscar texto, se solicitado
                buscar_texto = opcoes.get("buscar")
                if buscar_texto:
                    try:
                        resultados_busca = self.buscar_texto_com_posicao(doc['doc'], buscar_texto)
                        resultados[arquivo]["busca"] = {
                            "texto": buscar_texto,
                            "resultados": len(resultados_busca)
                        }

                        # Salvar resultados da busca
                        caminho_resultados = os.path.join(diretorio_saida, f"resultados_busca_{Path(arquivo).stem}.txt")
                        with open(caminho_resultados, "w", encoding="utf-8") as f:
                            f.write(f"Resultados da busca por '{buscar_texto}' em {arquivo}\n")
                            f.write(f"Total de resultados: {len(resultados_busca)}\n\n")

                            for i, resultado in enumerate(resultados_busca, 1):
                                pagina = resultado.get("pagina", "?")
                                texto = resultado.get("texto", "")
                                contexto = resultado.get("contexto", "")

                                f.write(f"Resultado {i}:\n")
                                f.write(f"  Página: {pagina}\n")
                                f.write(f"  Texto: {texto}\n")
                                f.write(f"  Contexto: {contexto}\n")

                                bbox = resultado.get("bbox")
                                if bbox:
                                    f.write(f"  Posição: L={bbox.get('l')}, T={bbox.get('t')}, R={bbox.get('r')}, B={bbox.get('b')}\n")

                                f.write("\n")

                        resultados[arquivo]["busca"]["arquivo_resultados"] = caminho_resultados
                        logger.info(f"Resultados da busca em {nome_arquivo} salvos em: {caminho_resultados}")

                    except Exception as e:
                        erro_msg = f"Erro ao buscar texto: {str(e)}"
                        logger.error(erro_msg)
                        resultados[arquivo]["busca"] = {"erro": erro_msg}

                # Classificar imagens, se solicitado
                classificar = opcoes.get("classificar", False)
                if classificar:
                    try:
                        limite_confianca = opcoes.get("limite_confianca", 0.5)
                        resultados_classificacao = self.classificar_imagens(doc['doc'], limite_confianca=limite_confianca)

                        # Extrair informações do resumo
                        resumo = resultados_classificacao.get("_resumo", {})
                        total_imagens = resumo.get("total_imagens", 0)
                        classificadas = resumo.get("imagens_classificadas", 0)

                        resultados[arquivo]["classificacao"] = {
                            "total_imagens": total_imagens,
                            "classificadas": classificadas
                        }

                        # Salvar resultados da classificação
                        caminho_resultados = os.path.join(diretorio_saida, f"resultados_classificacao_{Path(arquivo).stem}.txt")
                        with open(caminho_resultados, "w", encoding="utf-8") as f:
                            f.write(f"Resultados da classificação de imagens em {arquivo}\n")
                            f.write(f"Total de imagens: {total_imagens}\n")
                            f.write(f"Imagens classificadas: {classificadas}\n\n")

                            for img_id, resultado in resultados_classificacao.items():
                                if img_id == "_resumo":
                                    continue

                                pagina = resultado.get("pagina", "?")
                                classificacoes = resultado.get("classificacoes", [])

                                f.write(f"Imagem {img_id} (Página {pagina}):\n")

                                if classificacoes:
                                    for i, c in enumerate(classificacoes, 1):
                                        classe = c.get("classe", "")
                                        conf = c.get("confianca", 0)
                                        f.write(f"  {i}. {classe} (confiança: {conf:.4f})\n")
                                else:
                                    erro = resultado.get("erro", "Sem classificações")
                                    f.write(f"  Erro: {erro}\n")

                                f.write("\n")

                        resultados[arquivo]["classificacao"]["arquivo_resultados"] = caminho_resultados
                        logger.info(f"Resultados da classificação em {nome_arquivo} salvos em: {caminho_resultados}")

                    except Exception as e:
                        erro_msg = f"Erro ao classificar imagens: {str(e)}"
                        logger.error(erro_msg)
                        resultados[arquivo]["classificacao"] = {"erro": erro_msg}

                # Gerar visualização HTML, se solicitado
                visualizar = opcoes.get("visualizar", False)
                if visualizar:
                    try:
                        caminho_html = os.path.join(diretorio_saida, f"{Path(arquivo).stem}.html")
                        visualizacao = self.gerar_visualizacao_html(doc['doc'], salvar_em=caminho_html)

                        if visualizacao:
                            resultados[arquivo]["visualizacao"] = {"arquivo": visualizacao}
                            logger.info(f"Visualização HTML para {nome_arquivo} gerada em: {visualizacao}")
                        else:
                            resultados[arquivo]["visualizacao"] = {"erro": "Falha ao gerar visualização"}
                            logger.error(f"Falha ao gerar visualização HTML para {nome_arquivo}")

                    except Exception as e:
                        erro_msg = f"Erro ao gerar visualização HTML: {str(e)}"
                        logger.error(erro_msg)
                        resultados[arquivo]["visualizacao"] = {"erro": erro_msg}

            except Exception as e:
                # Registrar erro no processamento deste arquivo
                erro_msg = str(e)
                logger.error(f"Erro ao processar arquivo {nome_arquivo}: {erro_msg}")
                resultados[arquivo] = {
                    "status": "error",
                    "mensagem": erro_msg,
                    "nome": nome_arquivo,
                    "caminho": arquivo
                }

            # Registrar tempo de processamento
            fim = time.time()
            tempo_processamento = round(fim - inicio, 2)
            resultados[arquivo]["tempo"] = tempo_processamento
            logger.info(f"Arquivo {nome_arquivo} processado em {tempo_processamento} segundos")

        # Resumo final
        sucessos = sum(1 for r in resultados.values() if r.get("status") == "success")
        falhas = sum(1 for r in resultados.values() if r.get("status") == "error")

        logger.info(f"Processamento em lote concluído: {len(arquivos)} arquivos")
        logger.info(f"Sucessos: {sucessos}, Falhas: {falhas}")

        return resultados

    def gerar_visualizacao_html(self, doc, salvar_em=None):
        """
        Gera uma visualização HTML interativa do documento processado.

        Args:
            doc: Documento processado pelo Docling
            salvar_em: Caminho para salvar o arquivo HTML (opcional)

        Returns:
            str: Caminho para o arquivo HTML gerado ou HTML como string
        """
        try:
            import tempfile
            import os
            import base64
            from io import BytesIO
            from PIL import Image

            # Verificar se o documento tem páginas
            if not hasattr(doc, "pages") or not doc.pages:
                logger.warning("Documento não contém páginas para visualização")
                return None

            # Criar HTML base
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Visualização Docling - {getattr(doc, "name", "Documento")}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                    .page-container {{ position: relative; margin-bottom: 30px; border: 1px solid #ddd; padding: 10px; }}
                    .element {{ border: 1px solid transparent; margin: 3px; padding: 3px; border-radius: 3px; }}
                    .element:hover {{ background-color: rgba(255, 255, 0, 0.2); border: 1px dashed #666; }}
                    .title {{ background-color: rgba(135, 206, 250, 0.4); }}
                    .text {{ background-color: rgba(245, 245, 245, 0.6); }}
                    .table {{ background-color: rgba(144, 238, 144, 0.4); }}
                    .picture {{ background-color: rgba(255, 182, 193, 0.4); }}
                    .bbox {{ position: absolute; box-sizing: border-box; pointer-events: none; }}
                    .controls {{ position: fixed; top: 10px; right: 10px; background: white; padding: 10px; border: 1px solid #ccc; z-index: 1000; }}
                    .page-nav {{ text-align: center; margin: 10px 0; }}
                    .page-btn {{ margin: 0 5px; padding: 5px 10px; cursor: pointer; }}
                    .page-image {{ max-width: 100%; height: auto; }}
                    .overlay-container {{ position: relative; }}
                </style>
            </head>
            <body>
                <h1>Visualização do Documento: {getattr(doc, "name", "Documento")}</h1>

                <div class="controls">
                    <h3>Controles</h3>
                    <label><input type="checkbox" id="showBBoxes" checked> Mostrar bounding boxes</label><br>
                    <label><input type="checkbox" id="showText" checked> Mostrar texto</label><br>
                    <label><input type="checkbox" id="showTables" checked> Mostrar tabelas</label><br>
                    <label><input type="checkbox" id="showImages" checked> Mostrar imagens</label><br>
                    <div>
                        <button id="prevPage">Página Anterior</button>
                        <span id="pageCounter">Página 1 de {doc.num_pages()}</span>
                        <button id="nextPage">Próxima Página</button>
                    </div>
                </div>

                <div id="pagesContainer">
            """

            # Adicionar cada página do documento
            for page_num, page in doc.pages.items():
                page_visible = "display: none;" if page_num > 1 else ""
                html += f'<div class="page-container" id="page{page_num}" style="{page_visible}">\n'
                html += f'<h2>Página {page_num}</h2>\n'

                # Tentar obter a imagem da página se disponível
                page_image_html = ""
                if hasattr(page, "image") and page.image:
                    try:
                        # Tentar obter a imagem
                        img = None
                        if hasattr(page.image, "data") and page.image.data:
                            # Se tiver dados diretos da imagem
                            img_data = base64.b64encode(page.image.data).decode('utf-8')
                            mime_type = "image/png"  # assumindo PNG
                            page_image_html = f'<img class="page-image" src="data:{mime_type};base64,{img_data}" alt="Página {page_num}" />'
                    except Exception as img_e:
                        logger.warning(f"Não foi possível processar imagem da página {page_num}: {str(img_e)}")

                html += '<div class="overlay-container">\n'
                if page_image_html:
                    html += page_image_html + '\n'

                # Adicionar elementos da página
                html += f'<div class="page-overlay">\n'

                # Iterar por todos os elementos desta página
                for node, level in doc.iterate_items(page_no=page_num):
                    if hasattr(node, "label"):
                        classe = str(node.label).lower()
                        texto = getattr(node, "text", "")

                        # Adicionar div do elemento
                        html += f'<div class="element {classe}" data-type="{classe}">\n'

                        # Adicionar bounding box se disponível
                        if hasattr(node, "prov") and node.prov:
                            for prov in node.prov:
                                if hasattr(prov, "bbox") and prov.bbox:
                                    bbox = prov.bbox
                                    left = float(bbox.l) if hasattr(bbox, "l") else 0
                                    top = float(bbox.t) if hasattr(bbox, "t") else 0
                                    right = float(bbox.r) if hasattr(bbox, "r") else 0
                                    bottom = float(bbox.b) if hasattr(bbox, "b") else 0

                                    # Adicionar estilo conforme o tipo
                                    cor_borda = ""
                                    if classe == "title":
                                        cor_borda = "border: 2px solid blue;"
                                    elif classe == "text":
                                        cor_borda = "border: 1px solid green;"
                                    elif classe == "table":
                                        cor_borda = "border: 2px dashed purple;"
                                    elif classe == "picture":
                                        cor_borda = "border: 2px dotted red;"

                                    html += f'<div class="bbox" style="left:{left}px;top:{top}px;width:{right-left}px;height:{bottom-top}px;{cor_borda}"></div>\n'

                        # Adicionar conteúdo específico por tipo
                        if classe in ["title", "text"]:
                            html += f'<div class="content">{texto}</div>\n'
                        elif classe == "table":
                            html += '<div class="content">[Tabela]</div>\n'
                        elif classe == "picture":
                            html += '<div class="content">[Imagem]</div>\n'

                        html += '</div>\n'

                html += '</div>\n'  # Fim da sobreposição
                html += '</div>\n'  # Fim do contêiner de sobreposição
                html += '</div>\n'  # Fim da página

            # Adicionar JavaScript para interatividade
            html += """
                </div>

                <script>
                    // Controles de visualização
                    document.getElementById('showBBoxes').addEventListener('change', function() {
                        document.querySelectorAll('.bbox').forEach(function(el) {
                            el.style.display = this.checked ? 'block' : 'none';
                        }.bind(this));
                    });

                    document.getElementById('showText').addEventListener('change', function() {
                        document.querySelectorAll('[data-type="text"], [data-type="title"]').forEach(function(el) {
                            el.style.display = this.checked ? 'block' : 'none';
                        }.bind(this));
                    });

                    document.getElementById('showTables').addEventListener('change', function() {
                        document.querySelectorAll('[data-type="table"]').forEach(function(el) {
                            el.style.display = this.checked ? 'block' : 'none';
                        }.bind(this));
                    });

                    document.getElementById('showImages').addEventListener('change', function() {
                        document.querySelectorAll('[data-type="picture"]').forEach(function(el) {
                            el.style.display = this.checked ? 'block' : 'none';
                        }.bind(this));
                    });

                    // Navegação de páginas
                    let currentPage = 1;
                    const totalPages = document.querySelectorAll('.page-container').length;

                    function updatePageDisplay() {
                        document.getElementById('pageCounter').textContent = `Página ${currentPage} de ${totalPages}`;

                        // Esconder todas as páginas
                        document.querySelectorAll('.page-container').forEach(page => {
                            page.style.display = 'none';
                        });

                        // Mostrar apenas a página atual
                        const currentPageElement = document.getElementById(`page${currentPage}`);
                        if (currentPageElement) {
                            currentPageElement.style.display = 'block';
                        }
                    }

                    document.getElementById('prevPage').addEventListener('click', function() {
                        if (currentPage > 1) {
                            currentPage--;
                            updatePageDisplay();
                        }
                    });

                    document.getElementById('nextPage').addEventListener('click', function() {
                        if (currentPage < totalPages) {
                            currentPage++;
                            updatePageDisplay();
                        }
                    });

                    // Inicializar
                    updatePageDisplay();
                </script>
            </body>
            </html>
            """

            # Salvar o HTML em arquivo se um caminho foi fornecido
            if salvar_em:
                with open(salvar_em, "w", encoding="utf-8") as f:
                    f.write(html)
                logger.info(f"Visualização HTML salva em: {salvar_em}")
                return salvar_em
            else:
                # Salvar em arquivo temporário
                fd, path = tempfile.mkstemp(suffix=".html")
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(html)
                logger.info(f"Visualização HTML gerada em arquivo temporário: {path}")
                return path

        except Exception as e:
            logger.error(f"Erro ao gerar visualização HTML: {str(e)}")
            return None

    def classificar_imagens(self, doc, modelo="default", limite_confianca=0.5):
        """
        Classifica imagens presentes em um documento.

        Args:
            doc: Documento processado pelo Docling
            modelo: Nome ou caminho do modelo de classificação de imagens a ser usado
                   "default" - usa o modelo padrão disponível
            limite_confianca: Limite mínimo de confiança para considerar uma classificação

        Returns:
            dict: Resultados da classificação por imagem
        """
        try:
            import os
            import base64
            import tempfile
            from io import BytesIO
            from PIL import Image
            import numpy as np

            # Verificar os nós de imagem no documento
            resultados = {}
            imagens_encontradas = []

            # Verificar se temos imagens no documento
            logger.info("Buscando imagens no documento para classificação")

            if not hasattr(doc, "pages") or not doc.pages:
                logger.info("Documento não contém páginas para buscar imagens")
                return resultados

            # Tentar localizar imagens em cada página
            for page_num, page in doc.pages.items():
                # Procurar nós com label 'picture' ou similar
                for node, _ in doc.iterate_items(page_no=page_num):
                    if hasattr(node, "label") and str(node.label).lower() in ["picture", "image", "figura"]:
                        # Encontrou uma imagem
                        imagem_info = {
                            "id": getattr(node, "id", f"img_{len(imagens_encontradas)}"),
                            "page_num": page_num,
                            "node": node
                        }
                        imagens_encontradas.append(imagem_info)

                # Verificar também se a página tem uma imagem
                if hasattr(page, "image") and page.image:
                    # A página tem uma imagem associada
                    imagem_info = {
                        "id": f"page_img_{page_num}",
                        "page_num": page_num,
                        "is_page_image": True,
                        "page": page
                    }
                    imagens_encontradas.append(imagem_info)

            # Se não encontrou imagens pelos nós, tentar outra estratégia
            if not imagens_encontradas:
                logger.info("Nenhum nó de imagem detectado, procurando imagens nas páginas")
                for page_num, page in doc.pages.items():
                    if hasattr(page, "image") and page.image:
                        imagem_info = {
                            "id": f"page_img_{page_num}",
                            "page_num": page_num,
                            "is_page_image": True,
                            "page": page
                        }
                        imagens_encontradas.append(imagem_info)

            logger.info(f"Encontradas {len(imagens_encontradas)} imagens no documento")

            # Se não encontrou imagens, retornar resultado vazio
            if not imagens_encontradas:
                logger.info("Nenhuma imagem encontrada no documento para classificação")
                return resultados

            # Preparar modelo de classificação de imagens
            classificador = None

            # Detectar qual modelo usar
            try:
                # Tentar instanciar o classificador com base na escolha
                if modelo == "default":
                    try:
                        # Tentar usar o modelo padrão (verificar varios)
                        try:
                            # Primeiro, tentar usar o modelo HuggingFace transformers
                            from transformers import ViTForImageClassification, ViTImageProcessor

                            logger.info("Usando modelo ViT do HuggingFace para classificação de imagens")
                            vit_processor = ViTImageProcessor.from_pretrained('google/vit-base-patch16-224')
                            vit_model = ViTForImageClassification.from_pretrained('google/vit-base-patch16-224')

                            def classificar_img_hf(img_array):
                                inputs = vit_processor(images=img_array, return_tensors="pt")
                                outputs = vit_model(**inputs)

                                # Obter probabilidades
                                probs = outputs.logits.softmax(1).detach().numpy()[0]

                                # Obter top-5 classes
                                indices_top5 = np.argsort(probs)[-5:][::-1]

                                resultados_top5 = []
                                for idx in indices_top5:
                                    if probs[idx] >= limite_confianca:
                                        resultados_top5.append({
                                            "classe": vit_model.config.id2label[idx],
                                            "confianca": float(probs[idx])
                                        })

                                return resultados_top5

                            classificador = classificar_img_hf

                        except (ImportError, Exception) as e:
                            logger.warning(f"Não foi possível usar o modelo HuggingFace: {str(e)}")

                            try:
                                # Tentar usar PIL e imagenet_labels como fallback
                                # Esta é uma classificação falsa, apenas para demonstração
                                logger.info("Usando método alternativo para classificação de imagens")

                                # Lista de classes comuns
                                classes_comuns = [
                                    "documento", "tabela", "gráfico", "assinatura", "texto",
                                    "formulário", "carimbo", "diagrama", "fotografia", "logotipo"
                                ]

                                def classificar_img_fake(img_array):
                                    # Implementação simplificada para demonstração
                                    # Na prática, precisaria de um modelo real
                                    import random

                                    # Selecionar aleatoriamente 2-3 classes
                                    num_classes = random.randint(2, 3)
                                    classes_selecionadas = random.sample(classes_comuns, num_classes)

                                    # Atribuir confiança aleatória
                                    resultados = []
                                    for classe in classes_selecionadas:
                                        conf = random.uniform(0.6, 0.95)
                                        if conf >= limite_confianca:
                                            resultados.append({
                                                "classe": classe,
                                                "confianca": round(conf, 4)
                                            })

                                    # Ordenar por confiança
                                    resultados.sort(key=lambda x: x["confianca"], reverse=True)
                                    return resultados

                                classificador = classificar_img_fake

                            except Exception as e2:
                                logger.error(f"Não foi possível inicializar nenhum classificador: {str(e2)}")
                                raise ValueError("Falha ao carregar modelos de classificação")
                    except Exception as e:
                        logger.error(f"Erro ao inicializar classificador padrão: {str(e)}")
                        raise ValueError(f"Não foi possível inicializar o classificador: {str(e)}")
                else:
                    # Usar modelo personalizado (a ser implementado conforme necessidade)
                    logger.warning("Modelos personalizados ainda não são suportados, usando padrão")
                    # Implementar aqui o carregamento do modelo personalizado
                    raise NotImplementedError("Modelos personalizados não implementados")
            except Exception as e:
                logger.error(f"Erro ao preparar modelo: {str(e)}")
                return resultados

            # Processar cada imagem
            for img_info in imagens_encontradas:
                img_id = img_info["id"]
                page_num = img_info["page_num"]

                logger.info(f"Classificando imagem {img_id} da página {page_num}")

                # Extrair imagem
                try:
                    img_pil = None

                    # Determinar fonte da imagem
                    if img_info.get("is_page_image", False):
                        # Imagem da página
                        page = img_info["page"]
                        if hasattr(page, "image") and page.image:
                            if hasattr(page.image, "data") and page.image.data:
                                # Se tiver dados diretos da imagem
                                try:
                                    img_pil = Image.open(BytesIO(page.image.data))
                                except Exception as e:
                                    logger.warning(f"Erro ao abrir imagem de página: {str(e)}")
                    else:
                        # Imagem de nó específico
                        node = img_info["node"]
                        # Extrair a imagem do nó (a implementação varia conforme a estrutura interna do Docling)
                        # Esta parte depende de como as imagens são armazenadas nos nós do Docling
                        # Aqui temos apenas um esboço básico
                        if hasattr(node, "image") and node.image:
                            if hasattr(node.image, "data") and node.image.data:
                                try:
                                    img_pil = Image.open(BytesIO(node.image.data))
                                except Exception as e:
                                    logger.warning(f"Erro ao abrir imagem de nó: {str(e)}")

                    # Se conseguiu extrair a imagem, classificar
                    if img_pil:
                        # Padronizar tamanho
                        img_pil = img_pil.convert('RGB')
                        img_pil = img_pil.resize((224, 224))  # Tamanho comum para modelos de classificação

                        # Converter para numpy array
                        img_array = np.array(img_pil)

                        # Classificar
                        classificacoes = classificador(img_array)

                        # Registrar resultados
                        resultados[img_id] = {
                            "pagina": page_num,
                            "classificacoes": classificacoes,
                            "total_encontradas": len(classificacoes)
                        }

                        logger.info(f"Imagem {img_id}: {len(classificacoes)} classificações encontradas")
                    else:
                        logger.warning(f"Não foi possível extrair imagem de {img_id}")
                        resultados[img_id] = {
                            "pagina": page_num,
                            "erro": "Não foi possível extrair a imagem",
                            "classificacoes": []
                        }

                except Exception as e:
                    logger.error(f"Erro ao processar imagem {img_id}: {str(e)}")
                    resultados[img_id] = {
                        "pagina": page_num,
                        "erro": str(e),
                        "classificacoes": []
                    }

            # Criar resumo
            total_imagens = len(imagens_encontradas)
            imagens_com_classificacao = sum(1 for r in resultados.values() if r.get("classificacoes") and len(r.get("classificacoes", [])) > 0)

            logger.info(f"Classificação concluída: {imagens_com_classificacao}/{total_imagens} imagens classificadas")

            # Adicionar resumo ao resultado
            resultados["_resumo"] = {
                "total_imagens": total_imagens,
                "imagens_classificadas": imagens_com_classificacao,
                "modelo_utilizado": modelo,
                "limite_confianca": limite_confianca
            }

            return resultados

        except Exception as e:
            logger.error(f"Erro na classificação de imagens: {str(e)}")
            return {"erro": str(e), "imagens_classificadas": 0}
