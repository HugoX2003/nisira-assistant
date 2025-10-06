"""
Embedding Manager
================

Gestor de embeddings que utiliza LangChain con APIs gratuitas
como Google Gemini y Hugging Face para crear vectores de documentos.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
import hashlib

try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

from ..config import API_CONFIG

logger = logging.getLogger(__name__)

class EmbeddingManager:
    """
    Gestor de embeddings con múltiples proveedores
    """
    
    def __init__(self):
        self.config = API_CONFIG
        self.embedding_models = {}
        self.current_provider = None
        self.cache = {}  # Cache local para embeddings
        
        # Configurar proveedores disponibles
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Inicializar proveedores de embeddings disponibles"""
        if not LANGCHAIN_AVAILABLE:
            logger.error("❌ LangChain no está disponible")
            return
        
        self.available_providers = {}
        
        # Google Gemini (gratuito con límites)
        if self.config['google_api_key']:
            try:
                self.available_providers['google'] = {
                    'name': 'Google Gemini',
                    'model': 'models/text-embedding-004',  # Modelo más reciente y potente
                    'max_tokens': 2048,
                    'rate_limit': 60,  # requests per minute
                    'free_quota': True
                }
                logger.info("✅ Google Gemini disponible para embeddings (MODELO AVANZADO)")
            except Exception as e:
                logger.warning(f"⚠️  Error configurando Google Gemini: {e}")
        
        # Hugging Face (gratuito, sin API key necesaria)
        try:
            self.available_providers['huggingface'] = {
                'name': 'Hugging Face',
                'model': 'sentence-transformers/all-mpnet-base-v2',  # EL MEJOR MODELO - 768 dimensiones
                'max_tokens': 512,  # Máxima calidad
                'rate_limit': None,  # Sin límite en modelo local
                'free_quota': True
            }
            logger.info("✅ Hugging Face disponible para embeddings (MÁXIMA CALIDAD - 768D)")
        except Exception as e:
            logger.warning(f"⚠️  Error configurando Hugging Face: {e}")
        
        # Seleccionar proveedor por defecto (preferir HuggingFace para ahorrar cuota de Google)
        if 'huggingface' in self.available_providers:
            self.current_provider = 'huggingface'
        elif 'google' in self.available_providers:
            self.current_provider = 'google'
        else:
            logger.error("❌ No hay proveedores de embeddings disponibles")
    
    def is_ready(self) -> bool:
        """Verificar si el sistema está listo para generar embeddings"""
        return (
            LANGCHAIN_AVAILABLE and 
            len(self.available_providers) > 0 and 
            self.current_provider is not None
        )
    
    def get_embedding_model(self, provider: Optional[str] = None):
        """
        Obtener modelo de embeddings
        
        Args:
            provider: Proveedor específico ('google', 'huggingface')
        
        Returns:
            Modelo de embeddings inicializado
        """
        provider = provider or self.current_provider
        
        if not provider or provider not in self.available_providers:
            raise ValueError(f"Proveedor no disponible: {provider}")
        
        # Usar cache si ya está inicializado
        if provider in self.embedding_models:
            return self.embedding_models[provider]
        
        try:
            if provider == 'google':
                model = GoogleGenerativeAIEmbeddings(
                    model=self.available_providers[provider]['model'],
                    google_api_key=self.config['google_api_key']
                )
            
            elif provider == 'huggingface':
                model = HuggingFaceEmbeddings(
                    model_name=self.available_providers[provider]['model'],
                    model_kwargs={'device': 'cpu'},  # Usar CPU para compatibilidad
                    encode_kwargs={'normalize_embeddings': True}
                )
            
            else:
                raise ValueError(f"Proveedor no soportado: {provider}")
            
            # Cachear modelo
            self.embedding_models[provider] = model
            logger.info(f"✅ Modelo {provider} inicializado correctamente")
            
            return model
            
        except Exception as e:
            logger.error(f"❌ Error inicializando modelo {provider}: {e}")
            raise
    
    def _get_text_hash(self, text: str) -> str:
        """Generar hash para cachear embeddings"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _truncate_text(self, text: str, provider: str) -> str:
        """
        Truncar texto según límites del proveedor
        
        Args:
            text: Texto a truncar
            provider: Proveedor de embeddings
        
        Returns:
            Texto truncado
        """
        max_tokens = self.available_providers[provider]['max_tokens']
        
        # Estimación aproximada: 1 token ≈ 4 caracteres
        max_chars = max_tokens * 4
        
        if len(text) <= max_chars:
            return text
        
        # Truncar respetando palabras
        truncated = text[:max_chars]
        last_space = truncated.rfind(' ')
        
        if last_space > max_chars * 0.8:  # Si el último espacio está cerca del final
            truncated = truncated[:last_space]
        
        logger.debug(f"Texto truncado de {len(text)} a {len(truncated)} caracteres")
        return truncated
    
    def create_embedding(self, text: str, provider: Optional[str] = None) -> Optional[List[float]]:
        """
        Crear embedding para un texto
        
        Args:
            text: Texto a procesar
            provider: Proveedor específico
        
        Returns:
            Vector de embedding o None si falló
        """
        if not text.strip():
            logger.warning("⚠️  Texto vacío, no se puede crear embedding")
            return None
        
        provider = provider or self.current_provider
        
        if not self.is_ready():
            logger.error("❌ Sistema de embeddings no está listo")
            return None
        
        try:
            # Verificar cache
            text_hash = self._get_text_hash(text)
            cache_key = f"{provider}_{text_hash}"
            
            if cache_key in self.cache:
                logger.debug("📋 Embedding obtenido del cache")
                return self.cache[cache_key]
            
            # Truncar texto si es necesario
            processed_text = self._truncate_text(text, provider)
            
            # Obtener modelo
            model = self.get_embedding_model(provider)
            
            # Crear embedding
            embedding = model.embed_query(processed_text)
            
            # Cachear resultado
            self.cache[cache_key] = embedding
            
            logger.debug(f"✅ Embedding creado con {provider}: {len(embedding)} dimensiones")
            return embedding
            
        except Exception as e:
            logger.error(f"❌ Error creando embedding con {provider}: {e}")
            
            # Intentar con otro proveedor si está disponible
            if provider != 'huggingface' and 'huggingface' in self.available_providers:
                logger.info("🔄 Intentando con Hugging Face como respaldo")
                return self.create_embedding(text, 'huggingface')
            
            return None
    
    def create_embeddings_batch(self, texts: List[str], provider: Optional[str] = None, 
                               max_workers: int = 4) -> List[Optional[List[float]]]:
        """
        Crear embeddings para múltiples textos en paralelo
        
        Args:
            texts: Lista de textos
            provider: Proveedor específico
            max_workers: Número máximo de hilos paralelos
        
        Returns:
            Lista de embeddings
        """
        if not texts:
            return []
        
        provider = provider or self.current_provider
        
        if not self.is_ready():
            logger.error("❌ Sistema de embeddings no está listo")
            return [None] * len(texts)
        
        logger.info(f"🔄 Procesando {len(texts)} textos con {provider}")
        
        # Para Hugging Face, usar procesamiento por lotes OPTIMIZADO
        if provider == 'huggingface':
            try:
                model = self.get_embedding_model(provider)
                
                # Procesar textos
                processed_texts = [self._truncate_text(text, provider) for text in texts]
                
                # PROCESAMIENTO EN MINI-BATCHES SÚPER OPTIMIZADO para all-mpnet-base-v2
                embeddings = []
                batch_size = 4  # Batches MUY pequeños para modelo pesado (768D)
                
                for i in range(0, len(processed_texts), batch_size):
                    batch = processed_texts[i:i + batch_size]
                    
                    # Crear embeddings para este mini-batch
                    batch_embeddings = model.embed_documents(batch)
                    embeddings.extend(batch_embeddings)
                    
                    # Log progreso detallado
                    progress = min(i + batch_size, len(processed_texts))
                    logger.info(f"📊 Embeddings 768D: {progress}/{len(processed_texts)} ({(progress/len(processed_texts)*100):.1f}%)")
                    
                    # Pequeña pausa para evitar sobrecarga
                    import time
                    time.sleep(0.1)
                
                # Cachear resultados
                for text, embedding in zip(texts, embeddings):
                    text_hash = self._get_text_hash(text)
                    cache_key = f"{provider}_{text_hash}"
                    self.cache[cache_key] = embedding
                
                logger.info(f"✅ {len(embeddings)} embeddings creados en mini-batches optimizados")
                return embeddings
                
            except Exception as e:
                logger.error(f"❌ Error en procesamiento por lotes: {e}")
                # Fallar al procesamiento individual
        
        # Procesamiento individual con hilos paralelos
        def create_single_embedding(text):
            return self.create_embedding(text, provider)
        
        embeddings = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Enviar tareas
            futures = [executor.submit(create_single_embedding, text) for text in texts]
            
            # Recopilar resultados
            for i, future in enumerate(futures):
                try:
                    embedding = future.result(timeout=30)  # 30 segundos timeout
                    embeddings.append(embedding)
                    
                    if (i + 1) % 10 == 0:
                        logger.info(f"📊 Progreso: {i + 1}/{len(texts)} embeddings")
                        
                except Exception as e:
                    logger.error(f"❌ Error procesando texto {i}: {e}")
                    embeddings.append(None)
        
        successful = len([e for e in embeddings if e is not None])
        logger.info(f"✅ Procesamiento completado: {successful}/{len(texts)} exitosos")
        
        return embeddings
    
    def get_embedding_dimension(self, provider: Optional[str] = None) -> int:
        """
        Obtener dimensión de los embeddings
        
        Args:
            provider: Proveedor específico
        
        Returns:
            Número de dimensiones
        """
        provider = provider or self.current_provider
        
        if not self.is_ready():
            return 0
        
        try:
            # Crear embedding de prueba
            test_embedding = self.create_embedding("test", provider)
            
            if test_embedding:
                return len(test_embedding)
            else:
                return 0
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo dimensión: {e}")
            return 0
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calcular similitud coseno entre dos embeddings
        
        Args:
            embedding1: Primer embedding
            embedding2: Segundo embedding
        
        Returns:
            Similitud coseno (0-1)
        """
        if not NUMPY_AVAILABLE:
            logger.warning("⚠️  NumPy no disponible, usando cálculo básico")
            
            # Cálculo manual de similitud coseno
            dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
            magnitude1 = sum(a * a for a in embedding1) ** 0.5
            magnitude2 = sum(b * b for b in embedding2) ** 0.5
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
                
            return dot_product / (magnitude1 * magnitude2)
        
        try:
            # Usar NumPy para cálculo eficiente
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Similitud coseno
            similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"❌ Error calculando similitud: {e}")
            return 0.0
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Obtener información sobre proveedores disponibles
        
        Returns:
            Información detallada de proveedores
        """
        return {
            'current_provider': self.current_provider,
            'available_providers': self.available_providers,
            'system_ready': self.is_ready(),
            'cache_size': len(self.cache),
            'langchain_available': LANGCHAIN_AVAILABLE,
            'numpy_available': NUMPY_AVAILABLE
        }
    
    def switch_provider(self, provider: str) -> bool:
        """
        Cambiar proveedor de embeddings
        
        Args:
            provider: Nuevo proveedor
        
        Returns:
            True si el cambio fue exitoso
        """
        if provider not in self.available_providers:
            logger.error(f"❌ Proveedor no disponible: {provider}")
            return False
        
        try:
            # Probar el proveedor
            test_model = self.get_embedding_model(provider)
            test_embedding = test_model.embed_query("test")
            
            if test_embedding:
                self.current_provider = provider
                logger.info(f"✅ Proveedor cambiado a: {provider}")
                return True
            else:
                logger.error(f"❌ Error probando proveedor: {provider}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error cambiando a proveedor {provider}: {e}")
            return False
    
    def clear_cache(self):
        """Limpiar cache de embeddings"""
        self.cache.clear()
        logger.info("🧹 Cache de embeddings limpiado")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del sistema
        
        Returns:
            Estadísticas detalladas
        """
        stats = {
            'ready': self.is_ready(),
            'current_provider': self.current_provider,
            'providers_available': len(self.available_providers),
            'cache_entries': len(self.cache),
            'embedding_dimension': self.get_embedding_dimension()
        }
        
        if self.current_provider:
            provider_info = self.available_providers[self.current_provider]
            stats['current_model'] = provider_info['model']
            stats['max_tokens'] = provider_info['max_tokens']
            stats['free_quota'] = provider_info['free_quota']
        
        return stats