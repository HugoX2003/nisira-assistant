"""
RAGAS Evaluator con Gemini API
================================

Sistema de evaluación de calidad de respuesta usando RAGAS real
con Google Gemini como LLM para evaluación.

Métricas RAGAS utilizadas (NO requieren ground_truth):
- Faithfulness: Fidelidad de la respuesta al contexto (0-1)
- Answer Relevancy: Relevancia de la respuesta a la pregunta (0-1)
- Context Utilization: Calculado localmente - uso efectivo del contexto (0-1)

Calidad de Respuesta = Promedio ponderado de estas 3 métricas
"""

import logging
import os
from typing import List, Dict, Any
from datasets import Dataset

# Silenciar el warning de git antes de importar RAGAS
os.environ.setdefault('GIT_PYTHON_REFRESH', 'quiet')

from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy
)
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

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
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            raise ValueError("Se requiere GEMINI_API_KEY o GOOGLE_API_KEY")
        
        try:
            # Configurar Gemini como LLM para RAGAS
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=self.api_key,
                temperature=0.0
            )
            
            # Configurar embeddings de Gemini
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=self.api_key
            )
            
            # Configurar métricas RAGAS (solo las que NO requieren ground_truth)
            self.metrics = [
                faithfulness,          # Fidelidad al contexto
                answer_relevancy       # Relevancia de la respuesta
            ]
            
            logger.info("✅ RAGASEvaluator inicializado con Gemini API (gemini-2.0-flash)")
            
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
                llm=self.llm,
                embeddings=self.embeddings
            )
            
            # Extraer scores de RAGAS
            # result.scores es un DataFrame de pandas
            scores_df = result.scores
            faithfulness_score = float(scores_df['faithfulness'].iloc[0]) if 'faithfulness' in scores_df.columns else 0.0
            relevancy_score = float(scores_df['answer_relevancy'].iloc[0]) if 'answer_relevancy' in scores_df.columns else 0.0
            
            # Calcular Context Utilization manualmente
            # Medimos qué proporción de palabras clave del contexto aparecen en la respuesta
            context_util_score = self._calculate_context_utilization(answer, contexts)
            
            # Calcular calidad de respuesta (promedio ponderado)
            # Faithfulness 40%, Answer Relevancy 40%, Context Utilization 20%
            calidad = (
                faithfulness_score * 0.4 +
                relevancy_score * 0.4 +
                context_util_score * 0.2
            )
            
            metrics = {
                'faithfulness': float(faithfulness_score),
                'answer_relevancy': float(relevancy_score),
                'context_precision': float(context_util_score),  # Mapeamos a context_precision para compatibilidad
                'calidad_respuesta': float(calidad)
            }
            
            logger.info(f"✅ RAGAS Evaluation Results:")
            logger.info(f"   Faithfulness: {faithfulness_score:.2%}")
            logger.info(f"   Answer Relevancy: {relevancy_score:.2%}")
            logger.info(f"   Context Utilization: {context_util_score:.2%}")
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
    
    def _calculate_context_utilization(self, answer: str, contexts: List[str]) -> float:
        """
        Calcular qué tan bien se utilizan los contextos en la respuesta.
        Mide la proporción de términos importantes del contexto que aparecen en la respuesta.
        
        Args:
            answer: Respuesta generada
            contexts: Lista de contextos recuperados
        
        Returns:
            Score de 0.0 a 1.0
        """
        import re
        
        # Palabras comunes a ignorar (stopwords en español)
        stopwords = {
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'de', 'del', 'al',
            'a', 'en', 'con', 'por', 'para', 'es', 'son', 'que', 'se', 'su', 'sus',
            'y', 'o', 'pero', 'como', 'más', 'este', 'esta', 'estos', 'estas',
            'tiene', 'tienen', 'ser', 'estar', 'hay', 'lo', 'le', 'les', 'no', 'si',
            'the', 'a', 'an', 'is', 'are', 'of', 'to', 'in', 'for', 'on', 'with'
        }
        
        def extract_keywords(text: str) -> set:
            """Extraer palabras clave de un texto"""
            # Convertir a minúsculas y extraer palabras
            words = re.findall(r'\b[a-záéíóúñ]{4,}\b', text.lower())
            # Filtrar stopwords y palabras muy cortas
            return {w for w in words if w not in stopwords and len(w) >= 4}
        
        # Extraer keywords del contexto
        context_text = ' '.join(contexts)
        context_keywords = extract_keywords(context_text)
        
        if not context_keywords:
            return 0.5  # Sin contexto, valor neutral
        
        # Extraer keywords de la respuesta
        answer_keywords = extract_keywords(answer)
        
        # Calcular cuántas keywords del contexto aparecen en la respuesta
        matching_keywords = context_keywords.intersection(answer_keywords)
        
        # Score = proporción de keywords del contexto usadas en la respuesta
        # Limitado a 1.0 máximo
        utilization = len(matching_keywords) / len(context_keywords)
        
        # Normalizar: si usa más del 30% de keywords del contexto, es excelente
        normalized_score = min(utilization / 0.3, 1.0)
        
        return normalized_score
    
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
