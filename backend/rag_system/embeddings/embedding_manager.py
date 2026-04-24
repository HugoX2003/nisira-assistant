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
    from sentence_transformers import SentenceTransformer  # type: ignore
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    SentenceTransformer = None  # type: ignore
    SENTENCE_TRANSFORMERS_AVAILABLE = False

if SENTENCE_TRANSFORMERS_AVAILABLE:
    class SentenceTransformerAdapter:
        """Envoltorio mínimo para usar SentenceTransformer como proveedor"""

        def __init__(self, model_name: str):
            self._model = SentenceTransformer(model_name, device='cpu')

        def embed_query(self, text: str):  # type: ignore[override]
            return self._model.encode(text, normalize_embeddings=True)

        def embed_documents(self, texts: List[str]):  # type: ignore[override]
            return self._model.encode(texts, normalize_embeddings=True)
else:
    SentenceTransformerAdapter = None  # type: ignore

try:
    from langchain_huggingface import HuggingFaceEmbeddings  # type: ignore
    HUGGINGFACE_BACKEND = "langchain_huggingface"
    HUGGINGFACE_AVAILABLE = True
except ImportError:  # pragma: no cover - fallback
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings  # type: ignore
        HUGGINGFACE_BACKEND = "langchain_community"
        HUGGINGFACE_AVAILABLE = True
    except ImportError:
        HuggingFaceEmbeddings = None  # type: ignore
        HUGGINGFACE_BACKEND = None
        HUGGINGFACE_AVAILABLE = False

try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings  # type: ignore
    GOOGLE_EMBEDDINGS_AVAILABLE = True
except ImportError:  # pragma: no cover
    GoogleGenerativeAIEmbeddings = None  # type: ignore
    GOOGLE_EMBEDDINGS_AVAILABLE = False

LANGCHAIN_AVAILABLE = HUGGINGFACE_AVAILABLE or GOOGLE_EMBEDDINGS_AVAILABLE or SENTENCE_TRANSFORMERS_AVAILABLE

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

    @staticmethod
    def _normalize_vector(vector: Any) -> Optional[List[float]]:
        """Convertir cualquier salida de embedding a lista de floats"""
        if vector is None:
            return None

        if isinstance(vector, list):
            return vector

        if hasattr(vector, "tolist"):
            try:
                return vector.tolist()
            except Exception:  # pragma: no cover - depende de backend
                pass

        try:
            return list(vector)
        except TypeError:  # pragma: no cover - tipos no iterables
            return None
    
    def _initialize_providers(self):
        """Inicializar proveedores de embeddings disponibles"""
        if not LANGCHAIN_AVAILABLE:
            logger.error("[ERROR] Ningún proveedor de embeddings está disponible (instala sentence-transformers o langchain-google-genai)")
            return
        
        self.available_providers = {}
        
        # Google Gemini (gratuito con límites)
        if GOOGLE_EMBEDDINGS_AVAILABLE and self.config['google_api_key']:
            try:
                self.available_providers['google'] = {
                    'name': 'Google Gemini',
                    'model': 'models/text-embedding-004',  # Modelo más reciente y potente
                    'max_tokens': 2048,
                    'rate_limit': 60,  # requests per minute
                    'free_quota': True
                }
                logger.info("[OK] Google Gemini disponible para embeddings (MODELO AVANZADO)")
            except Exception as e:
                logger.warning(f"[WARN]  Error configurando Google Gemini: {e}")
        
        # Hugging Face (gratuito, sin API key necesaria)
        if HUGGINGFACE_AVAILABLE or SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                backend = HUGGINGFACE_BACKEND or "sentence_transformers"
                self.available_providers['huggingface'] = {
                    'name': 'Hugging Face',
                    'model': 'sentence-transformers/all-mpnet-base-v2',  # EL MEJOR MODELO - 768 dimensiones
                    'max_tokens': 512,  # Máxima calidad
                    'rate_limit': None,  # Sin límite en modelo local
                    'free_quota': True,
                    'backend': backend
                }
                logger.info("[OK] Hugging Face disponible para embeddings (MÁXIMA CALIDAD - 768D)")
            except Exception as e:
                logger.warning(f"[WARN]  Error configurando Hugging Face: {e}")
        else:
            logger.warning("[WARN]  No se encontraron adaptadores de Hugging Face; instala sentence-transformers")
        
        # Seleccionar proveedor por defecto (preferir HuggingFace para ahorrar cuota de Google)
        if 'huggingface' in self.available_providers:
            self.current_provider = 'huggingface'
        elif 'google' in self.available_providers:
            self.current_provider = 'google'
        else:
            logger.error("[ERROR] No hay proveedores de embeddings disponibles")
    
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
                if not GOOGLE_EMBEDDINGS_AVAILABLE:
                    raise RuntimeError("Google Generative AI embeddings no disponibles: instala langchain-google-genai")
                model = GoogleGenerativeAIEmbeddings(
                    model=self.available_providers[provider]['model'],
                    google_api_key=self.config['google_api_key']
                )
            
            elif provider == 'huggingface':
                provider_info = self.available_providers.get(provider, {})

                if provider_info.get('backend') == "langchain_huggingface" and HUGGINGFACE_AVAILABLE and HuggingFaceEmbeddings is not None:
                    model = HuggingFaceEmbeddings(
                        model_name=provider_info.get('model'),
                        model_kwargs={'device': 'cpu'},
                        encode_kwargs={'normalize_embeddings': True}
                    )
                elif SENTENCE_TRANSFORMERS_AVAILABLE and SentenceTransformerAdapter is not None:
                    model = SentenceTransformerAdapter(provider_info.get('model'))
                    logger.info("[INFO]  Usando SentenceTransformer directo para embeddings Hugging Face")
                elif HUGGINGFACE_AVAILABLE and HuggingFaceEmbeddings is not None:
                    logger.warning("[WARN]  Usando backend langchain_community (deprecado); instala sentence-transformers para un adaptador nativo")
                    model = HuggingFaceEmbeddings(
                        model_name=provider_info.get('model'),
                        model_kwargs={'device': 'cpu'},
                        encode_kwargs={'normalize_embeddings': True}
                    )
                else:
                    raise RuntimeError("HuggingFaceEmbeddings no disponible: instala sentence-transformers")
            
            else:
                raise ValueError(f"Proveedor no soportado: {provider}")
            
            # Cachear modelo
            self.embedding_models[provider] = model
            logger.info(f"[OK] Modelo {provider} inicializado correctamente")
            
            return model
            
        except Exception as e:
            logger.error(f"[ERROR] Error inicializando modelo {provider}: {e}")
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
            logger.warning("[WARN]  Texto vacío, no se puede crear embedding")
            return None
        
        provider = provider or self.current_provider
        
        if not self.is_ready():
            logger.error("[ERROR] Sistema de embeddings no está listo")
            return None
        
        try:
            # Verificar cache
            text_hash = self._get_text_hash(text)
            cache_key = f"{provider}_{text_hash}"
            
            if cache_key in self.cache:
                logger.debug("[LIST] Embedding obtenido del cache")
                return self.cache[cache_key]
            
            # Truncar texto si es necesario
            processed_text = self._truncate_text(text, provider)
            
            # Obtener modelo
            model = self.get_embedding_model(provider)
            
            # Crear embedding
            embedding = model.embed_query(processed_text)
            embedding = self._normalize_vector(embedding)
            
            if embedding is None:
                logger.error("[ERROR] El backend de embeddings devolvió un resultado vacío")
                return None

            # Cachear resultado
            self.cache[cache_key] = embedding
            
            logger.debug(f"[OK] Embedding creado con {provider}: {len(embedding)} dimensiones")
            return embedding
            
        except Exception as e:
            logger.error(f"[ERROR] Error creando embedding con {provider}: {e}")
            
            # Intentar con otro proveedor si está disponible
            if provider != 'huggingface' and 'huggingface' in self.available_providers:
                logger.info("[SYNC] Intentando con Hugging Face como respaldo")
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
            logger.error("[ERROR] Sistema de embeddings no está listo")
            return [None] * len(texts)
        
        logger.info(f"[SYNC] Procesando {len(texts)} textos con {provider}")
        
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
                    normalized_batch = [self._normalize_vector(vec) for vec in batch_embeddings]
                    embeddings.extend(normalized_batch)
                    
                    # Log progreso detallado
                    progress = min(i + batch_size, len(processed_texts))
                    logger.info(f"[STATS] Embeddings 768D: {progress}/{len(processed_texts)} ({(progress/len(processed_texts)*100):.1f}%)")
                    
                    # Pequeña pausa para evitar sobrecarga
                    import time
                    time.sleep(0.1)
                
                # Cachear resultados
                for text, embedding in zip(texts, embeddings):
                    if embedding is None:
                        continue
                    text_hash = self._get_text_hash(text)
                    cache_key = f"{provider}_{text_hash}"
                    self.cache[cache_key] = embedding
                
                logger.info(f"[OK] {len(embeddings)} embeddings creados en mini-batches optimizados")
                return embeddings
                
            except Exception as e:
                logger.error(f"[ERROR] Error en procesamiento por lotes: {e}")
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
                    embeddings.append(self._normalize_vector(embedding))
                    
                    if (i + 1) % 10 == 0:
                        logger.info(f"[STATS] Progreso: {i + 1}/{len(texts)} embeddings")
                        
                except Exception as e:
                    logger.error(f"[ERROR] Error procesando texto {i}: {e}")
                    embeddings.append(None)
        
        successful = len([e for e in embeddings if e is not None])
        logger.info(f"[OK] Procesamiento completado: {successful}/{len(texts)} exitosos")
        
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
            logger.error(f"[ERROR] Error obteniendo dimensión: {e}")
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
            logger.warning("[WARN]  NumPy no disponible, usando cálculo básico")
            
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
            logger.error(f"[ERROR] Error calculando similitud: {e}")
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
            logger.error(f"[ERROR] Proveedor no disponible: {provider}")
            return False
        
        try:
            # Probar el proveedor
            test_model = self.get_embedding_model(provider)
            test_embedding = test_model.embed_query("test")
            
            if test_embedding:
                self.current_provider = provider
                logger.info(f"[OK] Proveedor cambiado a: {provider}")
                return True
            else:
                logger.error(f"[ERROR] Error probando proveedor: {provider}")
                return False
                
        except Exception as e:
            logger.error(f"[ERROR] Error cambiando a proveedor {provider}: {e}")
            return False
    
    def clear_cache(self):
        """Limpiar cache de embeddings"""
        self.cache.clear()
        logger.info("[CLEAN] Cache de embeddings limpiado")
    
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