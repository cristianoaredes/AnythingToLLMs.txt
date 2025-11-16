#!/usr/bin/env python3
"""
CLI para Anything to LLMs.txt.

Conversão simples de documentos via linha de comando.
"""

import argparse
import sys
import os
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.document_converter import DocumentConverterTool
from src.config import DEFAULT_OCR_ENGINE, DEFAULT_OCR_LANGUAGE


def main():
    """Ponto de entrada do CLI."""
    parser = argparse.ArgumentParser(
        description="Converte documentos para formato LLMs.txt",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python -m src.main --file documento.pdf
  python -m src.main --file documento.pdf --profile llms-min
  python -m src.main --file documento.pdf --output resultado.txt
  python -m src.main --file documento.pdf --ocr-engine tesseract --ocr-language eng
        """
    )

    # Argumentos obrigatórios
    parser.add_argument(
        '--file', '-f',
        type=str,
        required=True,
        help='Caminho para o arquivo a ser convertido'
    )

    # Argumentos opcionais
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Caminho para salvar o arquivo de saída (padrão: <arquivo>_llms.txt)'
    )

    parser.add_argument(
        '--profile', '-p',
        type=str,
        choices=['llms-min', 'llms-ctx', 'llms-tables', 'llms-images', 'llms-raw', 'llms-full'],
        default='llms-full',
        help='Perfil de formatação (padrão: llms-full)'
    )

    parser.add_argument(
        '--ocr-engine',
        type=str,
        choices=['auto', 'tesseract', 'easyocr', 'rapidocr', 'mac'],
        default=DEFAULT_OCR_ENGINE,
        help=f'Engine OCR a usar (padrão: {DEFAULT_OCR_ENGINE})'
    )

    parser.add_argument(
        '--ocr-language',
        type=str,
        default=DEFAULT_OCR_LANGUAGE,
        help=f'Idioma para OCR (padrão: {DEFAULT_OCR_LANGUAGE})'
    )

    parser.add_argument(
        '--force-ocr',
        action='store_true',
        help='Forçar OCR mesmo para PDFs com texto'
    )

    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Não salvar arquivo de saída (apenas exibir no terminal)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Modo verboso (mostra mais detalhes)'
    )

    # Parse dos argumentos
    args = parser.parse_args()

    # Validar arquivo de entrada
    if not os.path.exists(args.file):
        print(f"L Erro: Arquivo '{args.file}' não encontrado", file=sys.stderr)
        sys.exit(1)

    # Determinar arquivo de saída
    if args.output:
        output_path = args.output
    else:
        # Gerar nome baseado no arquivo de entrada
        input_path = Path(args.file)
        output_path = str(input_path.parent / f"{input_path.stem}_llms.txt")

    # Executar conversão
    try:
        if args.verbose:
            print(f"=Ä Arquivo de entrada: {args.file}")
            print(f"=Ë Perfil: {args.profile}")
            print(f"= OCR Engine: {args.ocr_engine}")
            print(f"< Idioma OCR: {args.ocr_language}")
            print(f"™  Forçar OCR: {'Sim' if args.force_ocr else 'Não'}")
            print()
            print("= Processando...")

        # Inicializar conversor
        converter = DocumentConverterTool()

        # Executar conversão
        resultado = converter.run(
            file_path=args.file,
            save_output=not args.no_save,
            profile=args.profile,
            ocr_engine=args.ocr_engine,
            ocr_language=args.ocr_language,
            force_ocr=args.force_ocr,
            export_formats=['llms']
        )

        # Obter conteúdo formatado
        if 'formats' in resultado and 'llms' in resultado['formats']:
            content = resultado['formats']['llms']

            # Salvar ou exibir
            if not args.no_save:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f" Conversão concluída!")
                print(f"=Á Arquivo salvo em: {output_path}")
            else:
                print(content)

            # Mostrar estatísticas se verbose
            if args.verbose:
                print()
                print("=Ê Estatísticas:")
                print(f"   Tamanho: {len(content)} caracteres")
                if 'doc' in resultado:
                    doc = resultado['doc']
                    if hasattr(doc, 'pages'):
                        print(f"   Páginas: {len(doc.pages)}")

        else:
            print("L Erro: Formato 'llms' não encontrado no resultado", file=sys.stderr)
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"L Erro: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"L Erro: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"L Erro inesperado: {str(e)}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
