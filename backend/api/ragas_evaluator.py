"""
RAGAS Evaluator con OpenRouter
================================

Sistema de evaluación de calidad de respuesta usando RAGAS real
con OpenRouter (Gemini via OpenRouter) como LLM para evaluación.

Métricas RAGAS utilizadas (NO requieren ground_truth):
- Faithfulness: Fidelidad de la respuesta al contexto (0-1)
- Answer Relevancy: Relevancia de la respuesta a la pregunta (0-1)
- Context Utilization: Calculado localmente (0-1)
"""

import logging
import os
from typing import List, Dict
from datasets import Dataset

os.environ.setdefault('GIT_PYTHON_REFRESH', 'quiet')

from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)


class RAGASEvaluator:

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")

        if not self.api_key:
            raise ValueError("Se requiere OPENROUTER_API_KEY")

        try:
            self.llm = ChatOpenAI(
                model=os.getenv("RAGAS_EVALUATOR_MODEL", "google/gemini-2.0-flash-exp"),
                openai_api_key=self.api_key,
                openai_api_base="https://openrouter.ai/api/v1",
                temperature=0.0,
            )

            # Embeddings locales con HuggingFace (sin API externa)
            self.embeddings = HuggingFaceEmbeddings(
                model_name=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2"),
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )

            self.metrics = [
                faithfulness,
                answer_relevancy,
            ]

            logger.info("[OK] RAGASEvaluator inicializado con OpenRouter")

        except Exception as e:
            logger.error(f"[ERROR] Error al inicializar RAGASEvaluator: {e}")
            raise

    def evaluate_response(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: str = None
    ) -> Dict[str, float]:

        try:
            data = {
                'question': [question],
                'answer': [answer],
                'contexts': [contexts],
            }

            if ground_truth:
                data['ground_truth'] = [ground_truth]

            dataset = Dataset.from_dict(data)

            logger.info(f"[SEARCH] Evaluando con RAGAS...")
            logger.info(f"   Question: {question[:100]}")
            logger.info(f"   Contexts: {len(contexts)} documentos")

            result = evaluate(
                dataset,
                metrics=self.metrics,
                llm=self.llm,
                embeddings=self.embeddings,
            )

            if hasattr(result, 'to_pandas'):
                result_dict = result.to_pandas().to_dict('records')[0]
            elif isinstance(result, dict):
                result_dict = result
            else:
                result_dict = result.__dict__

            faithfulness_score = float(result_dict.get('faithfulness', 0.0))
            relevancy_score = float(result_dict.get('answer_relevancy', 0.0))
            context_util_score = self._calculate_context_utilization(answer, contexts)

            calidad = (
                faithfulness_score * 0.4 +
                relevancy_score * 0.4 +
                context_util_score * 0.2
            )

            metrics = {
                'faithfulness': faithfulness_score,
                'answer_relevancy': relevancy_score,
                'context_precision': context_util_score,
                'calidad_respuesta': calidad,
            }

            logger.info(f"[OK] RAGAS Results - Faith: {faithfulness_score:.2%} | Relevancy: {relevancy_score:.2%} | Calidad: {calidad:.2%}")

            return metrics

        except Exception as e:
            logger.error(f"[ERROR] Error en evaluación RAGAS: {e}")
            return {
                'faithfulness': 0.0,
                'answer_relevancy': 0.0,
                'context_precision': 0.0,
                'calidad_respuesta': 0.0,
                'error': str(e),
            }

    def _calculate_context_utilization(self, answer: str, contexts: List[str]) -> float:
        import re

        stopwords = {
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'de', 'del', 'al',
            'a', 'en', 'con', 'por', 'para', 'es', 'son', 'que', 'se', 'su', 'sus',
            'y', 'o', 'pero', 'como', 'más', 'este', 'esta', 'estos', 'estas',
            'tiene', 'tienen', 'ser', 'estar', 'hay', 'lo', 'le', 'les', 'no', 'si',
        }

        def extract_keywords(text: str) -> set:
            words = re.findall(r'\b[a-záéíóúñ]{4,}\b', text.lower())
            return {w for w in words if w not in stopwords}

        context_keywords = extract_keywords(' '.join(contexts))
        if not context_keywords:
            return 0.5

        answer_keywords = extract_keywords(answer)
        matching = context_keywords.intersection(answer_keywords)
        utilization = len(matching) / len(context_keywords)
        return min(utilization / 0.3, 1.0)

    def get_quality_label(self, calidad_score: float) -> str:
        if calidad_score >= 0.8:
            return "Excelente"
        elif calidad_score >= 0.6:
            return "Buena"
        elif calidad_score >= 0.4:
            return "Aceptable"
        else:
            return "Deficiente"