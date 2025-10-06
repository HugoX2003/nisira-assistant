"""
PDF Processor Avanzado con LangChain
===================================

Procesador PDF optimizado que usa LangChain para:
- Chunking inteligente con contexto semántico
- Preservación de estructura académica
- Extracción de metadatos enriquecidos
- Limpieza avanzada de texto
"""

import os
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders import PyPDFLoader
    from langchain.schema import Document
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    print(f"⚠️ Dependencias PDF no disponibles: {e}")
    
    # Definir Document como clase simple para evitar errores
    class Document:
        def __init__(self, page_content: str, metadata: dict = None):
            self.page_content = page_content
            self.metadata = metadata or {}

from ..config import DOCUMENT_PROCESSING_CONFIG

logger = logging.getLogger(__name__)

class PDFProcessor:
    """
    Procesador PDF avanzado con LangChain
    """
    
    def __init__(self):
        self.config = DOCUMENT_PROCESSING_CONFIG
        
        # Configuración optimizada para textos académicos y citas
        self.chunk_size = 2000   # CHUNKS MÁS GRANDES para capturar CONTEXTO COMPLETO
        self.chunk_overlap = 600  # OVERLAP MAYOR para asegurar continuidad total
        self.min_chunk_size = 200  # Chunks mínimos más grandes
        
        # Text splitter inteligente con LangChain
        if DEPENDENCIES_AVAILABLE:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                separators=[
                    "\n\n\n",  # Separadores de sección
                    "\n\n",    # Párrafos
                    "\n",      # Líneas
                    ". ",      # Oraciones
                    ".",       # Puntos
                    " ",       # Espacios
                    ""         # Caracteres
                ]
            )
        
    def is_available(self) -> bool:
        """Verificar disponibilidad"""
        return DEPENDENCIES_AVAILABLE

    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Procesar PDF con LangChain y técnicas avanzadas
        
        Args:
            pdf_path: Ruta al archivo PDF
        
        Returns:
            Diccionario con texto procesado, chunks y metadatos
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "Dependencias PDF no disponibles"
            }
        
        if not os.path.exists(pdf_path):
            return {
                "success": False,
                "error": f"Archivo no encontrado: {pdf_path}"
            }
        
        try:
            filename = os.path.basename(pdf_path)
            logger.info(f"📄 Procesando PDF: {filename}")
            
            # 1. Cargar documento con LangChain - CON MANEJO DE ERRORES Y EXTRACCIÓN MEJORADA
            try:
                # Usar múltiples métodos de extracción para máxima calidad
                loader = PyPDFLoader(pdf_path)
                
                # Configurar extracción optimizada
                loader.extraction_mode = "layout"  # Preservar layout para mejor calidad
                documents = loader.load()
                
                # Si PyPDF falla, intentar con extracción alternativa
                if not documents or all(len(doc.page_content.strip()) < 50 for doc in documents):
                    logger.warning(f"⚠️ Extracción pobre con PyPDF, intentando método alternativo para {filename}")
                    documents = self._extract_with_fallback(pdf_path)
                    
            except Exception as pdf_error:
                logger.error(f"❌ Error cargando PDF {filename}: {pdf_error}")
                # Intentar método de fallback
                try:
                    logger.info(f"🔄 Intentando extracción alternativa para {filename}")
                    documents = self._extract_with_fallback(pdf_path)
                except Exception as fallback_error:
                    logger.error(f"❌ Extracción alternativa también falló: {fallback_error}")
                    return {
                        "success": False,
                        "error": f"Error al cargar PDF: {pdf_error}",
                        "file": filename
                    }
            
            if not documents:
                logger.warning(f"⚠️ PDF vacío: {filename}")
                return {
                    "success": False,
                    "error": "PDF vacío o sin contenido extraíble",
                    "file": filename
                }
            
            # 2. Limpiar y enriquecer texto - SIMPLIFICADO PARA VELOCIDAD
            cleaned_docs = []
            for i, doc in enumerate(documents):
                # LIMPIEZA BÁSICA Y RÁPIDA
                cleaned_text = doc.page_content.strip()
                
                # Solo limpieza esencial
                cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # Normalizar espacios
                cleaned_text = re.sub(r'\n+', '\n', cleaned_text)  # Normalizar saltos
                
                if len(cleaned_text) < 50:  # Saltar páginas muy cortas
                    continue
                
                # Metadatos básicos
                metadata = {
                    'source': filename,
                    'page': i + 1,
                    'total_pages': len(documents),
                    'file_path': pdf_path,
                    'chunk_type': 'page_content',
                    'word_count': len(cleaned_text.split()),
                    'char_count': len(cleaned_text),
                    'document': filename
                }
                
                cleaned_docs.append(Document(
                    page_content=cleaned_text,
                    metadata=metadata
                ))
            
            # 3. Chunking inteligente con LangChain
            chunks = self.text_splitter.split_documents(cleaned_docs)
            
            # 4. Post-procesar chunks
            processed_chunks = []
            for i, chunk in enumerate(chunks):
                # Filtrar chunks muy pequeños o irrelevantes
                if len(chunk.page_content.strip()) < self.min_chunk_size:
                    continue
                
                # Enriquecer metadatos del chunk
                chunk.metadata.update({
                    'chunk_id': i,
                    'chunk_size': len(chunk.page_content),
                    'document': filename
                })
                
                # Formato para ChromaDB
                chunk_data = {
                    'text': chunk.page_content.strip(),
                    'metadata': chunk.metadata
                }
                
                processed_chunks.append(chunk_data)
            
            logger.info(f"✅ Procesado: {len(processed_chunks)} chunks de {len(documents)} páginas")
            
            # 5. Estadísticas
            total_chars = sum(len(chunk['text']) for chunk in processed_chunks)
            total_words = sum(len(chunk['text'].split()) for chunk in processed_chunks)
            
            return {
                "success": True,
                "chunks": processed_chunks,
                "stats": {
                    "total_pages": len(documents),
                    "total_chunks": len(processed_chunks),
                    "total_chars": total_chars,
                    "total_words": total_words,
                    "avg_chunk_size": total_chars // len(processed_chunks) if processed_chunks else 0,
                    "processing_method": "langchain_advanced"
                },
                "metadata": {
                    "filename": filename,
                    "file_path": pdf_path,
                    "processing_config": {
                        "chunk_size": self.chunk_size,
                        "chunk_overlap": self.chunk_overlap,
                        "min_chunk_size": self.min_chunk_size
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error procesando PDF {pdf_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": pdf_path
            }
    
    def _clean_and_enrich_text(self, text: str) -> str:
        """
        Limpiar y enriquecer texto extraído con énfasis en preservar citas
        """
        if not text or not text.strip():
            return ""
        
        # 1. Preservar citas bibliográficas antes de limpiar
        text = self._preserve_citations(text)
        
        # 2. Normalizar espacios en blanco
        text = re.sub(r'\s+', ' ', text)
        
        # 3. Remover caracteres extraños pero preservar estructura y citas
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\(\)\-\"\'\n\u00C0-\u017F]', '', text)
        
        # 4. Mejorar formato de párrafos
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # 5. Corregir puntuación separada
        text = re.sub(r'\s+([\.,:;!?])', r'\1', text)
        
        # 6. Preservar estructura de listas y numeración
        text = re.sub(r'\n\s*(\d+[\.\)])', r'\n\1', text)
        text = re.sub(r'\n\s*([a-zA-Z][\.\)])', r'\n\1', text)
        
        return text.strip()
    
    def _preserve_citations(self, text: str) -> str:
        """
        Preservar y mejorar citas bibliográficas en el texto
        """
        # Patrones de citas bibliográficas comunes
        citation_patterns = [
            # Autor(año): Arias(2020), García(2019)
            (r'([A-Z][a-záéíóúñü]+)\s*\(\s*(\d{4})\s*\)', r'\1 (\2)'),
            # Según Autor (año): Según Arias (2020)
            (r'(según|de acuerdo a|como menciona|como indica)\s+([A-Z][a-záéíóúñü]+)\s*\(\s*(\d{4})\s*\)', 
             r'\1 \2 (\3)'),
            # Multiple authors: Arias et al. (2020)
            (r'([A-Z][a-záéíóúñü]+)\s+et\s+al\.\s*\(\s*(\d{4})\s*\)', r'\1 et al. (\2)'),
            # Citation with page: Arias (2020, p. 45)
            (r'([A-Z][a-záéíóúñü]+)\s*\(\s*(\d{4})\s*,\s*p\.\s*(\d+)\s*\)', r'\1 (\2, p. \3)')
        ]
        
        for pattern, replacement in citation_patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def _detect_sections(self, text: str) -> Dict[str, Any]:
        """
        Detectar secciones especiales en el texto incluyendo citas
        """
        sections = {
            'has_title': False,
            'has_author': False,
            'has_references': False,
            'has_conclusions': False,
            'has_citations': False,
            'section_type': 'content'
        }
        
        text_lower = text.lower()
        
        # Detectar títulos (texto en mayúsculas al inicio)
        if re.match(r'^[A-ZÁÉÍÓÚÑ\s]{10,}', text[:100]):
            sections['has_title'] = True
            sections['section_type'] = 'title'
        
        # Detectar autores
        author_patterns = [
            r'por:?\s+[A-Z][a-z]+\s+[A-Z]',
            r'autor:?\s+[A-Z]',
            r'^[A-Z][a-z]+\s+[A-Z][a-z]+(\s+[A-Z][a-z]+)?$'
        ]
        if any(re.search(pattern, text[:200], re.IGNORECASE) for pattern in author_patterns):
            sections['has_author'] = True
        
        # Detectar citas bibliográficas
        citation_patterns = [
            r'[A-Z][a-záéíóúñü]+\s*\(\s*\d{4}\s*\)',  # Autor(año)
            r'según\s+[A-Z][a-záéíóúñü]+\s*\(\s*\d{4}\s*\)',  # según Autor(año)
            r'[A-Z][a-záéíóúñü]+\s+et\s+al\.\s*\(\s*\d{4}\s*\)'  # Autor et al.(año)
        ]
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in citation_patterns):
            sections['has_citations'] = True
        
        # Detectar referencias/bibliografía
        ref_keywords = ['referencias', 'bibliografía', 'bibliography', 'works cited']
        if any(keyword in text_lower[:100] for keyword in ref_keywords):
            sections['has_references'] = True
            sections['section_type'] = 'references'
        
        # Detectar conclusiones
        conclusion_keywords = ['conclusión', 'conclusiones', 'summary', 'resumen']
        if any(keyword in text_lower[:100] for keyword in conclusion_keywords):
            sections['has_conclusions'] = True
            sections['section_type'] = 'conclusions'
        
        return sections
    
    def _extract_with_fallback(self, pdf_path: str) -> List[Document]:
        """
        Método de extracción alternativo cuando PyPDF falla
        """
        try:
            # Método 1: Usar pdfplumber si está disponible
            try:
                import pdfplumber
                documents = []
                
                with pdfplumber.open(pdf_path) as pdf:
                    for page_num, page in enumerate(pdf.pages):
                        text = page.extract_text()
                        if text and text.strip():
                            doc = Document(
                                page_content=text,
                                metadata={
                                    'source': os.path.basename(pdf_path),
                                    'page': page_num + 1
                                }
                            )
                            documents.append(doc)
                
                if documents:
                    logger.info(f"✅ Extracción exitosa con pdfplumber: {len(documents)} páginas")
                    return documents
                    
            except ImportError:
                logger.warning("pdfplumber no disponible, usando método básico")
            
            # Método 2: Usar PyPDF2 básico con configuración alternativa
            try:
                import PyPDF2
                documents = []
                
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    
                    for page_num, page in enumerate(pdf_reader.pages):
                        text = page.extract_text()
                        
                        # Limpiar texto extraído
                        if text and text.strip():
                            # Aplicar limpieza adicional
                            text = re.sub(r'\s+', ' ', text)  # Normalizar espacios
                            text = text.strip()
                            
                            if len(text) > 20:  # Solo páginas con contenido significativo
                                doc = Document(
                                    page_content=text,
                                    metadata={
                                        'source': os.path.basename(pdf_path),
                                        'page': page_num + 1
                                    }
                                )
                                documents.append(doc)
                
                if documents:
                    logger.info(f"✅ Extracción exitosa con PyPDF2: {len(documents)} páginas")
                    return documents
                    
            except Exception as e:
                logger.warning(f"PyPDF2 también falló: {e}")
            
            # Método 3: Último recurso - crear documento vacío con metadatos
            logger.warning(f"Todos los métodos de extracción fallaron para {pdf_path}")
            return [Document(
                page_content="[Contenido no extraíble - PDF problemático]",
                metadata={
                    'source': os.path.basename(pdf_path),
                    'page': 1,
                    'extraction_error': True
                }
            )]
            
        except Exception as e:
            logger.error(f"Error en extracción alternativa: {e}")
            return []