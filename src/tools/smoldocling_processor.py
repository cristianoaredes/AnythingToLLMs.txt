"""
Processador de documentos usando SmolDocling.

Este módulo integra o SmolDocling para melhorar a extração de documentos,
especialmente para conteúdo visual complexo.
"""

import os
import sys
import tempfile
import logging
from pathlib import Path
from src.utils.logging_config import setup_logger

# Configurar logger para este módulo
logger = setup_logger(__name__)

class SmolDoclingProcessor:
    """
    Processador de documentos usando SmolDocling para melhorar a extração de conteúdo
    visual complexo como tabelas, fórmulas e código.
    """
    
    def __init__(self):
        """
        Inicializa o processador SmolDocling.
        """
        logger.info("Inicializando SmolDoclingProcessor")
        
        # Verificar disponibilidade do SmolDocling
        try:
            import torch
            from transformers import AutoProcessor, AutoModelForVision2Seq
            
            self.torch_available = True
            logger.info("PyTorch disponível para SmolDocling")
            
            # Verificar disponibilidade de GPU
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"SmolDocling usando dispositivo: {self.device}")
            
            # Não carregar o modelo ainda para economizar memória
            self.model = None
            self.processor = None
            self.model_loaded = False
            
        except ImportError as e:
            logger.warning(f"SmolDocling não disponível: {str(e)}. É necessário instalar transformers e torch.")
            self.torch_available = False
    
    def load_model(self):
        """
        Carrega o modelo SmolDocling sob demanda.
        
        Returns:
            bool: True se o modelo foi carregado com sucesso, False caso contrário
        """
        if self.model_loaded:
            return True
            
        if not self.torch_available:
            logger.error("PyTorch ou transformers não disponíveis para carregar SmolDocling")
            return False
            
        try:
            from transformers import AutoProcessor, AutoModelForVision2Seq
            import torch
            
            logger.info("Carregando modelo SmolDocling...")
            
            # Carregar o processador
            self.processor = AutoProcessor.from_pretrained("ds4sd/SmolDocling-256M-preview")
            
            # Carregar o modelo
            self.model = AutoModelForVision2Seq.from_pretrained(
                "ds4sd/SmolDocling-256M-preview",
                torch_dtype=torch.bfloat16,
                _attn_implementation="flash_attention_2" if self.device == "cuda" else "eager"
            ).to(self.device)
            
            self.model_loaded = True
            logger.info("Modelo SmolDocling carregado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao carregar modelo SmolDocling: {str(e)}")
            return False
    
    def process_image(self, image_path):
        """
        Processa uma imagem com SmolDocling.
        
        Args:
            image_path (str): Caminho para a imagem
            
        Returns:
            str: Texto extraído da imagem em formato DocTags
        """
        # Carregar modelo se ainda não estiver carregado
        if not self.model_loaded and not self.load_model():
            logger.error("Não foi possível carregar o modelo SmolDocling")
            return None
            
        try:
            from PIL import Image
            import torch
            
            logger.info(f"Processando imagem com SmolDocling: {image_path}")
            
            # Carregar imagem usando PIL diretamente
            pil_image = Image.open(image_path).convert('RGB')
            
            # Preparar modelo para geração
            instruction = "<image>Convert this document page to text with DocTags format.</image>"
            
            # Preparar inputs com texto e imagem
            inputs = self.processor(
                text=[instruction],  # Usar lista para texto com marcador de imagem
                images=[pil_image],  # Usar lista para imagens
                return_tensors="pt",
                truncation=True,
                max_length=4096
            ).to(self.device)
            
            # Gerar saída
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=4096,
                do_sample=False
            )
            
            # Decodificar saída
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            logger.info(f"Imagem processada com sucesso: {len(generated_text)} caracteres")
            logger.debug(f"Texto gerado: {generated_text[:500]}...")  # Log primeiros 500 caracteres
            
            return generated_text
            
        except Exception as e:
            logger.error(f"Erro ao processar imagem com SmolDocling: {str(e)}")
            logger.exception("Detalhes do erro:")
            return None
    
    def convert_to_docling(self, doctags_text):
        """
        Converte texto em formato DocTags para um documento Docling.
        
        Args:
            doctags_text (str): Texto no formato DocTags gerado pelo SmolDocling
            
        Returns:
            DoclingDocument: Documento no formato Docling
        """
        try:
            from docling_core.types.doc import DoclingDocument
            
            logger.info("Convertendo DocTags para DoclingDocument")
            
            # Verificar se o texto está vazio ou não contém marcadores DocTags
            if not doctags_text or '<doctags>' not in doctags_text:
                # Adicionar marcadores DocTags se não existirem
                doctags_text = f"<doctags>{doctags_text}</doctags>"
            
            # Criar DoclingDocument com nome padrão e texto
            doc = DoclingDocument(
                name="SmolDocling_Processed_Document",
                text=doctags_text
            )
            
            logger.info("DocTags convertido para DoclingDocument com sucesso")
            return doc
            
        except Exception as e:
            logger.error(f"Erro ao converter DocTags para DoclingDocument: {str(e)}")
            logger.exception("Detalhes do erro:")
            return None
    
    def process_document(self, file_path):
        """
        Processa um documento usando SmolDocling.
        
        Args:
            file_path (str): Caminho para o documento
            
        Returns:
            DoclingDocument: Documento processado
        """
        # Verificar se arquivo existe
        if not os.path.exists(file_path):
            logger.error(f"Arquivo não encontrado: {file_path}")
            return None
            
        # Verificar extensão do arquivo
        _, ext = os.path.splitext(file_path)
        image_extensions = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp']
        
        if ext.lower() in image_extensions:
            # Processar imagem diretamente
            doctags_text = self.process_image(file_path)
            if doctags_text:
                return self.convert_to_docling(doctags_text)
            else:
                return None
        elif ext.lower() == '.pdf':
            # Para PDF, renderizar páginas e processar uma a uma
            try:
                import PyPDF2
                from PIL import Image
                
                logger.info(f"Processando PDF com SmolDocling: {file_path}")
                
                # Criar diretório temporário para salvar imagens de páginas
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Renderizar cada página como imagem
                    all_doctags = []
                    
                    # Abrir PDF
                    with open(file_path, 'rb') as pdf_file:
                        pdf_reader = PyPDF2.PdfReader(pdf_file)
                        
                        for page_idx, page in enumerate(pdf_reader.pages):
                            # Renderizar página como imagem
                            page_image_path = os.path.join(temp_dir, f"page_{page_idx}.png")
                            
                            # Usar PyMuPDF para renderização de página
                            import fitz
                            doc = fitz.open(file_path)
                            page = doc[page_idx]
                            pix = page.get_pixmap()
                            pix.save(page_image_path)
                            
                            # Processar imagem com SmolDocling
                            doctags_text = self.process_image(page_image_path)
                            if doctags_text:
                                all_doctags.append(doctags_text)
                    
                    # Combinar resultados de todas as páginas
                    if all_doctags:
                        combined_doctags = "\n\n".join(all_doctags)
                        return self.convert_to_docling(combined_doctags)
                
                logger.error("Nenhuma página processada com sucesso no PDF")
                return None
                
            except Exception as e:
                logger.error(f"Erro ao processar PDF com SmolDocling: {str(e)}")
                logger.exception("Detalhes do erro:")
                return None
        else:
            logger.error(f"Formato não suportado para SmolDocling: {ext}")
            return None
    
    def get_features(self):
        """
        Retorna as características suportadas pelo SmolDocling.
        
        Returns:
            dict: Dicionário com as características suportadas
        """
        features = {
            "available": self.torch_available,
            "loaded": self.model_loaded,
            "device": self.device if self.torch_available else None,
            "capabilities": [
                "OCR com detecção de layout",
                "Reconhecimento de tabelas",
                "Reconhecimento de código",
                "Reconhecimento de fórmulas matemáticas",
                "Classificação de figuras"
            ] if self.torch_available else []
        }
        
        return features
