#!/usr/bin/env python3
"""
Script para criar um PDF de exemplo para testes.
"""

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.units import inch
except ImportError:
    print("Instalando reportlab...")
    import os
    os.system("pip install reportlab")
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.units import inch

import os

def create_sample_pdf():
    # Garantir que o diretório existe
    os.makedirs("data/test_files", exist_ok=True)
    
    # Caminho do arquivo
    pdf_path = "data/test_files/exemplo.pdf"
    
    # Criar o PDF
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        title="Exemplo PDF para Teste",
        author="Anything to LLMs.txt"
    )
    
    # Conteúdo
    styles = getSampleStyleSheet()
    story = []
    
    # Título
    story.append(Paragraph("Documento de Exemplo para Teste", styles['Title']))
    story.append(Spacer(1, 0.5*inch))
    
    # Introdução
    intro_text = """Este é um documento PDF de exemplo criado para testar a ferramenta 'Anything to LLMs.txt'. 
    O objetivo é converter este PDF em um formato textual que possa ser processado por modelos de linguagem."""
    story.append(Paragraph(intro_text, styles['Normal']))
    story.append(Spacer(1, 0.25*inch))
    
    # Seção 1
    story.append(Paragraph("1. Sobre o Projeto", styles['Heading2']))
    section1_text = """O projeto 'Anything to LLMs.txt' visa facilitar a integração de diferentes fontes de dados com 
    modelos de linguagem. O sistema extrai texto de diversos formatos (PDF, DOCX, HTML, etc.) e o transforma em um 
    formato adequado para uso com LLMs via LangChain."""
    story.append(Paragraph(section1_text, styles['Normal']))
    story.append(Spacer(1, 0.25*inch))
    
    # Seção 2
    story.append(Paragraph("2. Benefícios", styles['Heading2']))
    section2_text = """- Processamento unificado de várias fontes de dados
    - Extração inteligente mantendo a estrutura semântica
    - Integração direta com bibliotecas de LLMs
    - Fluxo de trabalho simplificado para análise de documentos"""
    story.append(Paragraph(section2_text, styles['Normal']))
    story.append(Spacer(1, 0.25*inch))
    
    # Seção 3
    story.append(Paragraph("3. Exemplos de Uso", styles['Heading2']))
    section3_text = """Um caso de uso comum é a análise de documentação técnica. Por exemplo, manuais de produtos, 
    especificações técnicas ou documentos legais podem ser processados e disponibilizados para consulta via interface 
    de linguagem natural. Outro caso de uso é a consolidação de múltiplas fontes de informação para criar uma base de 
    conhecimento coerente."""
    story.append(Paragraph(section3_text, styles['Normal']))
    story.append(Spacer(1, 0.25*inch))
    
    # Conclusão
    story.append(Paragraph("Conclusão", styles['Heading2']))
    conclusion_text = """Este documento de exemplo demonstra o tipo de estrutura que o sistema 'Anything to LLMs.txt' 
    deve ser capaz de processar, mantendo a hierarquia de títulos, parágrafos e listas."""
    story.append(Paragraph(conclusion_text, styles['Normal']))
    
    # Construir o PDF
    doc.build(story)
    
    print(f"PDF de exemplo criado em: {pdf_path}")

if __name__ == "__main__":
    create_sample_pdf() 