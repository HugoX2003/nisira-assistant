#!/usr/bin/env python3
"""
REGENERADOR DE BASE DE DATOS RAG
===============================

Script para regenerar la base de datos con embeddings de alta calidad
de forma controlada y con monitoreo de progreso
"""

import os
import sys
import django
import time

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from rag_system.rag_engine.pipeline import RAGPipeline

def regenerar_base_datos():
    """Regenerar base de datos con embeddings de alta calidad"""
    
    print("[START] REGENERANDO BASE DE DATOS RAG")
    print("=" * 60)
    print("[STATS] Modelo: all-mpnet-base-v2 (768 dimensiones - MÁXIMA CALIDAD)")
    print("[FAST] Mini-batches súper optimizados (batch=4)")
    print("[CONFIG] Chunks grandes (2000 chars) + extracción PDF mejorada")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        # Inicializar pipeline
        pipeline = RAGPipeline()
        
        # Obtener lista de documentos
        import glob
        pdf_files = glob.glob("data/documents/*.pdf")
        total_files = len(pdf_files)
        
        print(f"[SEARCH] Encontrados {total_files} archivos PDF")
        print("-" * 60)
        
        processed = 0
        errors = 0
        
        for i, pdf_path in enumerate(pdf_files, 1):
            try:
                filename = os.path.basename(pdf_path)
                print(f"[INFO] [{i}/{total_files}] Procesando: {filename[:50]}...")

                result = pipeline.process_document(pdf_path)

                if result.get('success'):
                    processed += 1
                    chunks = result.get('chunks_created', 0)
                    print(f"   [OK] {chunks} chunks creados")
                else:
                    errors += 1
                    print(f"   [ERROR] Error: {result.get('error', 'Desconocido')}")

            except KeyboardInterrupt:
                print(f"\n[WARN] Interrumpido en archivo {i}/{total_files}")
                break
            except Exception as e:
                errors += 1
                print(f"   [ERROR] Error inesperado: {e}")

        elapsed = time.time() - start_time

        print("\n" + "=" * 60)
        print("[STATS] RESULTADOS FINALES:")
        print(f"[OK] Archivos procesados: {processed}/{total_files}")
        print(f"[ERROR] Errores: {errors}")
        print(f"[TIME] Tiempo total: {elapsed:.1f} segundos")

        if processed > 0:
            print("[DONE] BASE DE DATOS REGENERADA EXITOSAMENTE")
            print("[INFO] Embeddings OPTIMIZADOS listos")

    except KeyboardInterrupt:
        print("\n[WARN] Procesamiento interrumpido por el usuario")
    except Exception as e:
        print(f"\n[ERROR] Error inesperado: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    regenerar_base_datos()