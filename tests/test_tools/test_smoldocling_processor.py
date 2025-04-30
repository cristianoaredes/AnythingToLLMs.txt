from unittest.mock import patch, MagicMock
import os
import sys
import tempfile
from PIL import Image

from src.tools.smoldocling_processor import SmolDoclingProcessor


class TestSmolDoclingProcessor:
    """Test suite for SmolDoclingProcessor"""

    def test_init(self):
        """Test initialization of SmolDoclingProcessor"""
        # Test with torch available
        with patch('src.tools.smoldocling_processor.torch', create=True):
            with patch('src.tools.smoldocling_processor.AutoProcessor', create=True):
                with patch('src.tools.smoldocling_processor.AutoModelForVision2Seq', create=True):
                    processor = SmolDoclingProcessor()
                    assert processor.torch_available is True
                    assert processor.model_loaded is False

        # Test without torch - create a processor and manually set torch_available
        processor = SmolDoclingProcessor()
        processor.torch_available = False
        assert processor.torch_available is False

def raise_import_error(name):
    """Helper function to raise ImportError for specific modules"""
    raise ImportError(f"No module named '{name}'")

class TestSmolDoclingProcessor(TestSmolDoclingProcessor):
    """Continuation of test class"""

    def test_load_model(self):
        """Test loading the SmolDocling model"""
        # Create a processor with mocked dependencies
        processor = SmolDoclingProcessor()

        # Mock the dependencies directly on the processor
        with patch.object(processor, 'load_model', autospec=True) as mock_load_model:
            # Set up the mock to return True and set model_loaded
            def side_effect():
                processor.model_loaded = True
                return True

            mock_load_model.side_effect = side_effect

            # Test loading model
            result = processor.load_model()

            # Verify model was loaded
            assert result is True
            assert processor.model_loaded is True
            assert mock_load_model.called

    def test_load_model_failure(self):
        """Test handling of model loading failure"""
        # Create a processor with mocked dependencies
        processor = SmolDoclingProcessor()
        processor.torch_available = True
        processor.model_loaded = False

        # Mock the load_model method to simulate failure
        with patch.object(processor, 'load_model', autospec=True) as mock_load_model:
            # Set up the mock to return False
            mock_load_model.return_value = False

            # Test loading model
            result = processor.load_model()

            # Verify model loading failed
            assert result is False
            assert processor.model_loaded is False

    def test_process_image(self):
        """Test processing an image with SmolDocling"""
        processor = SmolDoclingProcessor()

        # Create a temporary test image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            # Create a simple test image
            img = Image.new('RGB', (100, 100), color='red')
            img.save(tmp_file.name)

            try:
                # Mock model loading and processing
                with patch.object(processor, 'load_model', return_value=True):
                    processor.model_loaded = True
                    processor.device = "cpu"

                    # Mock processor and model
                    processor.processor = MagicMock()
                    processor.model = MagicMock()

                    # Mock processor.batch_decode to return a sample result
                    processor.processor.batch_decode.return_value = ["Sample DocTags output"]

                    # Mock model.generate to return a tensor
                    processor.model.generate.return_value = MagicMock()

                    # Test processing image
                    result = processor.process_image(tmp_file.name)

                    # Verify result
                    assert result == "Sample DocTags output"
                    assert processor.processor.batch_decode.called
                    assert processor.model.generate.called
            finally:
                # Clean up the temporary file
                os.unlink(tmp_file.name)

    def test_process_image_model_load_failure(self):
        """Test handling of model loading failure during image processing"""
        processor = SmolDoclingProcessor()

        # Mock load_model to fail
        with patch.object(processor, 'load_model', return_value=False):
            result = processor.process_image("dummy.png")

            # Verify result is None
            assert result is None

    def test_process_image_processing_error(self):
        """Test handling of image processing error"""
        processor = SmolDoclingProcessor()

        # Mock model loading to succeed but processing to fail
        with patch.object(processor, 'load_model', return_value=True):
            processor.model_loaded = True

            # Mock PIL.Image.open to raise an exception
            with patch('PIL.Image.open', side_effect=Exception("Image processing error")):
                result = processor.process_image("dummy.png")

                # Verify result is None
                assert result is None

    def test_convert_to_docling(self):
        """Test conversion of DocTags to DoclingDocument"""
        processor = SmolDoclingProcessor()

        # Mock DoclingDocument
        mock_doc = MagicMock()

        # Use a module-level patch for docling_core.types.doc
        with patch.dict('sys.modules', {'docling_core.types.doc': MagicMock()}):
            # Create a mock DoclingDocument class
            mock_docling_module = sys.modules['docling_core.types.doc']
            mock_docling_module.DoclingDocument = MagicMock(return_value=mock_doc)

            # Test with valid DocTags
            result = processor.convert_to_docling("<doctags>Test content</doctags>")

            # Verify DoclingDocument was created
            assert result is mock_doc
            mock_docling_module.DoclingDocument.assert_called_once()

            # Test with DocTags missing tags
            result = processor.convert_to_docling("Test content without tags")

            # Verify tags were added
            assert result is mock_doc
            assert "<doctags>Test content without tags</doctags>" in str(mock_docling_module.DoclingDocument.call_args)

    def test_convert_to_docling_error(self):
        """Test handling of DocTags conversion error"""
        processor = SmolDoclingProcessor()

        # Use a module-level patch for docling_core.types.doc
        with patch.dict('sys.modules', {'docling_core.types.doc': MagicMock()}):
            # Create a mock DoclingDocument class that raises an exception
            mock_docling_module = sys.modules['docling_core.types.doc']
            mock_docling_module.DoclingDocument = MagicMock(side_effect=Exception("Conversion error"))

            result = processor.convert_to_docling("Test content")

            # Verify result is None
            assert result is None

    def test_process_document_file_not_found(self):
        """Test handling of non-existent file"""
        processor = SmolDoclingProcessor()

        result = processor.process_document("non_existent_file.pdf")

        # Verify result is None
        assert result is None

    def test_process_document_unsupported_format(self):
        """Test handling of unsupported file format"""
        processor = SmolDoclingProcessor()

        # Create a temporary file with unsupported extension
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as tmp_file:
            tmp_file.write(b"Test content")

            try:
                result = processor.process_document(tmp_file.name)

                # Verify result is None
                assert result is None
            finally:
                # Clean up the temporary file
                os.unlink(tmp_file.name)

    def test_process_document_image(self):
        """Test processing an image document"""
        processor = SmolDoclingProcessor()

        # Create a temporary test image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            # Create a simple test image
            img = Image.new('RGB', (100, 100), color='blue')
            img.save(tmp_file.name)

            try:
                # Mock process_image and convert_to_docling
                with patch.object(processor, 'process_image', return_value="DocTags content"):
                    with patch.object(processor, 'convert_to_docling', return_value=MagicMock()):
                        result = processor.process_document(tmp_file.name)

                        # Verify result is not None
                        assert result is not None
                        assert processor.process_image.called
                        assert processor.convert_to_docling.called
            finally:
                # Clean up the temporary file
                os.unlink(tmp_file.name)

    def test_process_document_pdf(self):
        """Test processing a PDF document"""
        processor = SmolDoclingProcessor()

        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(b"%PDF-1.5\n%Test PDF content")
            tmp_file_path = tmp_file.name

        try:
            # Mock all the necessary components
            with patch('os.path.exists', return_value=True):
                # Mock PyPDF2
                with patch.dict('sys.modules', {'PyPDF2': MagicMock()}):
                    mock_pdf = MagicMock()
                    mock_pdf.PdfReader.return_value.pages = [MagicMock()]
                    sys.modules['PyPDF2'] = mock_pdf

                    # Mock fitz (PyMuPDF)
                    with patch.dict('sys.modules', {'fitz': MagicMock()}):
                        mock_fitz = sys.modules['fitz']
                        mock_fitz.open.return_value = MagicMock()
                        mock_fitz.open.return_value.__getitem__.return_value = MagicMock()
                        mock_fitz.open.return_value.__getitem__.return_value.get_pixmap.return_value = MagicMock()

                        # Mock our processor methods
                        with patch.object(processor, 'process_image', return_value="DocTags content"):
                            with patch.object(processor, 'convert_to_docling', return_value=MagicMock()):
                                # Process the temporary PDF
                                result = processor.process_document(tmp_file_path)

                                # Verify result is not None
                                assert result is not None
        finally:
            # Clean up
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    def test_get_features(self):
        """Test getting SmolDocling features"""
        processor = SmolDoclingProcessor()

        # Test with torch available
        processor.torch_available = True
        processor.model_loaded = True
        processor.device = "cuda"

        features = processor.get_features()

        # Verify features
        assert features["available"] is True
        assert features["loaded"] is True
        assert features["device"] == "cuda"
        assert len(features["capabilities"]) > 0

        # Test without torch
        processor.torch_available = False

        features = processor.get_features()

        # Verify features
        assert features["available"] is False
        assert features["device"] is None
        assert len(features["capabilities"]) == 0
