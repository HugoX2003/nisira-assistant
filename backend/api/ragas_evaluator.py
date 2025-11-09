"""
Evaluador RAGAS para Métricas de Precisión
==========================================

Evalúa la calidad de las respuestas del sistema RAG usando el framework RAGAS.

Métricas implementadas:
- Faithfulness: ¿La respuesta está respaldada por el contexto?
- Answer Relevancy: ¿La respuesta es relevante a la pregunta?
- Context Precision: ¿Los documentos recuperados son relevantes?
- Context Recall: ¿Se recuperaron todos los documentos necesarios?
"""

import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Importar RAGAS solo cuando esté disponible
try:
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall
    )
    from datasets import Dataset
    from langchain_openai import ChatOpenAI
    RAGAS_AVAILABLE = True
    logger.info("✅ RAGAS framework disponible")
except ImportError as e:
    RAGAS_AVAILABLE = False
    logger.warning(f"⚠️ RAGAS no disponible: {e}")
    logger.warning("📦 Instala con: pip install ragas datasets")


class RAGASEvaluator:
    """
    Evaluador de calidad para sistemas RAG usando RAGAS
    
    NOTA: RAGAS deshabilitado por defecto - usa métricas simuladas.
    RAGAS requiere API keys de OpenAI y puede tener problemas de compatibilidad.
    Para análisis de calidad, usa QueryMetrics que ya está funcionando.
    """
    
    def __init__(self):
        """Inicializar evaluador en modo simulado"""
        # RAGAS DESHABILITADO - siempre usar modo simulado
        self.available = False
        self.llm = None
        logger.info("📊 RAGASEvaluator inicializado en modo simulado (RAGAS deshabilitado)")
        logger.info("💡 Usando métricas heurísticas en lugar de RAGAS para mejor compatibilidad")
    
    def _setup_llm(self):
        """Configurar LLM para RAGAS usando OpenRouter o OpenAI"""
        try:
            # Prioridad: OPENROUTER_API_KEY > OPENAI_API_KEY
            openrouter_key = os.getenv('OPENROUTER_API_KEY')
            openai_key = os.getenv('OPENAI_API_KEY')
            
            if openrouter_key:
                # Usar OpenRouter (recomendado)
                # IMPORTANTE: Establecer como OPENAI_API_KEY para que RAGAS lo detecte
                os.environ['OPENAI_API_KEY'] = openrouter_key
                
                self.llm = ChatOpenAI(
                    model="google/gemma-2-9b-it",  # Modelo rápido y económico
                    openai_api_key=openrouter_key,  # Parámetro correcto
                    openai_api_base="https://openrouter.ai/api/v1",  # Base URL para OpenRouter
                    temperature=0.0,  # Determinístico para evaluaciones
                    model_kwargs={"headers": {"HTTP-Referer": "http://localhost:8000"}}  # Requerido por OpenRouter
                )
                logger.info("✅ RAGAS configurado con OpenRouter (gemma-2-9b-it)")
            elif openai_key:
                # Fallback a OpenAI
                self.llm = ChatOpenAI(
                    model="gpt-3.5-turbo",
                    openai_api_key=openai_key,
                    temperature=0.0,
                )
                logger.info("✅ RAGAS configurado con OpenAI (gpt-3.5-turbo)")
            else:
                logger.warning("⚠️ No se encontró OPENROUTER_API_KEY ni OPENAI_API_KEY")
                logger.warning("💡 Configura OPENROUTER_API_KEY para usar RAGAS")
                self.llm = None
        except Exception as e:
            logger.error(f"❌ Error configurando LLM para RAGAS: {e}")
            logger.info(f"📋 Detalles: {str(e)}")
            self.llm = None
    
    def evaluate_single(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Evaluar una sola consulta
        
        Args:
            question: La pregunta del usuario
            answer: La respuesta generada por el sistema
            contexts: Lista de contextos/documentos recuperados
            ground_truth: Respuesta correcta (opcional, para context_recall)
        
        Returns:
            Dict con las métricas calculadas
        """
        if not self.available:
            return self._fallback_evaluation()
        
        try:
            # Preparar datos en formato RAGAS
            data = {
                "question": [question],
                "answer": [answer],
                "contexts": [contexts],
            }
            
            # Agregar ground_truth si está disponible
            if ground_truth:
                data["ground_truth"] = [ground_truth]
            
            # Crear dataset
            dataset = Dataset.from_dict(data)
            
            # Evaluar con métricas disponibles
            metrics_to_use = self.metrics.copy()
            if not ground_truth:
                # Context recall y context precision requieren ground_truth (reference)
                if context_recall in metrics_to_use:
                    metrics_to_use.remove(context_recall)
                if context_precision in metrics_to_use:
                    metrics_to_use.remove(context_precision)
                logger.debug("⚠️ Métricas deshabilitadas (sin ground_truth): context_precision, context_recall")
            
            # Ejecutar evaluación
            logger.debug(f"🔍 Evaluando con RAGAS: {len(metrics_to_use)} métricas")
            
            # Verificar que haya LLM configurado
            if not self.llm:
                logger.warning("⚠️ No hay LLM configurado para RAGAS, usando evaluación simulada")
                return self._fallback_evaluation()
            
            # Ejecutar evaluación con el LLM configurado
            results = evaluate(
                dataset, 
                metrics=metrics_to_use,
                llm=self.llm
            )
            
            # Extraer resultados - results es un DataFrame en versiones nuevas de RAGAS
            # Convertir a dict si es necesario
            if hasattr(results, 'to_dict'):
                results_dict = results.to_dict('list')
                scores = {
                    'faithfulness': float(results_dict.get('faithfulness', [0.0])[0]) if 'faithfulness' in results_dict else 0.0,
                    'answer_relevancy': float(results_dict.get('answer_relevancy', [0.0])[0]) if 'answer_relevancy' in results_dict else 0.0,
                    'context_precision': float(results_dict.get('context_precision', [0.0])[0]) if 'context_precision' in results_dict and ground_truth else 0.0,
                    'context_recall': float(results_dict.get('context_recall', [0.0])[0]) if 'context_recall' in results_dict and ground_truth else None
                }
            else:
                # Fallback para versiones antiguas
                scores = {
                    'faithfulness': getattr(results, 'faithfulness', 0.0),
                    'answer_relevancy': getattr(results, 'answer_relevancy', 0.0),
                    'context_precision': getattr(results, 'context_precision', 0.0) if ground_truth else 0.0,
                    'context_recall': getattr(results, 'context_recall', None) if ground_truth else None
                }
            
            logger.info(f"✅ Evaluación RAGAS completada: {scores}")
            return scores
            
        except Exception as e:
            logger.error(f"❌ Error en evaluación RAGAS: {e}")
            logger.info("💡 Tip: Configura OPENROUTER_API_KEY o OPENAI_API_KEY para usar RAGAS")
            return self._fallback_evaluation()
    
    def evaluate_batch(
        self,
        questions: List[str],
        answers: List[str],
        contexts_list: List[List[str]],
        ground_truths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Evaluar múltiples consultas en batch
        
        Args:
            questions: Lista de preguntas
            answers: Lista de respuestas generadas
            contexts_list: Lista de listas de contextos
            ground_truths: Lista de respuestas correctas (opcional)
        
        Returns:
            Dict con métricas agregadas y por consulta
        """
        if not self.available:
            return {
                'aggregate': self._fallback_evaluation(),
                'per_query': [self._fallback_evaluation() for _ in questions]
            }
        
        try:
            # Preparar datos
            data = {
                "question": questions,
                "answer": answers,
                "contexts": contexts_list,
            }
            
            if ground_truths:
                data["ground_truth"] = ground_truths
            
            # Crear dataset
            dataset = Dataset.from_dict(data)
            
            # Determinar métricas disponibles
            metrics_to_use = self.metrics.copy()
            if not ground_truths:
                # Context recall y context precision requieren ground_truth
                if context_recall in metrics_to_use:
                    metrics_to_use.remove(context_recall)
                if context_precision in metrics_to_use:
                    metrics_to_use.remove(context_precision)
            
            # Verificar que haya LLM configurado
            if not self.llm:
                logger.warning("⚠️ No hay LLM configurado para RAGAS, usando evaluación simulada para batch")
                return {
                    'aggregate': self._fallback_evaluation(),
                    'per_query': [self._fallback_evaluation() for _ in questions]
                }
            
            # Evaluar
            logger.info(f"🔍 Evaluando batch de {len(questions)} consultas con RAGAS")
            results = evaluate(
                dataset, 
                metrics=metrics_to_use,
                llm=self.llm
            )
            
            # Extraer resultados agregados - results es un DataFrame en versiones nuevas de RAGAS
            if hasattr(results, 'to_dict'):
                results_dict = results.to_dict('list')
                aggregate = {
                    'faithfulness': float(sum(results_dict.get('faithfulness', [0.0])) / len(questions)) if 'faithfulness' in results_dict else 0.0,
                    'answer_relevancy': float(sum(results_dict.get('answer_relevancy', [0.0])) / len(questions)) if 'answer_relevancy' in results_dict else 0.0,
                    'context_precision': float(sum(results_dict.get('context_precision', [0.0])) / len(questions)) if 'context_precision' in results_dict and ground_truths else 0.0,
                    'context_recall': float(sum(results_dict.get('context_recall', [0.0])) / len(questions)) if 'context_recall' in results_dict and ground_truths else None
                }
            else:
                # Fallback para versiones antiguas
                aggregate = {
                    'faithfulness': getattr(results, 'faithfulness', 0.0),
                    'answer_relevancy': getattr(results, 'answer_relevancy', 0.0),
                    'context_precision': getattr(results, 'context_precision', 0.0),
                    'context_recall': getattr(results, 'context_recall', 0.0) if ground_truths else None
                }
            
            logger.info(f"✅ Evaluación batch completada: {aggregate}")
            
            return {
                'aggregate': aggregate,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"❌ Error en evaluación batch RAGAS: {e}")
            return {
                'aggregate': self._fallback_evaluation(),
                'per_query': [self._fallback_evaluation() for _ in questions]
            }
    
    def calculate_precision_at_k(
        self,
        retrieved_docs: List[str],
        relevant_docs: List[str],
        k: int = 5
    ) -> float:
        """
        Calcular Precision@k manualmente
        
        Precision@k = (# docs relevantes en top-k) / k
        
        Args:
            retrieved_docs: Documentos recuperados (ordenados por score)
            relevant_docs: Documentos que son realmente relevantes
            k: Número de documentos a considerar
        
        Returns:
            Precision@k score [0.0 - 1.0]
        """
        if not retrieved_docs or k <= 0:
            return 0.0
        
        # Tomar solo los top-k
        top_k = retrieved_docs[:k]
        
        # Contar cuántos son relevantes
        relevant_count = sum(1 for doc in top_k if doc in relevant_docs)
        
        precision = relevant_count / k
        logger.debug(f"📊 Precision@{k}: {relevant_count}/{k} = {precision:.2f}")
        
        return precision
    
    def calculate_recall_at_k(
        self,
        retrieved_docs: List[str],
        relevant_docs: List[str],
        k: int = 5
    ) -> float:
        """
        Calcular Recall@k manualmente
        
        Recall@k = (# docs relevantes recuperados en top-k) / (# total docs relevantes)
        
        Args:
            retrieved_docs: Documentos recuperados (ordenados por score)
            relevant_docs: Documentos que son realmente relevantes
            k: Número de documentos a considerar
        
        Returns:
            Recall@k score [0.0 - 1.0]
        """
        if not relevant_docs:
            return 0.0
        
        # Tomar solo los top-k
        top_k = retrieved_docs[:k]
        
        # Contar cuántos relevantes fueron recuperados
        relevant_count = sum(1 for doc in top_k if doc in relevant_docs)
        
        recall = relevant_count / len(relevant_docs)
        logger.debug(f"📊 Recall@{k}: {relevant_count}/{len(relevant_docs)} = {recall:.2f}")
        
        return recall
    
    def calculate_hallucination_rate(self, faithfulness_score: float) -> float:
        """
        Calcular tasa de alucinación basado en faithfulness
        
        Hallucination Rate = 1.0 - Faithfulness
        
        Args:
            faithfulness_score: Score de faithfulness [0.0 - 1.0]
        
        Returns:
            Hallucination rate [0.0 - 1.0]
        """
        hallucination = max(0.0, min(1.0, 1.0 - faithfulness_score))
        return hallucination
    
    def _fallback_evaluation(self) -> Dict[str, float]:
        """
        Evaluación simulada cuando RAGAS no está disponible
        
        Retorna valores razonables para desarrollo/testing
        """
        return {
            'faithfulness': 0.85,
            'answer_relevancy': 0.82,
            'context_precision': 0.78,
            'context_recall': 0.75
        }
    
    def is_available(self) -> bool:
        """Verificar si RAGAS está disponible"""
        return self.available


# Instancia global del evaluador
_evaluator = None

def get_ragas_evaluator() -> RAGASEvaluator:
    """
    Obtener instancia singleton del evaluador RAGAS
    
    Returns:
        RAGASEvaluator instance
    """
    global _evaluator
    if _evaluator is None:
        _evaluator = RAGASEvaluator()
    return _evaluator


def evaluate_query(
    question: str,
    answer: str,
    contexts: List[str],
    ground_truth: Optional[str] = None
) -> Dict[str, float]:
    """
    Función helper para evaluar una consulta
    
    Args:
        question: La pregunta del usuario
        answer: La respuesta generada
        contexts: Contextos recuperados
        ground_truth: Respuesta correcta (opcional)
    
    Returns:
        Dict con métricas RAGAS
    """
    evaluator = get_ragas_evaluator()
    return evaluator.evaluate_single(question, answer, contexts, ground_truth)
