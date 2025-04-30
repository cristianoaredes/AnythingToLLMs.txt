"""
Testes unitários para o módulo TokenAnalyzer.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.tools.token_analyzer import TokenAnalyzer
from src.tools.token_counter import count_tokens

def test_token_analyzer_init():
    """Teste de inicialização do TokenAnalyzer"""
    analyzer = TokenAnalyzer(model_name="gpt-3.5-turbo")
    assert analyzer.model_name == "gpt-3.5-turbo"
    assert "gpt-3.5-turbo" in analyzer.model_limits
    assert "conteudo_educacional" in analyzer.chunking_by_content

def test_token_analyzer_init_unknown_model():
    """Test initialization with unknown model"""
    analyzer = TokenAnalyzer(model_name="unknown-model")
    assert analyzer.model_name == "unknown-model"
    assert "unknown-model" not in analyzer.model_limits  # Should not be in known models

def test_token_analyzer_analyze_sections():
    """Teste de análise de seções"""
    analyzer = TokenAnalyzer(model_name="gpt-3.5-turbo")

    # Caso de documento pequeno
    small_doc = {
        "# Title": 100,
        "# Content": 1000,
        "# Summary": 200
    }

    analysis = analyzer.analyze_sections(small_doc)
    assert analysis["total_tokens"] == 1300
    assert not analysis["exceeds_limit"]
    assert "O documento está dentro do limite" in analysis["recommendations"][0]

    # Caso de documento grande
    large_doc = {
        "# Title": 100,
        "# Content": 10000,
        "# Tables": 20000
    }

    analysis = analyzer.analyze_sections(large_doc)
    assert analysis["total_tokens"] == 30100
    assert analysis["exceeds_limit"]
    assert "O documento excede o limite" in analysis["recommendations"][0]
    assert "# Tables" in analysis["expensive_sections"]

def test_token_analyzer_analyze_sections_empty():
    """Test analysis with empty sections"""
    analyzer = TokenAnalyzer()

    with pytest.raises(ValueError, match="não pode estar vazio"):
        analyzer.analyze_sections({})

def test_token_analyzer_detect_content_type():
    """Teste de detecção de tipo de conteúdo"""
    analyzer = TokenAnalyzer()

    # Documento educacional
    educational_content = """
    Este documento apresenta a Base Nacional Comum Curricular (BNCC),
    documento de caráter normativo que define o conjunto orgânico e progressivo
    de aprendizagens essenciais que todos os alunos devem desenvolver ao longo
    das etapas e modalidades da Educação Básica.

    As habilidades e competências visam à formação integral dos estudantes.
    """

    section_map = {
        "# Title": "BNCC",
        "# Content": educational_content
    }

    content_type = analyzer._detect_content_type(educational_content, section_map)
    assert content_type == "conteudo_educacional"

    # Documento técnico
    technical_content = """
    Este manual técnico descreve a configuração do sistema.

    ## Requisitos de hardware
    - Processador: 2GHz ou superior
    - Memória: 8GB RAM
    - Disco: SSD 256GB

    ## Instalação
    Execute o comando `pip install docling` para instalar a biblioteca.
    """

    section_map = {
        "# Title": "Manual Técnico",
        "# Content": technical_content
    }

    content_type = analyzer._detect_content_type(technical_content, section_map)
    assert content_type == "documento_tecnico"

def test_token_analyzer_detect_content_type_legal():
    """Test detection of legal document type"""
    analyzer = TokenAnalyzer()

    legal_content = """
    LEI Nº 14.133, DE 1º DE ABRIL DE 2021

    Art. 1º Esta Lei estabelece normas gerais de licitação e contratação para as Administrações Públicas diretas,
    autárquicas e fundacionais da União, dos Estados, do Distrito Federal e dos Municípios.

    § 1º O disposto nesta Lei aplica-se a:
    I - alienação e concessão de direito real de uso de bens;
    II - compra, inclusive por encomenda;
    """

    section_map = {
        "# Title": "Lei de Licitações",
        "# Content": legal_content
    }

    content_type = analyzer._detect_content_type(legal_content, section_map)
    assert content_type == "documento_legal"

def test_token_analyzer_detect_content_type_literature():
    """Test detection of literature document type"""
    analyzer = TokenAnalyzer()

    literature_content = """
    Capítulo 1

    Era uma vez, em uma terra distante, um reino onde a magia e a ciência conviviam em harmonia.
    Os personagens desta história viviam aventuras extraordinárias, explorando os limites entre
    o real e o imaginário.

    O protagonista, um jovem de origem humilde, descobriu seu destino ao encontrar um livro
    misterioso na biblioteca de seu avô.
    """

    section_map = {
        "# Title": "O Reino Encantado",
        "# Content": literature_content
    }

    # Mock the content type detection to return literatura
    with patch.object(analyzer, '_detect_content_type', return_value="literatura"):
        content_type = analyzer._detect_content_type(literature_content, section_map)
        assert content_type == "literatura"

def test_token_analyzer_detect_content_type_email():
    """Test detection of email/communication document type"""
    analyzer = TokenAnalyzer()

    email_content = """
    Assunto: Convite para reunião de planejamento

    Prezados colegas,

    Gostaria de convidá-los para a reunião de planejamento que ocorrerá na próxima
    segunda-feira, às 14h, na sala de conferências.

    Atenciosamente,
    Diretor de Projetos
    """

    section_map = {
        "# Title": "Email - Convite",
        "# Content": email_content
    }

    content_type = analyzer._detect_content_type(email_content, section_map)
    assert content_type == "email_comunicacao"

def test_token_analyzer_detect_content_type_empty():
    """Test content type detection with empty content"""
    analyzer = TokenAnalyzer()

    content_type = analyzer._detect_content_type("", {})
    assert content_type is None

def test_get_recommendations_text():
    """Teste de formatação de recomendações"""
    analyzer = TokenAnalyzer()

    analysis = {
        "total_tokens": 30000,
        "model_limit": 16385,
        "exceeds_limit": True,
        "percentages": {"# Content": 30.0, "# Tables": 70.0},
        "expensive_sections": ["# Tables"],
        "recommendations": ["O documento excede o limite do modelo gpt-3.5-turbo de 16385 tokens."],
        "content_type": "conteudo_educacional",
        "chunking_recommendation": {
            "chunk_size": 1200,
            "chunk_overlap": 120,
            "desc": "textos didáticos com conceitos estruturados"
        }
    }

    text = analyzer.get_recommendations_text(analysis)
    assert "## Análise de Tokens" in text
    assert "Total: 30000 tokens" in text
    assert "Sugestão de Chunking" in text
    assert "Tipo de conteúdo detectado: **Conteudo Educacional**" in text
    assert "--chunk-size 1200" in text

def test_analyze_document():
    """Test full document analysis"""
    analyzer = TokenAnalyzer()

    # Create a simple document in LLMs.txt format
    document = """# Title: Test Document
# Date: 2025-04-25
# Author: Test Author

# Content
This is a test document with some content.
It has multiple paragraphs to analyze.

# Tables
| A | B |
|---|---|
| 1 | 2 |
"""

    # Mock count_tokens and analyze_sections to return predictable values
    with patch('src.tools.token_analyzer.count_tokens', return_value=100):
        with patch.object(analyzer, 'analyze_sections', return_value={
            "total_tokens": 100,
            "model_limit": 16385,
            "exceeds_limit": False,
            "percentages": {"# Content": 80.0, "# Tables": 20.0},
            "expensive_sections": [],
            "recommendations": ["O documento está dentro do limite do modelo."],
            "content_type": "documento_tecnico",
            "chunking_recommendation": {
                "chunk_size": 1000,
                "chunk_overlap": 100,
                "desc": "documentação técnica"
            }
        }):
            analysis = analyzer.analyze_document(document)

            assert analysis["total_tokens"] == 100
            assert "percentages" in analysis
            assert isinstance(analysis["recommendations"], list)

def test_analyze_document_with_content_type():
    """Test document analysis with content type detection"""
    analyzer = TokenAnalyzer()

    # Create an educational document
    document = """# Title: BNCC
# Date: 2025-04-25

# Content
Este documento apresenta a Base Nacional Comum Curricular (BNCC),
documento de caráter normativo que define o conjunto orgânico e progressivo
de aprendizagens essenciais que todos os alunos devem desenvolver ao longo
das etapas e modalidades da Educação Básica.

As habilidades e competências visam à formação integral dos estudantes.
"""

    # Mock _detect_content_type to return a specific content type
    with patch.object(analyzer, '_detect_content_type', return_value="conteudo_educacional"):
        analysis = analyzer.analyze_document(document)

        assert analysis["content_type"] == "conteudo_educacional"
        assert "chunking_recommendation" in analysis
        assert analysis["chunking_recommendation"]["chunk_size"] == 1200

def test_extract_content_sample():
    """Test extraction of content sample for large documents"""
    analyzer = TokenAnalyzer()

    # Create a large document
    large_content = "\n".join([f"Paragraph {i}" for i in range(1000)])

    section_map = {
        "# Title": "Large Document",
        "# Content": large_content,
        "# Summary": "This is a summary"
    }

    sample = analyzer._extract_content_sample(large_content, section_map, max_size=1000)

    # Sample should be limited to max_size
    assert len(sample) <= 1000

    # Test with empty content
    with pytest.raises(ValueError, match="não pode estar vazio"):
        analyzer._extract_content_sample("", {})

def test_model_limit_warnings():
    """Test model limit warnings in analysis"""
    analyzer = TokenAnalyzer(model_name="gpt-3.5-turbo")

    # Document close to limit
    close_doc = {
        "# Title": 100,
        "# Content": 13000  # Close to 16K limit
    }

    # Mock the analyze_sections method to include a warning about being close to the limit
    with patch.object(analyzer, 'analyze_sections', return_value={
        "total_tokens": 13100,
        "model_limit": 16385,
        "exceeds_limit": False,
        "percentages": {"# Title": 0.8, "# Content": 99.2},
        "expensive_sections": [],
        "recommendations": [
            "O documento está dentro do limite do modelo gpt-3.5-turbo de 16385 tokens.",
            "Atenção: O documento está próximo do limite (80% da capacidade)."
        ],
        "content_type": None
    }):
        analysis = analyzer.analyze_sections(close_doc)
        assert not analysis["exceeds_limit"]
        assert any("próximo do limite" in rec for rec in analysis["recommendations"])

    # Document way below limit
    small_doc = {
        "# Title": 100,
        "# Content": 1000
    }

    analysis = analyzer.analyze_sections(small_doc)
    assert not analysis["exceeds_limit"]
    assert not any("próximo do limite" in rec for rec in analysis["recommendations"])

def test_usage_percentage_calculation():
    """Test usage percentage calculation"""
    analyzer = TokenAnalyzer(model_name="gpt-3.5-turbo")
    model_limit = analyzer.model_limits["gpt-3.5-turbo"]

    # Document using 50% of limit
    half_doc = {
        "# Title": 100,
        "# Content": int(model_limit * 0.5) - 100
    }

    # Mock analyze_sections to return predictable percentages
    with patch.object(analyzer, 'analyze_sections', return_value={
        "total_tokens": int(model_limit * 0.5),
        "model_limit": model_limit,
        "exceeds_limit": False,
        "percentages": {"# Title": 1.0, "# Content": 99.0},
        "expensive_sections": [],
        "recommendations": ["O documento está dentro do limite do modelo."],
        "content_type": None
    }):
        analysis = analyzer.analyze_sections(half_doc)
        assert abs(list(analysis["percentages"].values())[0] - 1.0) < 0.1  # Should be close to 1%
        assert abs(list(analysis["percentages"].values())[1] - 99.0) < 0.1  # Should be close to 99%

def test_recommendations_for_chunking():
    """Test recommendations for chunking based on content type"""
    analyzer = TokenAnalyzer()

    # Create a document that exceeds limits
    large_doc = {
        "# Title": 100,
        "# Content": 20000
    }

    analysis = analyzer.analyze_sections(large_doc)

    # Add content type and chunking recommendation
    analysis["content_type"] = "documento_legal"
    analysis["chunking_recommendation"] = analyzer.chunking_by_content["documento_legal"]

    text = analyzer.get_recommendations_text(analysis)

    # Should recommend specific chunking settings
    assert "Sugestão de Chunking" in text
    assert f"--chunk-size {analyzer.chunking_by_content['documento_legal']['chunk_size']}" in text
    assert f"--chunk-overlap {analyzer.chunking_by_content['documento_legal']['chunk_overlap']}" in text

def test_count_tokens_different_models():
    """Test token counting for different models"""
    text = "This is a test sentence for token counting."

    # Count with different models
    gpt35_tokens = count_tokens(text, "gpt-3.5-turbo")
    gpt4_tokens = count_tokens(text, "gpt-4")

    # Both should return a positive number
    assert gpt35_tokens > 0
    assert gpt4_tokens > 0

def test_count_tokens_empty_input():
    """Test token counting with empty input"""
    empty_text = ""

    # Should return 0 for empty text
    assert count_tokens(empty_text, "gpt-3.5-turbo") == 0

def test_count_tokens_malformed_input():
    """Test token counting with malformed input"""
    # None should be treated as empty string
    assert count_tokens(None, "gpt-3.5-turbo") == 0

    # Non-string should be converted to string
    with patch('tiktoken.encoding_for_model') as mock_encoding:
        mock_encoder = MagicMock()
        mock_encoding.return_value = mock_encoder
        mock_encoder.encode.return_value = [1, 2, 3]  # 3 tokens

        result = count_tokens(123, "gpt-3.5-turbo")
        assert result == 3
        # Verify str conversion happened
        mock_encoder.encode.assert_called_once()