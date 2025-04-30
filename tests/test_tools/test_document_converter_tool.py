import os
import pytest
from src.tools.document_converter import DocumentConverterTool

class DummyConv:
    class Result:
        def __init__(self):
            class Doc:
                def export_to_markdown(self):
                    return "Para1\n\nPara2"
                def num_pages(self):
                    return 1
                def export_to_dict(self):
                    return {"content": "Para1\n\nPara2"}
                def export_to_html(self):
                    return "<html><body>Para1<br><br>Para2</body></html>"
                tables = []
                images = []
                metadata = {}
                raw_text = "<p>Raw HTML</p>"
                summary = "Document summary"
            self.document = Doc()

    def __init__(self):
        pass

    def convert(self, path, pipeline_options=None):  # pylint: disable=unused-argument
        return self.Result()

class DummyConvWithTables:
    class Table:
        def to_markdown(self):
            return "| A | B |\n|---|---|\n| 1 | 2 |"

    class Image:
        def __init__(self, uri):
            self.uri = uri
            self.caption = f"Image caption for {uri}"

    class Result:
        def __init__(self, tables, images):
            class Doc:
                def export_to_markdown(self):
                    return "Para1\n\nPara2"
                def num_pages(self):
                    return 1
                def export_to_dict(self):
                    return {"content": "Para1\n\nPara2"}
                def export_to_html(self):
                    return "<html><body>Para1<br><br>Para2</body></html>"

                def __init__(self):
                    self.tables = tables
                    self.images = images
                    self.metadata = {"author": "Test Author", "subject": "Test Subject"}
                    self.raw_text = "<p>Raw HTML</p>"
                    self.summary = "Document summary"

            self.document = Doc()

    def __init__(self):
        pass

    def convert(self, path, pipeline_options=None):  # pylint: disable=unused-argument
        # Create tables and images
        tables = [self.Table()]
        images = [self.Image('img1.png'), self.Image('img2.jpg')]

        # Return result with document
        return self.Result(tables, images)

class DummyConvEmpty:
    class Result:
        def __init__(self):
            class Doc:
                def export_to_markdown(self):
                    return ""
                def num_pages(self):
                    return 0
                def export_to_dict(self):
                    return {}
                def export_to_html(self):
                    return "<html><body></body></html>"
                tables = []
                images = []
                metadata = {}
                raw_text = ""
            self.document = Doc()

    def __init__(self):
        pass

    def convert(self, path, pipeline_options=None):  # pylint: disable=unused-argument
        return self.Result()

class DummyConvError:
    def __init__(self, error_message="Simulated conversion error"):
        self.error_message = error_message

    def convert(self, path, pipeline_options=None):  # pylint: disable=unused-argument
        raise RuntimeError(self.error_message)

@pytest.mark.parametrize('profile', ['llms-min', 'llms-full'])
def test_run_and_save(tmp_path, monkeypatch, profile):
    # Configura ambiente
    tool = DocumentConverterTool()

    # Mock the DocumentConverter constructor and convert method
    from docling.document_converter import DocumentConverter
    original_init = DocumentConverter.__init__

    def mock_document_converter_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        # Replace the real convert method with our dummy
        self.convert = DummyConv().convert

    # Apply the mock
    monkeypatch.setattr(DocumentConverter, '__init__', mock_document_converter_init)

    # Cria arquivo dummy
    src = tmp_path / 'dummy.pdf'
    src.write_text('dummy')
    # Troca cwd para tmp_path
    monkeypatch.chdir(tmp_path)
    # Executa conversão e salva
    output = tool.run(str(src), save_output=True, profile=profile)
    # Verifica retorno contém texto
    assert 'Para1' in output['formats']['llms']
    # Verifica arquivo de saída existe
    out_dir = tmp_path / 'output'
    assert out_dir.is_dir()
    base = 'dummy'
    outfile = out_dir / f"{base}.{profile}.llms.txt"
    assert outfile.exists()
    content = outfile.read_text(encoding='utf-8')
    # Verifica estrutura mínima
    assert '# Title:' in content
    if profile == 'llms-full':
        assert '# Content' in content
    else:
        assert '# Content' in content

def test_file_not_found(tmp_path):
    """Test handling of non-existent files"""
    tool = DocumentConverterTool()
    non_existent_file = tmp_path / 'non_existent.pdf'

    with pytest.raises(FileNotFoundError):
        tool.run(str(non_existent_file))

def test_unsupported_file_type(tmp_path, monkeypatch):
    """Test handling of unsupported file types"""
    tool = DocumentConverterTool()

    # Mock the DocumentConverter constructor and convert method
    from docling.document_converter import DocumentConverter
    original_init = DocumentConverter.__init__

    def mock_document_converter_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.convert = DummyConv().convert

    monkeypatch.setattr(DocumentConverter, '__init__', mock_document_converter_init)

    # Create unsupported file type
    unsupported_file = tmp_path / 'test.xyz'
    unsupported_file.write_text('test content')

    # The warning is logged using logger.warning, not using warnings.warn
    output = tool.run(str(unsupported_file))
    assert output is not None

@pytest.mark.parametrize('ocr_engine,ocr_language,force_ocr', [
    ('tesseract', None, False),
    ('tesseract', 'eng', True),
    ('auto', None, False),
    (None, None, False)
])
def test_ocr_options(tmp_path, monkeypatch, ocr_engine, ocr_language, force_ocr):
    """Test conversion with different OCR options"""
    tool = DocumentConverterTool()

    # Mock DocumentConverter
    from docling.document_converter import DocumentConverter
    original_init = DocumentConverter.__init__
    original_convert = DocumentConverter.convert

    # Create a spy to capture pipeline options
    pipeline_options_spy = {}

    def mock_convert(self, path, pipeline_options=None):
        nonlocal pipeline_options_spy
        # Capture the options
        if pipeline_options:
            pipeline_options_spy.update(pipeline_options)
        # Call the original or return a dummy result
        return DummyConv().convert(path)

    # Apply the mocks
    monkeypatch.setattr(DocumentConverter, '__init__', original_init)
    monkeypatch.setattr(DocumentConverter, 'convert', mock_convert)

    # Create test file
    test_file = tmp_path / 'test.pdf'
    test_file.write_text('test content')

    # Run with OCR options
    tool.run(str(test_file), ocr_engine=ocr_engine, ocr_language=ocr_language, force_ocr=force_ocr)

    # Verify OCR options were passed correctly
    if ocr_engine:
        assert 'ocr_engine' in pipeline_options_spy
        assert pipeline_options_spy['ocr_engine'] == ocr_engine
    if ocr_language:
        assert 'ocr_language' in pipeline_options_spy
        assert pipeline_options_spy['ocr_language'] == ocr_language
    if force_ocr:
        assert 'force_ocr' in pipeline_options_spy
        assert pipeline_options_spy['force_ocr'] == force_ocr

@pytest.mark.parametrize('chunk_size,chunk_overlap', [
    (500, 50),
    (1000, 100),
    (None, None)
])
def test_chunking_options(tmp_path, monkeypatch, chunk_size, chunk_overlap):
    """Test conversion with different chunking options"""
    tool = DocumentConverterTool(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    # Mock DocumentConverter
    from docling.document_converter import DocumentConverter
    original_init = DocumentConverter.__init__

    # Create a spy to capture pipeline options
    pipeline_options_spy = {}

    def mock_convert(self, path, pipeline_options=None):
        nonlocal pipeline_options_spy
        # Capture the options
        if pipeline_options:
            pipeline_options_spy.update(pipeline_options)
        # Return a dummy result
        return DummyConv().convert(path)

    # Apply the mocks
    monkeypatch.setattr(DocumentConverter, '__init__', original_init)
    monkeypatch.setattr(DocumentConverter, 'convert', mock_convert)

    # Create test file
    test_file = tmp_path / 'test.pdf'
    test_file.write_text('test content')

    # Run with chunking options
    tool.run(str(test_file))

    # Verify chunking options were passed correctly
    if chunk_size:
        assert 'chunk_size' in pipeline_options_spy
        assert pipeline_options_spy['chunk_size'] == chunk_size
    if chunk_overlap:
        assert 'chunk_overlap' in pipeline_options_spy
        assert pipeline_options_spy['chunk_overlap'] == chunk_overlap

def test_docling_import_failure(monkeypatch):
    """Test handling of Docling import failure"""
    # Mock import to fail
    import builtins
    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == 'docling.document_converter' or name == 'docling':
            raise ImportError("Simulated import error")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', mock_import)

    # We expect an ImportError when creating the tool
    with pytest.raises(ImportError, match="Docling não encontrado"):
        DocumentConverterTool()

def test_docling_pipeline_misconfiguration(monkeypatch, tmp_path):
    """Test handling of Docling pipeline misconfiguration"""
    # Create a test file
    test_file = tmp_path / 'test.pdf'
    test_file.write_text('test content')

    # Mock DocumentConverter to raise an error during initialization
    from docling.document_converter import DocumentConverter

    def mock_document_converter_init(*args, **kwargs):
        raise ValueError("Simulated pipeline configuration error")

    monkeypatch.setattr(DocumentConverter, '__init__', mock_document_converter_init)

    tool = DocumentConverterTool()

    with pytest.raises(RuntimeError, match="Erro na configuração do Docling"):
        tool.run(str(test_file))

def test_conversion_failure(tmp_path, monkeypatch):
    """Test handling of conversion failure"""
    tool = DocumentConverterTool()

    # Mock DocumentConverter
    from docling.document_converter import DocumentConverter
    original_init = DocumentConverter.__init__

    def mock_document_converter_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.convert = DummyConvError("Simulated conversion error").convert

    monkeypatch.setattr(DocumentConverter, '__init__', mock_document_converter_init)

    # Create test file
    test_file = tmp_path / 'test.pdf'
    test_file.write_text('test content')

    with pytest.raises(RuntimeError, match="Falha no processamento do documento"):
        tool.run(str(test_file))

@pytest.mark.parametrize('export_formats', [
    None,
    ['md'],
    ['json'],
    ['html'],
    ['md', 'json', 'html']
])
def test_multiple_output_formats(tmp_path, monkeypatch, export_formats):
    """Test output in multiple formats"""
    tool = DocumentConverterTool()

    # Mock DocumentConverter
    from docling.document_converter import DocumentConverter
    original_init = DocumentConverter.__init__

    def mock_document_converter_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.convert = DummyConv().convert

    monkeypatch.setattr(DocumentConverter, '__init__', mock_document_converter_init)

    # Create test file
    test_file = tmp_path / 'test.pdf'
    test_file.write_text('test content')
    monkeypatch.chdir(tmp_path)

    # Run with export formats
    output = tool.run(str(test_file), save_output=True, export_formats=export_formats)

    # Verify output formats
    assert 'llms' in output['formats']

    if export_formats:
        for fmt in export_formats:
            assert fmt in output['formats']

            # Check if files were created
            out_dir = tmp_path / 'output'
            outfile = out_dir / f"test.llms-full.{fmt}"
            assert outfile.exists()

def test_output_directory_creation(tmp_path, monkeypatch):
    """Test output directory creation"""
    tool = DocumentConverterTool()

    # Mock DocumentConverter
    from docling.document_converter import DocumentConverter
    original_init = DocumentConverter.__init__

    def mock_document_converter_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.convert = DummyConv().convert

    monkeypatch.setattr(DocumentConverter, '__init__', mock_document_converter_init)

    # Create test file
    test_file = tmp_path / 'test.pdf'
    test_file.write_text('test content')
    monkeypatch.chdir(tmp_path)

    # Delete output directory if it exists
    import shutil
    out_dir = tmp_path / 'output'
    if out_dir.exists():
        shutil.rmtree(out_dir)

    # Run with save_output=True
    tool.run(str(test_file), save_output=True)

    # Verify output directory was created
    assert out_dir.exists()
    assert out_dir.is_dir()

def test_export_to_langchain(tmp_path, monkeypatch):
    """Test export to LangChain"""
    tool = DocumentConverterTool()

    # Mock DocumentConverter
    from docling.document_converter import DocumentConverter
    original_init = DocumentConverter.__init__

    def mock_document_converter_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.convert = DummyConv().convert

    monkeypatch.setattr(DocumentConverter, '__init__', mock_document_converter_init)

    # Mock the exportar_para_langchain method to return a non-empty list
    original_export = tool.exportar_para_langchain

    def mock_export_to_langchain(doc, save_json=False):
        return [{"page_content": "Test content", "metadata": {"source": "test.pdf"}}]

    monkeypatch.setattr(tool, 'exportar_para_langchain', mock_export_to_langchain)

    # Create test file
    test_file = tmp_path / 'test.pdf'
    test_file.write_text('test content')

    # Run with export_to_langchain=True
    output = tool.run(str(test_file), export_to_langchain=True)

    # Verify langchain_docs is in output
    assert 'langchain_docs' in output
    assert isinstance(output['langchain_docs'], list)
    assert len(output['langchain_docs']) > 0

def test_batch_processing(tmp_path, monkeypatch):
    """Test batch processing of multiple files"""
    tool = DocumentConverterTool()

    # Mock DocumentConverter
    from docling.document_converter import DocumentConverter
    original_init = DocumentConverter.__init__

    def mock_document_converter_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.convert = DummyConv().convert

    monkeypatch.setattr(DocumentConverter, '__init__', mock_document_converter_init)

    # Create test directory with multiple files
    test_dir = tmp_path / 'test_dir'
    test_dir.mkdir()

    # Create multiple test files
    for i in range(3):
        test_file = test_dir / f'test{i}.pdf'
        test_file.write_text(f'test content {i}')

    # Run batch processing
    results = tool.processar_em_lote(str(test_dir), padrao="*.pdf")

    # Verify results
    assert len(results) == 3
    for i in range(3):
        file_path = str(test_dir / f'test{i}.pdf')
        assert file_path in results
        assert results[file_path]['status'] == 'success'

def test_batch_processing_empty_directory(tmp_path):
    """Test batch processing of an empty directory"""
    tool = DocumentConverterTool()

    # Create empty test directory
    test_dir = tmp_path / 'empty_dir'
    test_dir.mkdir()

    # Run batch processing
    results = tool.processar_em_lote(str(test_dir), padrao="*.pdf")

    # Verify results
    assert len(results) == 0

def test_batch_processing_partially_corrupt(tmp_path, monkeypatch):
    """Test batch processing with some corrupt files"""
    tool = DocumentConverterTool()

    # Mock DocumentConverter
    from docling.document_converter import DocumentConverter
    original_init = DocumentConverter.__init__

    def mock_document_converter_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)

        # Make some files fail during conversion
        def conditional_convert(path, pipeline_options=None):
            if 'corrupt' in path:
                raise RuntimeError("Simulated corruption error")
            return DummyConv().convert(path, pipeline_options)

        self.convert = conditional_convert

    monkeypatch.setattr(DocumentConverter, '__init__', mock_document_converter_init)

    # Create test directory with mixed files
    test_dir = tmp_path / 'mixed_dir'
    test_dir.mkdir()

    # Create good and corrupt test files
    for i in range(2):
        test_file = test_dir / f'test{i}.pdf'
        test_file.write_text(f'test content {i}')

    corrupt_file = test_dir / 'corrupt.pdf'
    corrupt_file.write_text('corrupt content')

    # Run batch processing
    results = tool.processar_em_lote(str(test_dir), padrao="*.pdf")

    # Verify results
    assert len(results) == 3

    # Check good files
    for i in range(2):
        file_path = str(test_dir / f'test{i}.pdf')
        assert file_path in results
        assert results[file_path]['status'] == 'success'

    # Check corrupt file
    corrupt_path = str(test_dir / 'corrupt.pdf')
    assert corrupt_path in results
    assert results[corrupt_path]['status'] == 'error'

def test_extract_tables_images_raw(tmp_path, monkeypatch):
    """Test extraction of tables, images, and raw text"""
    tool = DocumentConverterTool()

    # Mock DocumentConverter
    from docling.document_converter import DocumentConverter
    original_init = DocumentConverter.__init__

    def mock_document_converter_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.convert = DummyConvWithTables().convert

    monkeypatch.setattr(DocumentConverter, '__init__', mock_document_converter_init)

    # Create test file
    test_file = tmp_path / 'test.pdf'
    test_file.write_text('test content')

    # Run with profile that includes tables, images, and raw text
    output = tool.run(str(test_file), profile='llms-full')

    # Verify output contains tables, images, and raw text
    assert 'llms' in output['formats']
    llms_text = output['formats']['llms']

    # Check for tables
    assert '# Tables' in llms_text
    assert '| A | B |' in llms_text

    # Check for images
    assert '# Images' in llms_text
    assert 'Image caption for img1.png' in llms_text
    assert 'Image caption for img2.jpg' in llms_text

    # Check for raw text
    assert '# Raw' in llms_text
    assert '<p>Raw HTML</p>' in llms_text
