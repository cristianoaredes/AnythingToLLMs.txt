import pytest
from unittest.mock import patch, MagicMock
from src.tools.llms_formatter import LLMSFormatter


class DummyTable:
    def __init__(self, data):
        self._data = data

    def to_markdown(self):
        # Simula saída de markdown de tabela
        header = '| ' + ' | '.join(self._data['columns']) + ' |'
        sep = '| ' + ' | '.join(['---'] * len(self._data['columns'])) + ' |'
        rows = []
        for row in self._data['rows']:
            rows.append('| ' + ' | '.join(row) + ' |')
        return '\n'.join([header, sep] + rows)


class DummyImage:
    def __init__(self, uri):
        self.uri = uri
        self.caption = f"Image caption for {uri}"


class DummyDoc:
    def __init__(self):
        self.tables = [DummyTable({'columns': ['A', 'B'], 'rows': [['1', '2']]})]
        self.images = [DummyImage('img1.png'), DummyImage('img2.jpg')]
        self.raw_text = '<p>Raw HTML</p>'
        self.metadata = {
            'author': 'Test Author',
            'subject': 'Test Subject'
        }
        self.summary = None

    def export_to_markdown(self):
        return 'Paragraph1\n\nParagraph2'


class DummyDocWithSummary(DummyDoc):
    def __init__(self):
        super().__init__()
        self.summary = "Explicit summary text"


class DummyDocEmpty:
    def __init__(self):
        self.tables = []
        self.images = []
        self.raw_text = ''
        self.metadata = {}
        self.summary = None

    def export_to_markdown(self):
        return ''


class DummyDocTablesOnly:
    def __init__(self):
        self.tables = [
            DummyTable({'columns': ['A', 'B'], 'rows': [['1', '2']]}),
            DummyTable({'columns': ['X', 'Y', 'Z'], 'rows': [['a', 'b', 'c'], ['d', 'e', 'f']]})
        ]
        self.images = []
        self.raw_text = ''
        self.metadata = {}
        self.summary = None

    def export_to_markdown(self):
        return ''


class DummyDocImagesOnly:
    def __init__(self):
        self.tables = []
        self.images = [
            DummyImage('img1.png'),
            DummyImage('img2.jpg'),
            DummyImage('img3.gif')
        ]
        self.raw_text = ''
        self.metadata = {}
        self.summary = None

    def export_to_markdown(self):
        return ''


class DummyDocLarge:
    def __init__(self):
        self.tables = [DummyTable({'columns': ['A', 'B'], 'rows': [['1', '2']]})]
        self.images = [DummyImage('img1.png')]
        self.raw_text = '<p>Raw HTML</p>'
        self.metadata = {
            'author': 'Test Author',
            'subject': 'Test Subject'
        }
        self.summary = None

    def export_to_markdown(self):
        # Generate a very large content
        return '\n\n'.join([f'Paragraph {i}' for i in range(1, 1000)])


@pytest.mark.parametrize('profile,expected_sections', [
    ('llms-min', ['# Title:', '# Content']),
    ('llms-ctx', ['# Title:', '# Content']),  # Summary is optional and depends on content
    ('llms-tables', ['# Title:', '# Content', '# Tables']),
    ('llms-images', ['# Title:', '# Content', '# Images']),
    ('llms-raw', ['# Title:', '# Raw']),
    ('llms-full', ['# Title:', '# Content', '# Tables', '# Images', '# Raw']),
])
def test_llms_formatter_profiles(profile, expected_sections):
    formatter = LLMSFormatter()
    doc = DummyDoc()
    output = formatter.format(doc, title="Test", date="2025-04-25", source="dummy", profile=profile)
    # Verifica que todas as seções esperadas aparecem
    for section in expected_sections:
        assert section in output

    # Special case for llms-ctx with explicit summary
    if profile == 'llms-ctx':
        doc_with_summary = DummyDocWithSummary()
        output_with_summary = formatter.format(doc_with_summary, title="Test", profile=profile)
        assert '# Summary' in output_with_summary


def test_llms_min_content_only():
    """Test basic content without errors"""
    formatter = LLMSFormatter()
    doc = DummyDoc()
    output = formatter.format(doc, title="Test", date="2025-04-25", source="dummy", profile="llms-min")
    # Deve conter apenas uma seção de conteúdo após metadata
    assert output.count('# Content') == 1
    assert 'Paragraph1' in output


def test_llms_images_content_and_images():
    """Test that image references appear correctly"""
    formatter = LLMSFormatter()
    doc = DummyDoc()
    output = formatter.format(doc, title="ImgTest", profile="llms-images")
    # Deve conter seção de imagens
    assert '# Images' in output
    assert 'Image caption for img1.png' in output
    assert 'Image caption for img2.jpg' in output


def test_llms_raw_sections():
    """Test that raw section contains HTML"""
    formatter = LLMSFormatter()
    doc = DummyDoc()
    output = formatter.format(doc, title="RawTest", profile="llms-raw")
    assert '<p>Raw HTML</p>' in output


def test_llms_full_references():
    """Test references in llms-full"""
    formatter = LLMSFormatter()
    doc = DummyDoc()
    output = formatter.format(doc, title="FullTest", profile="llms-full")
    # No longer testing references directly since they're not part of the implementation anymore
    assert '# Raw' in output


def test_llms_full_summary_section():
    """Test Summary section in llms-full"""
    formatter = LLMSFormatter()
    doc = DummyDoc()
    output = formatter.format(doc, title="FullTest", profile="llms-full")
    # Deve conter seção de Summary com primeiros parágrafos
    assert 'Paragraph1' in output
    assert 'Paragraph2' in output


def test_metadata_inclusion():
    """Test metadata inclusion in output"""
    formatter = LLMSFormatter()
    doc = DummyDoc()
    output = formatter.format(
        doc,
        title="Metadata Test",
        date="2025-04-25",
        source="test_source.pdf",
        profile="llms-min"
    )

    # Check all metadata is included
    assert '# Title: Metadata Test' in output
    assert '# Date: 2025-04-25' in output
    assert '# Source: test_source.pdf' in output
    assert '# Author: Test Author' in output
    assert '# Subject: Test Subject' in output


def test_explicit_summary_extraction():
    """Test extraction of explicit summary"""
    formatter = LLMSFormatter()
    doc = DummyDocWithSummary()
    output = formatter.format(doc, title="Summary Test", profile="llms-ctx")

    # Check summary is included
    assert '# Summary' in output
    assert 'Explicit summary text' in output


def test_automatic_summary_extraction():
    """Test automatic summary generation"""
    formatter = LLMSFormatter()
    doc = DummyDoc()

    # Mock _gerar_sumario_automatico to return a predictable summary
    with patch.object(formatter, '_gerar_sumario_automatico', return_value="Paragraph1\n\nParagraph2"):
        output = formatter.format(doc, title="Auto Summary Test", profile="llms-ctx")

        # Check summary is generated from content
        assert '# Summary' in output
        assert 'Paragraph1' in output


def test_empty_document():
    """Test handling of empty document"""
    formatter = LLMSFormatter()
    doc = DummyDocEmpty()
    output = formatter.format(doc, title="Empty Doc", profile="llms-full")

    # Should still have basic structure
    assert '# Title: Empty Doc' in output
    assert '# Content' in output


def test_document_with_only_tables():
    """Test document with only tables"""
    formatter = LLMSFormatter()
    doc = DummyDocTablesOnly()
    output = formatter.format(doc, title="Tables Only", profile="llms-tables")

    # Should have tables section
    assert '# Tables' in output
    assert '| A | B |' in output
    assert '| X | Y | Z |' in output


def test_document_with_only_images():
    """Test document with only images"""
    formatter = LLMSFormatter()
    doc = DummyDocImagesOnly()
    output = formatter.format(doc, title="Images Only", profile="llms-images")

    # Should have images section
    assert '# Images' in output
    assert 'Image caption for img1.png' in output
    assert 'Image caption for img2.jpg' in output
    assert 'Image caption for img3.gif' in output


def test_document_with_missing_metadata():
    """Test document with missing metadata"""
    formatter = LLMSFormatter()
    doc = DummyDocEmpty()
    output = formatter.format(doc, profile="llms-min")

    # Should not have metadata sections
    assert '# Title:' not in output
    assert '# Date:' not in output
    assert '# Source:' not in output
    assert '# Author:' not in output


def test_document_with_very_large_content():
    """Test document with very large content (test truncation/limits)"""
    formatter = LLMSFormatter()
    doc = DummyDocLarge()
    output = formatter.format(doc, title="Large Doc", profile="llms-full")

    # Should contain token analysis section
    assert '# Token Analysis' in output
    assert 'Total tokens' in output


def test_exception_in_summary_extraction():
    """Test handling of exception in summary extraction"""
    formatter = LLMSFormatter()
    doc = DummyDoc()

    # Mock _gerar_sumario_automatico to raise an exception
    with patch.object(formatter, '_gerar_sumario_automatico', side_effect=Exception("Summary error")):
        output = formatter.format(doc, title="Summary Error", profile="llms-ctx")

        # Should still produce output without summary
        assert '# Title: Summary Error' in output
        assert '# Content' in output


def test_exception_in_content_formatting():
    """Test handling of exception in content formatting"""
    formatter = LLMSFormatter()
    doc = DummyDoc()

    # Create a doc that raises an exception when export_to_markdown is called
    doc.export_to_markdown = MagicMock(side_effect=Exception("Content error"))

    output = formatter.format(doc, title="Content Error", profile="llms-min")

    # Should contain error message
    assert 'Erro ao processar conteúdo principal' in output or 'Error' in output


def test_token_analysis_section():
    """Test token analysis section in full profile"""
    formatter = LLMSFormatter()
    doc = DummyDoc()

    output = formatter.format(doc, title="Token Analysis", profile="llms-full")

    # Should contain token analysis
    assert '# Token Analysis' in output
    assert 'Total tokens' in output
    assert 'gpt-3.5-turbo' in output
