"""
RAGAS Evaluator con Gemini API
================================

Sistema de evaluación de calidad de respuesta usando RAGAS real
con Google Gemini como LLM para evaluación.

Métricas RAGAS utilizadas:
- Faithfulness: Fidelidad de la respuesta al contexto (0-1)
- Answer Relevancy: Relevancia de la respuesta a la pregunta (0-1)
- Context Precision: Precisión de la recuperación de contexto (0-1)

Calidad de Respuesta = Promedio ponderado de estas 3 métricas
"""

import logging
import os
from typing import List, Dict, Any
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision
)
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)


class RAGASEvaluator:
    """
    Evaluador de calidad de respuesta usando RAGAS con Gemini
    """
    
    def __init__(self, api_key: str = None):
        """
        Inicializar evaluador RAGAS con Gemini
        
        Args:
            api_key: API key de Google Gemini (opcional, usa env var si no se provee)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "AIzaSyCz1SUWtMm15vqng-KgMPxiVJlIGclwApk")
        
        try:
            # Configurar Gemini como LLM para RAGAS
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=self.api_key,
                temperature=0.0
            )
            
            # Configurar métricas RAGAS
            self.metrics = [
                faithfulness,
                answer_relevancy,
                context_precision
            ]
            
            logger.info("✅ RAGASEvaluator inicializado con Gemini API")
            
        except Exception as e:
            logger.error(f"❌ Error al inicializar RAGASEvaluator: {e}")
            raise
    
    def evaluate_response(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: str = None
    ) -> Dict[str, float]:
        """
        Evaluar calidad de respuesta usando RAGAS
        
        Args:
            question: Pregunta del usuario
            answer: Respuesta generada por el RAG
            contexts: Lista de contextos recuperados
            ground_truth: Respuesta ideal (opcional, mejora evaluación)
        
        Returns:
            Dict con métricas RAGAS:
            {
                'faithfulness': 0.0-1.0,
                'answer_relevancy': 0.0-1.0,
                'context_precision': 0.0-1.0,
                'calidad_respuesta': 0.0-1.0 (promedio)
            }
        """
        try:
            # Preparar datos en formato RAGAS
            data = {
                'question': [question],
                'answer': [answer],
                'contexts': [contexts],
            }
            
            # Si hay ground_truth, agregarlo
            if ground_truth:
                data['ground_truth'] = [ground_truth]
            
            # Crear dataset
            dataset = Dataset.from_dict(data)
            
            # Ejecutar evaluación RAGAS
            logger.info(f"🔍 Evaluando con RAGAS...")
            logger.info(f"   Question: {question[:100]}...")
            logger.info(f"   Answer length: {len(answer)} chars")
            logger.info(f"   Contexts: {len(contexts)} documents")
            
            result = evaluate(
                dataset,
                metrics=self.metrics,
                llm=self.llm
            )
            
            # Extraer scores
            faithfulness_score = result['faithfulness']
            relevancy_score = result['answer_relevancy']
            precision_score = result['context_precision']
            
            # Calcular calidad de respuesta (promedio ponderado)
            # Faithfulness 40%, Answer Relevancy 40%, Context Precision 20%
            calidad = (
                faithfulness_score * 0.4 +
                relevancy_score * 0.4 +
                precision_score * 0.2
            )
            
            metrics = {
                'faithfulness': float(faithfulness_score),
                'answer_relevancy': float(relevancy_score),
                'context_precision': float(precision_score),
                'calidad_respuesta': float(calidad)
            }
            
            logger.info(f"✅ RAGAS Evaluation Results:")
            logger.info(f"   Faithfulness: {faithfulness_score:.2%}")
            logger.info(f"   Answer Relevancy: {relevancy_score:.2%}")
            logger.info(f"   Context Precision: {precision_score:.2%}")
            logger.info(f"   📊 CALIDAD DE RESPUESTA: {calidad:.2%}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Error en evaluación RAGAS: {e}")
            # Retornar valores por defecto en caso de error
            return {
                'faithfulness': 0.0,
                'answer_relevancy': 0.0,
                'context_precision': 0.0,
                'calidad_respuesta': 0.0,
                'error': str(e)
            }
    
    def get_quality_label(self, calidad_score: float) -> str:
        """
        Obtener etiqueta descriptiva de calidad
        
        Args:
            calidad_score: Score de calidad (0.0-1.0)
        
        Returns:
            Etiqueta: Excelente, Buena, Aceptable, Deficiente
        """
        if calidad_score >= 0.8:
            return "Excelente"
        elif calidad_score >= 0.6:
            return "Buena"
        elif calidad_score >= 0.4:
            return "Aceptable"
        else:
            return "Deficiente"
    
    def get_quality_emoji(self, calidad_score: float) -> str:
        """
        Obtener emoji representativo de calidad
        
        Args:
            calidad_score: Score de calidad (0.0-1.0)
        
        Returns:
            Emoji: 🟢, 🟡, 🟠, 🔴
        """
        if calidad_score >= 0.8:
            return "🟢"
        elif calidad_score >= 0.6:
            return "🟡"
        elif calidad_score >= 0.4:
            return "🟠"
        else:
            return "🔴"
