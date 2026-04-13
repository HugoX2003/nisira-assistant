"""
Script para insertar consultas de prueba con métricas
"""

import sys
import os
import uuid
from datetime import datetime, timedelta
import random

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from api.models import QueryMetrics, RAGASMetrics
from django.contrib.auth.models import User

def create_sample_queries():
    """Crear consultas de ejemplo con métricas"""
    
    # Obtener o crear usuario admin
    try:
        admin_user = User.objects.get(username='admin')
    except User.DoesNotExist:
        admin_user = None
    
    sample_queries = [
        {
            "query_text": "¿Qué es ISO 27001 y cuáles son sus controles principales?",
            "is_complex": True,
            "complexity_score": 0.75,
            "total_latency": 3.45,
            "ttft": 0.89,
            "retrieval_time": 0.34,
            "generation_time": 2.22,
            "docs_retrieved": 5,
            "precision": 0.80,
            "recall": 0.60,
            "faithfulness": 0.92,
            "relevancy": 0.88
        },
        {
            "query_text": "Explica los requisitos de la norma ISO 27002",
            "is_complex": False,
            "complexity_score": 0.35,
            "total_latency": 2.18,
            "ttft": 0.56,
            "retrieval_time": 0.28,
            "generation_time": 1.34,
            "docs_retrieved": 5,
            "precision": 0.60,
            "recall": 0.40,
            "faithfulness": 0.85,
            "relevancy": 0.75
        },
        {
            "query_text": "¿Cuál es la diferencia entre ISO 27001 e ISO 27002?",
            "is_complex": True,
            "complexity_score": 0.68,
            "total_latency": 4.12,
            "ttft": 1.02,
            "retrieval_time": 0.45,
            "generation_time": 2.65,
            "docs_retrieved": 5,
            "precision": 0.40,
            "recall": 0.20,
            "faithfulness": 0.78,
            "relevancy": 0.82
        },
        {
            "query_text": "Dame ejemplos de controles de seguridad",
            "is_complex": False,
            "complexity_score": 0.25,
            "total_latency": 1.89,
            "ttft": 0.42,
            "retrieval_time": 0.22,
            "generation_time": 1.25,
            "docs_retrieved": 5,
            "precision": 0.60,
            "recall": 0.40,
            "faithfulness": 0.90,
            "relevancy": 0.92
        },
        {
            "query_text": "¿Cómo implementar un sistema de gestión de seguridad de la información según ISO 27001?",
            "is_complex": True,
            "complexity_score": 0.82,
            "total_latency": 5.34,
            "ttft": 1.23,
            "retrieval_time": 0.52,
            "generation_time": 3.59,
            "docs_retrieved": 5,
            "precision": 0.80,
            "recall": 0.80,
            "faithfulness": 0.95,
            "relevancy": 0.95
        }
    ]
    
    print("🔄 Insertando consultas de prueba...")
    
    for i, query_data in enumerate(sample_queries):
        # Crear QueryMetrics
        query_id = str(uuid.uuid4())
        timestamp = datetime.now() - timedelta(hours=i)
        
        query_metric = QueryMetrics.objects.create(
            query_id=query_id,
            user=admin_user,
            query_text=query_data['query_text'],
            total_latency=query_data['total_latency'],
            time_to_first_token=query_data['ttft'],
            retrieval_time=query_data['retrieval_time'],
            generation_time=query_data['generation_time'],
            is_complex_query=query_data['is_complex'],
            query_complexity_score=query_data['complexity_score'],
            documents_retrieved=query_data['docs_retrieved'],
            top_k=5
        )
        
        # Crear RAGASMetrics asociadas
        hallucination_rate = 1.0 - query_data['faithfulness']
        
        RAGASMetrics.objects.create(
            evaluation_id=str(uuid.uuid4()),
            query_metrics=query_metric,
            query_text=query_data['query_text'][:200],
            response_text="Respuesta generada de ejemplo",
            retrieved_contexts="Contextos recuperados",
            precision_at_k=query_data['precision'],
            recall_at_k=query_data['recall'],
            faithfulness_score=query_data['faithfulness'],
            answer_relevancy=query_data['relevancy'],
            hallucination_rate=hallucination_rate,
            k_value=5
        )
        
        print(f"  ✅ Consulta {i+1}: {query_data['query_text'][:50]}...")
    
    print(f"\n✅ {len(sample_queries)} consultas de prueba insertadas correctamente")
    print(f"\n📊 Total en base de datos: {QueryMetrics.objects.count()} consultas")
    print(f"📊 Consultas complejas: {QueryMetrics.objects.filter(is_complex_query=True).count()}")
    print(f"📊 Métricas de precisión: {RAGASMetrics.objects.count()}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("📊 GENERADOR DE CONSULTAS DE PRUEBA")
    print("="*60 + "\n")
    
    try:
        create_sample_queries()
        print("\n✅ ¡Listo! Ahora recarga el panel de administración")
        print("📍 Ve a: Métricas → Detalle por Consulta")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
