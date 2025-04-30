#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Exemplo de análise de documentos utilizando a ferramenta de extração e processamento de texto.
Este script demonstra como processar documentos (PDF, DOCX, etc.), buscar texto com posicionamento
e classificar imagens encontradas no documento.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("document-analysis")

def main():
    """Função principal do script de análise de documentos"""
    
    # Configuração dos argumentos de linha de comando
    parser = argparse.ArgumentParser(description="Ferramenta para análise de documentos")
    
    grupo_entrada = parser.add_mutually_exclusive_group(required=True)
    grupo_entrada.add_argument("-d", "--documento", help="Caminho para o documento a ser analisado")
    grupo_entrada.add_argument("-dir", "--diretorio", help="Diretório para processamento em lote de documentos")
    
    parser.add_argument("-p", "--padrao", default="*.pdf", help="Padrão de arquivos para processamento em lote (padrão: *.pdf)")
    parser.add_argument("-v", "--visualizar", action="store_true", help="Gerar visualização HTML do documento")
    parser.add_argument("-b", "--buscar", help="Texto a ser buscado no documento")
    parser.add_argument("-c", "--classificar", action="store_true", help="Classificar imagens no documento")
    parser.add_argument("-s", "--saida", default="./resultados", help="Diretório para salvar resultados")
    parser.add_argument("-l", "--limite", type=float, default=0.5, help="Limite de confiança para classificação de imagens (0-1)")
    
    args = parser.parse_args()
    
    # Criar diretório de saída se não existir
    os.makedirs(args.saida, exist_ok=True)
    
    # Importar a classe DocumentConverter
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
        from src.tools.document_converter import DocumentConverter
    except ImportError as e:
        logger.error(f"Erro ao importar módulos necessários: {e}")
        logger.error("Verifique se os pacotes requeridos estão instalados")
        sys.exit(1)
    
    try:
        # Inicializar o conversor de documentos
        conversor = DocumentConverter()
        
        # Configurar opções de processamento
        opcoes = {
            "visualizar": args.visualizar,
            "buscar": args.buscar,
            "classificar": args.classificar,
            "limite_confianca": args.limite,
            "diretorio_saida": args.saida
        }
        
        # Processar documento único ou diretório em lote
        if args.documento:
            # Processar um único documento
            logger.info(f"Processando documento único: {args.documento}")
            
            try:
                # Processar o documento
                resultado_doc = conversor.processar_documento(args.documento)
                
                # Processar operações solicitadas
                
                # Buscar texto
                if args.buscar:
                    logger.info(f"Buscando texto '{args.buscar}' no documento")
                    resultados_busca = conversor.buscar_texto_com_posicao(resultado_doc, args.buscar)
                    
                    # Salvar resultados da busca em arquivo de texto
                    arquivo_resultados = os.path.join(args.saida, f"resultados_busca_{Path(args.documento).stem}.txt")
                    with open(arquivo_resultados, "w", encoding="utf-8") as f:
                        f.write(f"Resultados da busca por '{args.buscar}' em {args.documento}\n")
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
                    
                    logger.info(f"Resultados da busca salvos em: {arquivo_resultados}")
                
                # Classificar imagens
                if args.classificar:
                    logger.info("Classificando imagens no documento")
                    resultados_classificacao = conversor.classificar_imagens(resultado_doc, limite_confianca=args.limite)
                    
                    # Extrair informações do resumo
                    resumo = resultados_classificacao.get("_resumo", {})
                    total_imagens = resumo.get("total_imagens", 0)
                    classificadas = resumo.get("imagens_classificadas", 0)
                    
                    # Salvar resultados da classificação em arquivo de texto
                    arquivo_resultados = os.path.join(args.saida, f"resultados_classificacao_{Path(args.documento).stem}.txt")
                    with open(arquivo_resultados, "w", encoding="utf-8") as f:
                        f.write(f"Resultados da classificação de imagens em {args.documento}\n")
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
                    
                    logger.info(f"Resultados da classificação salvos em: {arquivo_resultados}")
                
                # Gerar visualização HTML
                if args.visualizar:
                    logger.info("Gerando visualização HTML do documento")
                    caminho_html = os.path.join(args.saida, f"{Path(args.documento).stem}.html")
                    visualizacao = conversor.gerar_visualizacao_html(resultado_doc, salvar_em=caminho_html)
                    
                    if visualizacao:
                        logger.info(f"Visualização HTML gerada em: {visualizacao}")
                    else:
                        logger.error("Falha ao gerar visualização HTML")
                
                logger.info("Processamento concluído com sucesso")
                
            except Exception as e:
                logger.error(f"Erro ao processar documento: {e}")
                sys.exit(1)
                
        else:
            # Processar documentos em lote de um diretório
            logger.info(f"Processando diretório: {args.diretorio}")
            
            if not os.path.exists(args.diretorio):
                logger.error(f"Diretório não encontrado: {args.diretorio}")
                sys.exit(1)
            
            # Processar documentos em lote usando o método processar_em_lote
            try:
                resultados = conversor.processar_em_lote(
                    diretorio=args.diretorio,
                    padrao=args.padrao,
                    opcoes=opcoes
                )
                
                # Salvar resumo do processamento em lote
                arquivo_resumo = os.path.join(args.saida, "resumo_processamento.txt")
                with open(arquivo_resumo, "w", encoding="utf-8") as f:
                    f.write(f"Resumo do processamento em lote\n")
                    f.write(f"Diretório: {args.diretorio}\n")
                    f.write(f"Padrão: {args.padrao}\n")
                    f.write(f"Total de arquivos processados: {len(resultados)}\n")
                    
                    # Contador de sucessos e falhas
                    sucessos = sum(1 for r in resultados.values() if r.get("status") == "success")
                    falhas = sum(1 for r in resultados.values() if r.get("status") == "error")
                    
                    f.write(f"Sucessos: {sucessos}\n")
                    f.write(f"Falhas: {falhas}\n\n")
                    
                    # Detalhes por arquivo
                    f.write("Detalhes por arquivo:\n")
                    for arquivo, resultado in resultados.items():
                        nome = resultado.get("nome", os.path.basename(arquivo))
                        status = resultado.get("status", "desconhecido")
                        mensagem = resultado.get("mensagem", "")
                        tempo = resultado.get("tempo", 0)
                        
                        f.write(f"\n{nome}:\n")
                        f.write(f"  Status: {status}\n")
                        f.write(f"  Tempo de processamento: {tempo} segundos\n")
                        
                        if status == "error":
                            f.write(f"  Erro: {mensagem}\n")
                        else:
                            f.write(f"  Mensagem: {mensagem}\n")
                            
                            # Adicionar detalhes da busca
                            if "busca" in resultado:
                                busca = resultado["busca"]
                                f.write(f"  Busca por '{busca.get('texto', '')}':\n")
                                f.write(f"    Resultados: {busca.get('resultados', 0)}\n")
                                
                                arquivo_resultados = busca.get("arquivo_resultados")
                                if arquivo_resultados:
                                    f.write(f"    Detalhes em: {os.path.basename(arquivo_resultados)}\n")
                            
                            # Adicionar detalhes da classificação
                            if "classificacao" in resultado:
                                classificacao = resultado["classificacao"]
                                f.write(f"  Classificação de imagens:\n")
                                f.write(f"    Total de imagens: {classificacao.get('total_imagens', 0)}\n")
                                f.write(f"    Imagens classificadas: {classificacao.get('classificadas', 0)}\n")
                                
                                arquivo_resultados = classificacao.get("arquivo_resultados")
                                if arquivo_resultados:
                                    f.write(f"    Detalhes em: {os.path.basename(arquivo_resultados)}\n")
                            
                            # Adicionar detalhes da visualização
                            if "visualizacao" in resultado:
                                visualizacao = resultado["visualizacao"]
                                arquivo_html = visualizacao.get("arquivo")
                                if arquivo_html:
                                    f.write(f"  Visualização HTML: {os.path.basename(arquivo_html)}\n")
                
                logger.info(f"Resumo do processamento em lote salvo em: {arquivo_resumo}")
                logger.info(f"Processamento em lote concluído: {sucessos} sucessos, {falhas} falhas")
                
            except Exception as e:
                logger.error(f"Erro no processamento em lote: {e}")
                sys.exit(1)
    
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 