"""
Sistema de Tracking de Métricas para Tesis
==========================================

Captura métricas de rendimiento y precisión en tiempo real
para análisis del sistema RAG.
"""

import os
import time
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from django.utils import timezone

from .models import QueryMetrics, RAGASMetrics
from .custom_evaluator import get_custom_evaluator

logger = logging.getLogger(__name__)


class MetricsTracker:
    """
    Clase para rastrear métricas de consultas en tiempo real
    """
    
    def __init__(self):
        self.query_id = str(uuid.uuid4())
        self.start_time = None
        self.first_token_time = None
        self.retrieval_start = None
        self.retrieval_end = None
        self.generation_start = None
        self.generation_end = None
        self.query_text = None
        self.documents_retrieved = 0
        self.top_k = None  # Se establecerá dinámicamente según la consulta
        
        # Para evaluación personalizada
        self.answer = None
        self.contexts = []
        self.custom_evaluator = get_custom_evaluator()
        
    def start_query(self, query_text: str, user=None, conversation=None):
        """Iniciar tracking de una nueva consulta"""
        self.start_time = time.time()
        self.query_text = query_text
        self.user = user
        self.conversation = conversation
        logger.info(f"[STATS] Iniciando tracking de métricas para query: {self.query_id[:8]}")
    
    def mark_first_token(self):
        """Marcar cuando se genera el primer token"""
        if self.start_time and not self.first_token_time:
            self.first_token_time = time.time()
            ttft = self.first_token_time - self.start_time
            logger.debug(f"[FAST] Time to First Token: {ttft:.3f}s")
    
    def start_retrieval(self):
        """Iniciar medición de tiempo de recuperación"""
        self.retrieval_start = time.time()
        logger.debug(f"[SEARCH] Iniciando recuperación de documentos")
    
    def end_retrieval(self, num_documents: int, k: int = 5):
        """Finalizar medición de recuperación"""
        if self.retrieval_start:
            self.retrieval_end = time.time()
            self.documents_retrieved = num_documents
            self.top_k = k
            retrieval_time = self.retrieval_end - self.retrieval_start
            logger.debug(f"[OK] Recuperación completada: {num_documents} docs en {retrieval_time:.3f}s")
    
    def start_generation(self):
        """Iniciar medición de tiempo de generación"""
        self.generation_start = time.time()
        logger.debug(f"[BRAIN] Iniciando generación de respuesta")
    
    def end_generation(self):
        """Finalizar medición de generación"""
        if self.generation_start:
            self.generation_end = time.time()
            generation_time = self.generation_end - self.generation_start
            logger.debug(f"[OK] Generación completada en {generation_time:.3f}s")
    
    def set_answer_and_contexts(self, answer: str, contexts: List[str]):
        """
        Guardar respuesta y contextos para evaluación de métricas
        
        Args:
            answer: La respuesta generada por el sistema
            contexts: Lista de fragmentos de texto recuperados
        """
        self.answer = answer
        self.contexts = contexts
        logger.debug(f"[NOTE] Guardado para evaluación: respuesta ({len(answer)} chars) y {len(contexts)} contextos")
    
    def is_complex_query(self, query_text: str) -> tuple:
        """
        Clasificar si una consulta es compleja
        
        Criterios:
        - Longitud > 100 caracteres
        - Múltiples preguntas (?, cuánto, cómo, por qué)
        - Palabras clave: "comparar", "diferencia", "analizar", "explicar detalladamente"
        
        Returns:
            (is_complex: bool, complexity_score: float)
        """
        score = 0.0
        
        # Longitud
        if len(query_text) > 100:
            score += 0.3
        elif len(query_text) > 50:
            score += 0.15
        
        # Múltiples preguntas
        question_marks = query_text.count('?')
        if question_marks > 1:
            score += 0.2
        
        # Palabras clave de complejidad
        complex_keywords = [
            'comparar', 'diferencia', 'analizar', 'explicar detalladamente',
            'por qué', 'cómo funciona', 'paso a paso', 'diferencias entre',
            'ventajas y desventajas', 'pros y contras'
        ]
        
        query_lower = query_text.lower()
        for keyword in complex_keywords:
            if keyword in query_lower:
                score += 0.15
        
        # Cláusula de normalización
        score = min(score, 1.0)
        
        is_complex = score > 0.5
        
        return is_complex, score
    
    def save_metrics(self) -> Optional[QueryMetrics]:
        """
        Guardar métricas en la base de datos
        
        Returns:
            QueryMetrics object si se guardó exitosamente, None en caso contrario
        """
        try:
            if not self.start_time:
                logger.warning("[WARN]  No se puede guardar métricas: no hay start_time")
                return None
            
            end_time = time.time()
            total_latency = end_time - self.start_time
            
            # Time to First Token
            if self.first_token_time:
                ttft = self.first_token_time - self.start_time
            else:
                ttft = total_latency  # Fallback
            
            # Retrieval time
            if self.retrieval_start and self.retrieval_end:
                retrieval_time = self.retrieval_end - self.retrieval_start
            else:
                retrieval_time = 0.0
            
            # Generation time
            if self.generation_start and self.generation_end:
                generation_time = self.generation_end - self.generation_start
            else:
                generation_time = total_latency - retrieval_time
            
            # Clasificar complejidad
            is_complex, complexity_score = self.is_complex_query(self.query_text or "")
            
            # Crear registro de métricas de rendimiento
            metrics = QueryMetrics.objects.create(
                query_id=self.query_id,
                user=self.user,
                conversation=self.conversation,
                query_text=self.query_text or "",
                total_latency=total_latency,
                time_to_first_token=ttft,
                retrieval_time=retrieval_time,
                generation_time=generation_time,
                is_complex_query=is_complex,
                query_complexity_score=complexity_score,
                documents_retrieved=self.documents_retrieved,
                top_k=self.top_k
            )
            
            logger.info(f"[OK] Métricas de rendimiento guardadas: {self.query_id[:8]} - {total_latency:.3f}s")
            
            # TIMESTAMPS DETALLADOS
            start_timestamp = datetime.fromtimestamp(self.start_time).isoformat()
            end_timestamp = datetime.fromtimestamp(end_time).isoformat()
            
            logger.info(f"\n" + "="*80)
            logger.info("⏱️  TIEMPOS DE RESPUESTA Y PROCESAMIENTO")
            logger.info("="*80)
            logger.info(f"Timestamp inicio: {start_timestamp}")
            logger.info(f"Timestamp fin: {end_timestamp}")
            logger.info(f"Tiempo transcurrido: {total_latency:.4f} segundos")
            logger.info(f"\nCálculo:")
            logger.info(f"  start_time = {self.start_time}")
            logger.info(f"  end_time = {end_time}")
            logger.info(f"  response_time = end_time - start_time")
            logger.info(f"  response_time = {end_time} - {self.start_time}")
            logger.info(f"  response_time = {total_latency:.4f}s")
            
            # Evaluar CALIDAD DE RESPUESTA con RAGAS si tenemos respuesta y contextos
            if self.answer and self.contexts:
                try:
                    # VELOCIDAD DE PROCESAMIENTO (tokens/segundo)
                    tokens_generados = len(self.answer.split())  # Aproximación: palabras como tokens
                    velocidad_procesamiento = tokens_generados / total_latency if total_latency > 0 else 0
                    
                    logger.info(f"\n[START] VELOCIDAD DE PROCESAMIENTO:")
                    logger.info(f"Tokens generados: {tokens_generados}")
                    logger.info(f"Tiempo total: {total_latency:.4f}s")
                    logger.info(f"Velocidad = tokens / tiempo")
                    logger.info(f"Velocidad = {tokens_generados} / {total_latency:.4f}")
                    logger.info(f"Velocidad = {velocidad_procesamiento:.2f} tokens/segundo")
                    logger.info("="*80 + "\n")
                    
                    # Verificar si RAGAS está habilitado (por defecto deshabilitado en producción para ahorrar cuota)
                    ragas_enabled = os.environ.get('RAGAS_ENABLED', 'false').lower() == 'true'
                    
                    # Importar y usar el evaluador RAGAS (si está disponible Y habilitado)
                    if ragas_enabled:
                        try:
                            from .ragas_evaluator import RAGASEvaluator
                            
                            logger.info(f"[SEARCH] Evaluando CALIDAD DE RESPUESTA con RAGAS...")
                            ragas_evaluator = RAGASEvaluator()
                            ragas_scores = ragas_evaluator.evaluate_response(
                                question=self.query_text or "",
                                answer=self.answer,
                                contexts=self.contexts,
                                ground_truth=None  # Opcional
                            )
                            
                            calidad_respuesta = ragas_scores.get('calidad_respuesta', 0.0)
                            faithfulness = ragas_scores.get('faithfulness', 0.0)
                            answer_relevancy = ragas_scores.get('answer_relevancy', 0.0)
                            context_precision = ragas_scores.get('context_precision', 0.0)
                        except ImportError as e:
                            logger.warning(f"[WARN] RAGAS no disponible (requiere git): {e}")
                            calidad_respuesta = 0.0
                            faithfulness = 0.0
                            answer_relevancy = 0.0
                            context_precision = 0.0
                        except Exception as e:
                            logger.warning(f"[WARN] Error en RAGAS (posible cuota excedida): {e}")
                            calidad_respuesta = 0.0
                            faithfulness = 0.0
                            answer_relevancy = 0.0
                            context_precision = 0.0
                    else:
                        logger.info("ℹ️ RAGAS deshabilitado (RAGAS_ENABLED=false). Respuestas más rápidas.")
                        calidad_respuesta = 0.0
                        faithfulness = 0.0
                        answer_relevancy = 0.0
                        context_precision = 0.0
                    
                    # Preparar datos para guardar MÉTRICAS RAGAS
                    metrics_data = {
                        'evaluation_id': str(uuid.uuid4()),
                        'query_metrics': metrics,
                        'query_text': self.query_text or "",
                        'response_text': self.answer[:500],
                        'retrieved_contexts': str(self.contexts[:3]) if self.contexts else "",
                        'precision_at_k': context_precision,  # Context Precision de RAGAS
                        'recall_at_k': 0.0,  # No usado
                        'faithfulness_score': faithfulness,
                        'answer_relevancy': answer_relevancy,
                        'wer_score': calidad_respuesta,  # Reusamos este campo para calidad_respuesta
                        'k_value': self.top_k or 5
                    }
                    
                    # Guardar métricas
                    ragas_metrics = RAGASMetrics.objects.create(**metrics_data)
                    
                    logger.info(f"\n[SAVE] RESUMEN DE MÉTRICAS GUARDADAS:")
                    logger.info(f"   ⏱️  Tiempo de respuesta: {total_latency:.4f}s")
                    logger.info(f"   [START] Velocidad de procesamiento: {velocidad_procesamiento:.2f} tokens/s")
                    logger.info(f"   [GOAL] Precision@{self.top_k}: {ragas_metrics.precision_at_k:.4f}")
                    logger.info(f"   [GOAL] Recall@{self.top_k}: {ragas_metrics.recall_at_k:.4f}\n")
                    
                except Exception as e:
                    logger.error(f"[ERROR] Error evaluando métricas personalizadas: {e}", exc_info=True)
            
            return metrics
            
        except Exception as e:
            logger.error(f"[ERROR] Error guardando métricas: {e}")
            return None
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtener resumen de las métricas actuales"""
        if not self.start_time:
            return {}
        
        end_time = time.time()
        total_latency = end_time - self.start_time
        
        return {
            "query_id": self.query_id,
            "total_latency": round(total_latency, 3),
            "time_to_first_token": round(self.first_token_time - self.start_time, 3) if self.first_token_time else None,
            "retrieval_time": round(self.retrieval_end - self.retrieval_start, 3) if self.retrieval_start and self.retrieval_end else None,
            "generation_time": round(self.generation_end - self.generation_start, 3) if self.generation_start and self.generation_end else None,
            "documents_retrieved": self.documents_retrieved
        }


def get_aggregated_metrics() -> Dict[str, Any]:
    """
    Obtener métricas agregadas de todas las consultas
    
    3 MÉTRICAS FINALES:
    1. Latencia Total: Tiempo de respuesta promedio (segundos)
    2. Reducción de Tiempo: Velocidad de procesamiento (tokens/segundo)
    3. Calidad de Respuesta: Score RAGAS promedio (0-1)
    
    Returns:
        Dict con promedios de las 3 métricas
    """
    try:
        # Importar aquí para evitar circular imports
        from django.db.models import Avg, Count
        
        # Métricas generales
        all_queries = QueryMetrics.objects.all()
        total_queries = all_queries.count()
        
        if total_queries == 0:
            return {
                "tiempoRespuesta": 0,
                "velocidadProcesamiento": 0,
                "calidadRespuesta": 0,
                "totalQueries": 0
            }
        
        # 1. LATENCIA TOTAL: Promedio de tiempo de respuesta
        avg_metrics = all_queries.aggregate(
            avg_latency=Avg('total_latency')
        )
        latencia_total = avg_metrics['avg_latency'] or 0
        
        # 2. REDUCCIÓN DE TIEMPO: Velocidad de procesamiento (tokens/segundo)
        # 3. CALIDAD DE RESPUESTA: Score RAGAS promedio
        ragas_metrics = RAGASMetrics.objects.all()
        ragas_count = ragas_metrics.count()
        
        velocidad_procesamiento = 0
        calidad_respuesta = 0
        
        if ragas_count > 0:
            # Calcular velocidad de procesamiento
            for ragas in ragas_metrics:
                if ragas.query_metrics:
                    tokens = len(ragas.response_text.split()) if ragas.response_text else 0
                    time_taken = ragas.query_metrics.total_latency
                    if time_taken > 0:
                        velocidad_procesamiento += tokens / time_taken
            velocidad_procesamiento = velocidad_procesamiento / ragas_count if ragas_count > 0 else 0
            
            # Calcular calidad de respuesta (reusamos el campo wer_score para calidad_respuesta)
            ragas_avg = ragas_metrics.aggregate(
                avg_calidad=Avg('wer_score')  # Este campo ahora guarda calidad_respuesta
            )
            calidad_respuesta = ragas_avg['avg_calidad'] or 0
        
        return {
            "tiempoRespuesta": round(latencia_total, 4),  # Segundos
            "velocidadProcesamiento": round(velocidad_procesamiento, 2),  # Tokens/segundo
            "calidadRespuesta": round(calidad_respuesta, 4),  # Score 0-1
            "totalQueries": total_queries
        }
        
    except Exception as e:
        logger.error(f"[ERROR] Error obteniendo métricas agregadas: {e}")
        return {
            "tiempoRespuesta": 0,
            "velocidadProcesamiento": 0,
            "precision": 0,
            "recall": 0,
            "totalQueries": 0
        }
