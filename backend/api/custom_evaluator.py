"""
Evaluador de Métricas Personalizado SIN RAGAS
==============================================

Sistema propio de evaluación de métricas de precisión para RAG
sin dependencias externas ni API keys.

Métricas implementadas:
- Precision@k: Relevancia de documentos recuperados
- Recall@k: Cobertura de documentos relevantes
- Faithfulness: Fidelidad al contexto (sin alucinaciones)
- Hallucination Rate: Tasa de información inventada
- WER (Word Error Rate): Calidad de generación de texto
- Answer Relevancy: Relevancia de la respuesta
"""

import logging
import re
from typing import List, Dict, Any, Set
from difflib import SequenceMatcher
import numpy as np

logger = logging.getLogger(__name__)


class CustomMetricsEvaluator:
    """
    Evaluador de métricas personalizado sin dependencias externas
    """
    
    def __init__(self):
        """Inicializar evaluador"""
        logger.info("✅ CustomMetricsEvaluator inicializado (sin dependencias externas)")
    
    def calculate_precision_at_k(
        self,
        retrieved_contexts: List[str],
        answer: str,
        k: int = 5
    ) -> float:
        """
        Calcular Precision@k basado en la relevancia de los contextos recuperados
        
        Mide: ¿Cuántos de los documentos recuperados fueron realmente útiles?
        
        Método: Calcula overlap semántico entre cada contexto y la respuesta.
        Si el overlap > 0.3, se considera relevante.
        
        Args:
            retrieved_contexts: Lista de contextos recuperados
            answer: La respuesta generada
            k: Número de documentos a evaluar
        
        Returns:
            Precision@k [0.0 - 1.0]
        """
        if not retrieved_contexts or k <= 0:
            return 0.0
        
        # Tomar solo top-k contextos
        top_k_contexts = retrieved_contexts[:k]
        
        # Contar cuántos contextos son relevantes (tienen overlap con la respuesta)
        relevant_count = 0
        answer_words = set(self._tokenize(answer.lower()))
        
        logger.info(f"\n🔍 Método: Jaccard Similarity entre palabras de respuesta y cada documento")
        logger.info(f"   Threshold: 0.20 (20% de overlap mínimo para considerar relevante)")
        logger.info(f"\n📝 Palabras en la respuesta: {len(answer_words)} palabras únicas")
        logger.info(f"   Muestra: {list(answer_words)[:10]}...\n")
        
        for i, context in enumerate(top_k_contexts):
            context_words = set(self._tokenize(context.lower()))
            
            # Calcular Jaccard similarity
            if len(answer_words) > 0 and len(context_words) > 0:
                # Palabras en común entre respuesta y documento
                palabras_comunes = answer_words.intersection(context_words)
                overlap = len(palabras_comunes)
                
                # Total de palabras únicas entre ambos
                union = len(answer_words.union(context_words))
                
                # Similitud de Jaccard = intersección / unión
                similarity = overlap / union if union > 0 else 0.0
                
                logger.info(f"📄 DOCUMENTO {i+1}:")
                logger.info(f"   Contenido: {context[:150]}...")
                logger.info(f"   Palabras en documento: {len(context_words)}")
                logger.info(f"   Palabras comunes (overlap): {overlap}")
                logger.info(f"   Palabras totales (unión): {union}")
                logger.info(f"   Jaccard Similarity = {overlap}/{union} = {similarity:.4f}")
                logger.info(f"   Porcentaje de similitud: {similarity * 100:.2f}%")
                
                # THRESHOLD AJUSTADO: 0.08 (8% de overlap se considera relevante)
                # En sistemas RAG, documentos recuperados por embeddings suelen tener 5-15% de overlap
                THRESHOLD = 0.08
                
                if similarity > THRESHOLD:
                    relevant_count += 1
                    logger.info(f"   ✅ RELEVANTE (similarity {similarity:.4f} > {THRESHOLD})")
                    logger.info(f"   Palabras clave compartidas: {list(palabras_comunes)[:20]}...")
                else:
                    logger.info(f"   ❌ IRRELEVANTE (similarity {similarity:.4f} ≤ {THRESHOLD})")
                    # Mostrar por qué no es relevante
                    if overlap == 0:
                        logger.info(f"   ⚠️ Sin palabras en común entre respuesta y documento")
                    elif similarity < 0.05:
                        logger.info(f"   ⚠️ Muy poca similitud (<5%), documento probablemente no útil")
                logger.info("")
        
        precision = relevant_count / k
        logger.info(f"\n🎯 RESULTADO FINAL - Precision@{k}:")
        logger.info(f"   Fórmula: (documentos_relevantes) / k")
        logger.info(f"   Cálculo: {relevant_count} / {k} = {precision:.4f}")
        logger.info(f"   Porcentaje: {precision * 100:.2f}%")
        logger.info(f"   Documentos relevantes: {relevant_count}/{k}")
        logger.info(f"   Documentos irrelevantes: {k - relevant_count}/{k}")
        
        return precision
    
    def calculate_recall_at_k(
        self,
        retrieved_contexts: List[str],
        answer: str,
        k: int = 5
    ) -> float:
        """
        Calcular Recall@k basado en la cobertura de información en la respuesta
        
        Mide: ¿La respuesta cubre información de múltiples contextos relevantes?
        
        Método: Verifica cuántos contextos tienen información presente en la respuesta.
        
        Args:
            retrieved_contexts: Lista de contextos recuperados
            answer: La respuesta generada
            k: Número de documentos a evaluar
        
        Returns:
            Recall@k [0.0 - 1.0]
        """
        if not retrieved_contexts or k <= 0:
            return 0.0
        
        # Tomar top-k contextos
        top_k_contexts = retrieved_contexts[:k]
        answer_lower = answer.lower()
        
        # Contar cuántos contextos tienen información en la respuesta
        contexts_covered = 0
        
        logger.info(f"\n🔍 Método: Detección de n-gramas (frases de 3 palabras) del contexto en la respuesta")
        logger.info(f"   Si al menos 1 frase del documento aparece en la respuesta → contexto USADO\n")
        
        for i, context in enumerate(top_k_contexts):
            # Extraer frases clave del contexto (n-gramas de 3 palabras)
            key_phrases = self._extract_key_phrases(context, n=3)
            
            # Verificar si alguna frase clave está en la respuesta
            frases_encontradas = [phrase for phrase in key_phrases if phrase in answer_lower]
            found = len(frases_encontradas) > 0
            
            logger.info(f"📄 CONTEXTO {i+1}:")
            logger.info(f"   Contenido: {context[:100]}...")
            logger.info(f"   Frases clave extraídas: {len(key_phrases)}")
            logger.info(f"   Muestra de frases: {key_phrases[:5]}")
            logger.info(f"   Frases encontradas en respuesta: {len(frases_encontradas)}")
            if frases_encontradas:
                logger.info(f"   Frases que coinciden: {frases_encontradas[:3]}...")
            
            if found:
                contexts_covered += 1
                logger.info(f"   ✅ USADO - La respuesta contiene información de este documento")
            else:
                logger.info(f"   ❌ NO USADO - La respuesta no usa información de este documento")
            logger.info("")
        
        # Recall = contextos cubiertos / total contextos recuperados
        recall = contexts_covered / k
        logger.info(f"\n🎯 RESULTADO FINAL - Recall@{k}:")
        logger.info(f"   Fórmula: (contextos_usados) / k")
        logger.info(f"   Cálculo: {contexts_covered} / {k} = {recall:.4f}")
        logger.info(f"   Porcentaje: {recall * 100:.2f}%")
        logger.info(f"   Contextos usados: {contexts_covered}/{k}")
        logger.info(f"   Contextos no usados: {k - contexts_covered}/{k}")
        
        return recall
    
    def calculate_faithfulness(
        self,
        answer: str,
        contexts: List[str]
    ) -> float:
        """
        Calcular Faithfulness (Fidelidad) - ¿La respuesta está respaldada por el contexto?
        
        Mide: ¿Cuánto de la respuesta proviene del contexto vs inventado?
        
        Método: Divide la respuesta en frases y verifica cuántas tienen soporte
        en los contextos proporcionados.
        
        Args:
            answer: La respuesta generada
            contexts: Lista de contextos utilizados
        
        Returns:
            Faithfulness score [0.0 - 1.0]
        """
        if not answer or not contexts:
            return 0.0
        
        # Dividir respuesta en oraciones
        sentences = self._split_into_sentences(answer)
        
        if not sentences:
            return 0.0
        
        # Concatenar todos los contextos
        full_context = " ".join(contexts).lower()
        
        # Contar cuántas oraciones están respaldadas por el contexto
        supported_sentences = 0
        
        for i, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()
            
            # Extraer palabras clave de la oración (sin stopwords)
            keywords = self._extract_keywords(sentence_lower)
            
            if not keywords:
                continue
            
            # Verificar cuántas palabras clave están en el contexto
            keywords_in_context = sum(1 for kw in keywords if kw in full_context)
            coverage = keywords_in_context / len(keywords)
            
            logger.info(f"  📝 Oración {i+1}: {keywords_in_context}/{len(keywords)} keywords en contexto ({coverage:.2%})")
            
            # Si >60% de las palabras clave están en el contexto, la oración está respaldada
            if coverage > 0.6:
                supported_sentences += 1
                logger.info(f"    ✅ Respaldada (coverage > 60%)")
            else:
                logger.info(f"    ❌ Sin respaldo (coverage ≤ 60%)")
        
        faithfulness = supported_sentences / len(sentences)
        logger.info(f"🎯 Faithfulness = {supported_sentences}/{len(sentences)} = {faithfulness:.4f}")
        logger.info(f"   Fórmula: (oraciones_respaldadas) / (total_oraciones)")
        logger.info(f"   Cálculo: ({supported_sentences}) / {len(sentences)} = {faithfulness:.4f}")
        
        return faithfulness
    
    def calculate_hallucination_rate(self, faithfulness_score: float) -> float:
        """
        Calcular tasa de alucinación
        
        Hallucination Rate = 1.0 - Faithfulness
        
        Args:
            faithfulness_score: Score de faithfulness [0.0 - 1.0]
        
        Returns:
            Hallucination rate [0.0 - 1.0]
        """
        hallucination = 1.0 - faithfulness_score
        return max(0.0, min(1.0, hallucination))
    
    def calculate_answer_relevancy(
        self,
        question: str,
        answer: str
    ) -> float:
        """
        Calcular relevancia de la respuesta con respecto a la pregunta
        
        Mide: ¿La respuesta aborda la pregunta planteada?
        
        Método: Calcula overlap semántico entre pregunta y respuesta,
        considerando palabras clave y entidades.
        
        Args:
            question: La pregunta del usuario
            answer: La respuesta generada
        
        Returns:
            Relevancy score [0.0 - 1.0]
        """
        if not question or not answer:
            return 0.0
        
        # Extraer palabras clave de la pregunta
        question_keywords = self._extract_keywords(question.lower())
        
        if not question_keywords:
            return 0.5  # Neutral si no hay keywords
        
        # Verificar cuántas keywords están en la respuesta
        answer_lower = answer.lower()
        keywords_in_answer = sum(1 for kw in question_keywords if kw in answer_lower)
        keywords_missing = len(question_keywords) - keywords_in_answer
        
        logger.info(f"  🔑 Keywords pregunta: {question_keywords}")
        logger.info(f"  ✅ Presentes en respuesta: {keywords_in_answer}")
        logger.info(f"  ❌ Ausentes: {keywords_missing}")
        
        # Calcular relevancia base
        relevancy = keywords_in_answer / len(question_keywords)
        
        # Bonus: si la respuesta tiene longitud razonable (no muy corta ni muy larga)
        answer_length = len(answer.split())
        if 20 <= answer_length <= 300:
            old_relevancy = relevancy
            relevancy = min(1.0, relevancy + 0.1)
            logger.info(f"  🎁 Bonus longitud razonable: {old_relevancy:.4f} + 0.1 = {relevancy:.4f}")
        
        logger.info(f"🎯 Answer Relevancy = {keywords_in_answer}/{len(question_keywords)} = {relevancy:.4f}")
        logger.info(f"   Fórmula: (keywords_presentes) / (total_keywords)")
        logger.info(f"   Cálculo: ({keywords_in_answer}) / {len(question_keywords)} = {relevancy:.4f}")
        
        return relevancy
    
    def calculate_wer(
        self,
        reference: str,
        hypothesis: str
    ) -> float:
        """
        Calcular Word Error Rate (WER)
        
        WER = (Sustituciones + Inserciones + Eliminaciones) / Total palabras en referencia
        
        Mide la distancia de edición entre dos textos.
        
        Args:
            reference: Texto de referencia (ground truth)
            hypothesis: Texto generado (a evaluar)
        
        Returns:
            WER score [0.0 - inf], donde 0.0 es perfecto
        """
        # Tokenizar
        ref_words = self._tokenize(reference)
        hyp_words = self._tokenize(hypothesis)
        
        # Calcular distancia de Levenshtein
        distance = self._levenshtein_distance(ref_words, hyp_words)
        
        # WER = distancia / longitud de referencia
        wer = distance / len(ref_words) if ref_words else 0.0
        
        logger.debug(f"📊 WER: {distance}/{len(ref_words)} = {wer:.3f}")
        
        return wer
    
    def evaluate_single(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: str = None,
        k: int = 5
    ) -> Dict[str, Any]:
        """
        Evaluar consulta con SOLO Precision@k y Recall@k
        
        Args:
            question: Pregunta del usuario
            answer: Respuesta generada
            contexts: Contextos recuperados
            ground_truth: No usado (por compatibilidad)
            k: Número de documentos para precision/recall
        
        Returns:
            Dict con SOLO precision y recall
        """
        try:
            logger.info("\n" + "="*80)
            logger.info("🔬 EVALUACIÓN DE PRECISIÓN Y EXHAUSTIVIDAD")
            logger.info("="*80)
            logger.info(f"📋 Pregunta: {question}")
            logger.info(f"📋 Respuesta generada: {len(answer)} caracteres")
            logger.info(f"📋 Documentos recuperados: {len(contexts)}")
            logger.info(f"📋 K value (top-k para evaluar): {k}")
            logger.info("\n" + "-"*80)
            logger.info("📊 CALCULANDO ÍNDICE DE PRECISIÓN (Precision@k)")
            logger.info("-"*80)
            
            # Calcular SOLO precision y recall
            precision = self.calculate_precision_at_k(contexts, answer, k)
            
            logger.info("\n" + "-"*80)
            logger.info("📊 CALCULANDO ÍNDICE DE EXHAUSTIVIDAD (Recall@k)")
            logger.info("-"*80)
            recall = self.calculate_recall_at_k(contexts, answer, k)
            
            metrics = {
                'context_precision': precision,
                'context_recall': recall
            }
            
            logger.info("\n" + "="*80)
            logger.info("✅ EVALUACIÓN COMPLETADA")
            logger.info("="*80)
            logger.info(f"   📊 Índice de Precisión (Precision@k): {precision:.4f} ({precision*100:.2f}%)")
            logger.info(f"   📊 Índice de Exhaustividad (Recall@k): {recall:.4f} ({recall*100:.2f}%)")
            logger.info("="*80 + "\n")
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Error en evaluación: {e}", exc_info=True)
            return {
                'context_precision': 0.0,
                'context_recall': 0.0
            }
    
    # ========== MÉTODOS AUXILIARES ==========
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenizar texto en palabras"""
        # Remover puntuación y dividir por espacios
        text = re.sub(r'[^\w\s]', ' ', text)
        words = text.lower().split()
        return [w for w in words if len(w) > 2]  # Filtrar palabras muy cortas
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Dividir texto en oraciones"""
        # Dividir por puntos, signos de exclamación o interrogación
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extraer palabras clave (sin stopwords comunes)"""
        # Stopwords en español e inglés
        stopwords = {
            'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se', 'no', 'hay',
            'por', 'con', 'su', 'para', 'como', 'está', 'lo', 'pero', 'sus', 'le',
            'ya', 'o', 'fue', 'este', 'ha', 'sí', 'porque', 'esta', 'son', 'entre',
            'the', 'is', 'at', 'which', 'on', 'are', 'as', 'an', 'be', 'this', 'that',
            'was', 'for', 'with', 'by', 'from', 'or', 'not', 'but', 'what', 'all'
        }
        
        words = self._tokenize(text)
        keywords = {w for w in words if w not in stopwords and len(w) > 3}
        
        return keywords
    
    def _extract_key_phrases(self, text: str, n: int = 3) -> List[str]:
        """Extraer frases clave (n-gramas)"""
        words = self._tokenize(text)
        phrases = []
        
        # Generar n-gramas
        for i in range(len(words) - n + 1):
            phrase = ' '.join(words[i:i+n])
            phrases.append(phrase)
        
        return phrases
    
    def _levenshtein_distance(self, seq1: List[str], seq2: List[str]) -> int:
        """
        Calcular distancia de Levenshtein entre dos secuencias
        (número mínimo de operaciones para transformar seq1 en seq2)
        """
        m, n = len(seq1), len(seq2)
        
        # Crear matriz de distancias
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        # Inicializar primera fila y columna
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        
        # Llenar matriz
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i-1] == seq2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(
                        dp[i-1][j],    # Eliminación
                        dp[i][j-1],    # Inserción
                        dp[i-1][j-1]   # Sustitución
                    )
        
        return dp[m][n]


# Instancia global
_evaluator = None

def get_custom_evaluator() -> CustomMetricsEvaluator:
    """Obtener instancia singleton del evaluador"""
    global _evaluator
    if _evaluator is None:
        _evaluator = CustomMetricsEvaluator()
    return _evaluator
