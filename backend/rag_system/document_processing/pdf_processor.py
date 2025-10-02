"""
PDF Processor
============

Procesador avanzado de documentos PDF que preserva el contexto,
estructura y metadatos importantes para el sistema RAG.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
import re
from pathlib import Path

try:
    import PyPDF2
    import pdfplumber
    PYPDF2_AVAILABLE = True
    PDFPLUMBER_AVAILABLE = True
except ImportError as e:
    if 'PyPDF2' in str(e):
        PYPDF2_AVAILABLE = False
    if 'pdfplumber' in str(e):
        PDFPLUMBER_AVAILABLE = False

from ..config import DOCUMENT_PROCESSING_CONFIG

logger = logging.getLogger(__name__)

class PDFProcessor:
    """
    Procesador avanzado de documentos PDF
    """
    
    def __init__(self):
        self.config = DOCUMENT_PROCESSING_CONFIG
        self.chunk_size = self.config['chunk_size']
        self.chunk_overlap = self.config['chunk_overlap']
        self.preserve_structure = self.config['preserve_structure']
        self.extract_metadata = self.config['extract_metadata']
    
    def is_available(self) -> bool:
        """Verificar si las librerías necesarias están disponibles"""
        return PYPDF2_AVAILABLE and PDFPLUMBER_AVAILABLE
    
    def extract_text_with_pypdf2(self, pdf_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extraer texto usando PyPDF2 (método básico)
        
        Args:
            pdf_path: Ruta al archivo PDF
        
        Returns:
            Tupla con (texto_extraído, metadatos)
        """
        if not PYPDF2_AVAILABLE:
            raise ImportError("PyPDF2 no está disponible")
        
        text = ""
        metadata = {}
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extraer metadatos
                if self.extract_metadata and pdf_reader.metadata:
                    metadata = {
                        'title': pdf_reader.metadata.get('/Title', ''),
                        'author': pdf_reader.metadata.get('/Author', ''),
                        'subject': pdf_reader.metadata.get('/Subject', ''),
                        'creator': pdf_reader.metadata.get('/Creator', ''),
                        'producer': pdf_reader.metadata.get('/Producer', ''),
                        'creation_date': pdf_reader.metadata.get('/CreationDate', ''),
                        'modification_date': pdf_reader.metadata.get('/ModDate', ''),
                        'num_pages': len(pdf_reader.pages)
                    }
                
                # Extraer texto página por página
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            if self.preserve_structure:
                                text += f"\\n\\n--- PÁGINA {page_num + 1} ---\\n\\n"
                            text += page_text + "\\n"
                    except Exception as e:
                        logger.warning(f"Error extrayendo página {page_num + 1}: {e}")
                        continue
                
                logger.info(f"✅ Texto extraído con PyPDF2: {len(text)} caracteres")
                
        except Exception as e:
            logger.error(f"❌ Error procesando PDF con PyPDF2: {e}")
            raise
        
        return text, metadata
    
    def extract_text_with_pdfplumber(self, pdf_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extraer texto usando pdfplumber (método avanzado con mejor estructura)
        
        Args:
            pdf_path: Ruta al archivo PDF
        
        Returns:
            Tupla con (texto_extraído, metadatos)
        """
        if not PDFPLUMBER_AVAILABLE:
            raise ImportError("pdfplumber no está disponible")
        
        text = ""
        metadata = {}
        tables_info = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Extraer metadatos básicos
                if self.extract_metadata:
                    metadata = {
                        'num_pages': len(pdf.pages),
                        'file_size': os.path.getsize(pdf_path),
                        'file_name': os.path.basename(pdf_path)
                    }
                    
                    # Metadatos del PDF si están disponibles
                    if hasattr(pdf, 'metadata') and pdf.metadata:
                        metadata.update({
                            'title': pdf.metadata.get('Title', ''),
                            'author': pdf.metadata.get('Author', ''),
                            'subject': pdf.metadata.get('Subject', ''),
                            'creator': pdf.metadata.get('Creator', ''),
                            'producer': pdf.metadata.get('Producer', ''),
                            'creation_date': pdf.metadata.get('CreationDate', ''),
                            'modification_date': pdf.metadata.get('ModDate', '')
                        })
                
                # Procesar cada página
                for page_num, page in enumerate(pdf.pages):
                    try:
                        # Extraer texto principal
                        page_text = page.extract_text()
                        
                        if page_text and page_text.strip():
                            if self.preserve_structure:
                                text += f"\\n\\n=== PÁGINA {page_num + 1} ===\\n\\n"
                            
                            # Limpiar y normalizar texto
                            page_text = self._clean_text(page_text)
                            text += page_text + "\\n"
                        
                        # Extraer tablas si las hay
                        if self.preserve_structure:
                            tables = page.extract_tables()
                            if tables:
                                for table_num, table in enumerate(tables):
                                    table_text = self._table_to_text(table, page_num + 1, table_num + 1)
                                    text += f"\\n\\n--- TABLA {table_num + 1} (Página {page_num + 1}) ---\\n"
                                    text += table_text + "\\n"
                                    
                                    tables_info.append({
                                        'page': page_num + 1,
                                        'table_num': table_num + 1,
                                        'rows': len(table),
                                        'cols': len(table[0]) if table else 0
                                    })
                    
                    except Exception as e:
                        logger.warning(f"Error procesando página {page_num + 1}: {e}")
                        continue
                
                if tables_info:
                    metadata['tables'] = tables_info
                
                logger.info(f"✅ Texto extraído con pdfplumber: {len(text)} caracteres, {len(tables_info)} tablas")
                
        except Exception as e:
            logger.error(f"❌ Error procesando PDF con pdfplumber: {e}")
            raise
        
        return text, metadata
    
    def _clean_text(self, text: str) -> str:
        """
        Limpiar y normalizar texto extraído
        
        Args:
            text: Texto a limpiar
        
        Returns:
            Texto limpio
        """
        if not text:
            return ""
        
        # Normalizar espacios en blanco
        text = re.sub(r'\\s+', ' ', text)
        
        # Eliminar caracteres de control
        text = re.sub(r'[\\x00-\\x08\\x0B\\x0C\\x0E-\\x1F\\x7F]', '', text)
        
        # Normalizar saltos de línea
        text = re.sub(r'\\n\\s*\\n', '\\n\\n', text)
        
        # Eliminar espacios al inicio y final
        text = text.strip()
        
        return text
    
    def _table_to_text(self, table: List[List[str]], page_num: int, table_num: int) -> str:
        """
        Convertir tabla a texto estructurado
        
        Args:
            table: Tabla extraída
            page_num: Número de página
            table_num: Número de tabla
        
        Returns:
            Texto estructurado de la tabla
        """
        if not table:
            return ""
        
        text_lines = []
        
        for row_num, row in enumerate(table):
            if row and any(cell for cell in row if cell):  # Solo filas con contenido
                row_text = " | ".join(str(cell or "") for cell in row)
                text_lines.append(row_text)
        
        return "\\n".join(text_lines)
    
    def extract_text(self, pdf_path: str, method: str = 'pdfplumber') -> Tuple[str, Dict[str, Any]]:
        """
        Extraer texto del PDF usando el método especificado
        
        Args:
            pdf_path: Ruta al archivo PDF
            method: Método a usar ('pdfplumber' o 'pypdf2')
        
        Returns:
            Tupla con (texto_extraído, metadatos)
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Archivo PDF no encontrado: {pdf_path}")
        
        logger.info(f"📄 Procesando PDF: {os.path.basename(pdf_path)} con método {method}")
        
        if method == 'pdfplumber' and PDFPLUMBER_AVAILABLE:
            return self.extract_text_with_pdfplumber(pdf_path)
        elif method == 'pypdf2' and PYPDF2_AVAILABLE:
            return self.extract_text_with_pypdf2(pdf_path)
        elif PDFPLUMBER_AVAILABLE:
            logger.warning(f"Método {method} no disponible, usando pdfplumber")
            return self.extract_text_with_pdfplumber(pdf_path)
        elif PYPDF2_AVAILABLE:
            logger.warning(f"Método {method} no disponible, usando PyPDF2")
            return self.extract_text_with_pypdf2(pdf_path)
        else:
            raise ImportError("No hay librerías PDF disponibles. Instalar PyPDF2 y pdfplumber")
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Dividir texto en chunks para procesamiento RAG
        
        Args:
            text: Texto completo del documento
            metadata: Metadatos del documento
        
        Returns:
            Lista de chunks con metadatos
        """
        if not text.strip():
            return []
        
        chunks = []
        
        # Dividir por párrafos primero si se preserva estructura
        if self.preserve_structure:
            # Buscar divisiones naturales (páginas, secciones)
            sections = re.split(r'\\n\\n(?:===|---)', text)
            
            for section_num, section in enumerate(sections):
                section = section.strip()
                if not section:
                    continue
                
                # Dividir sección en chunks si es muy larga
                section_chunks = self._split_text_into_chunks(section)
                
                for chunk_num, chunk_text in enumerate(section_chunks):
                    chunk = {
                        'text': chunk_text,
                        'metadata': {
                            **metadata,
                            'chunk_id': len(chunks),
                            'section_num': section_num,
                            'chunk_num': chunk_num,
                            'total_chunks': len(section_chunks),
                            'char_count': len(chunk_text),
                            'word_count': len(chunk_text.split())
                        }
                    }
                    chunks.append(chunk)
        else:
            # División simple por tamaño
            text_chunks = self._split_text_into_chunks(text)
            
            for chunk_num, chunk_text in enumerate(text_chunks):
                chunk = {
                    'text': chunk_text,
                    'metadata': {
                        **metadata,
                        'chunk_id': chunk_num,
                        'total_chunks': len(text_chunks),
                        'char_count': len(chunk_text),
                        'word_count': len(chunk_text.split())
                    }
                }
                chunks.append(chunk)
        
        logger.info(f"📝 Texto dividido en {len(chunks)} chunks")
        return chunks
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """
        Dividir texto en chunks respetando límites de palabras
        
        Args:
            text: Texto a dividir
        
        Returns:
            Lista de chunks de texto
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end >= len(text):
                # Último chunk
                chunks.append(text[start:])
                break
            
            # Buscar un buen punto de corte (espacio o puntuación)
            cut_point = end
            for i in range(end, max(start + self.chunk_size - 200, start), -1):
                if text[i] in ' \\n.!?;':
                    cut_point = i + 1
                    break
            
            chunks.append(text[start:cut_point])
            start = cut_point - self.chunk_overlap
        
        return chunks
    
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Procesar completamente un archivo PDF
        
        Args:
            pdf_path: Ruta al archivo PDF
        
        Returns:
            Resultado completo del procesamiento
        """
        try:
            # Extraer texto y metadatos
            text, metadata = self.extract_text(pdf_path)
            
            if not text.strip():
                return {
                    "success": False,
                    "error": "No se pudo extraer texto del PDF",
                    "file_path": pdf_path
                }
            
            # Dividir en chunks
            chunks = self.chunk_text(text, metadata)
            
            result = {
                "success": True,
                "file_path": pdf_path,
                "file_name": os.path.basename(pdf_path),
                "text": text,
                "metadata": metadata,
                "chunks": chunks,
                "stats": {
                    "total_chars": len(text),
                    "total_words": len(text.split()),
                    "total_chunks": len(chunks),
                    "processing_method": "pdfplumber" if PDFPLUMBER_AVAILABLE else "pypdf2"
                }
            }
            
            logger.info(f"✅ PDF procesado exitosamente: {result['stats']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error procesando PDF {pdf_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": pdf_path
            }
    
    def get_supported_formats(self) -> List[str]:
        """Obtener formatos soportados"""
        return ['.pdf']
    
    def validate_pdf(self, pdf_path: str) -> bool:
        """
        Validar que el archivo PDF sea válido
        
        Args:
            pdf_path: Ruta al PDF
        
        Returns:
            True si es válido
        """
        if not os.path.exists(pdf_path):
            return False
        
        if not pdf_path.lower().endswith('.pdf'):
            return False
        
        try:
            if PDFPLUMBER_AVAILABLE:
                with pdfplumber.open(pdf_path) as pdf:
                    return len(pdf.pages) > 0
            elif PYPDF2_AVAILABLE:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    return len(pdf_reader.pages) > 0
            else:
                return False
        except Exception:
            return False