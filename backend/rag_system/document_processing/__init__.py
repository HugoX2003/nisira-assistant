"""
Módulo de Procesamiento de Documentos
===================================

Procesa documentos PDF, DOCX, TXT y otros formatos preservando el contexto.
"""

from .pdf_processor import PDFProcessor
from .text_processor import TextProcessor

__all__ = ["PDFProcessor", "TextProcessor"]