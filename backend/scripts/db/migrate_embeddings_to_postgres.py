"""
Script para migrar embeddings de ChromaDB a PostgreSQL
======================================================

Migra todos los embeddings existentes en tu ChromaDB local
a PostgreSQL para deployment en producción.
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from rag_system.vector_store.chroma_manager import ChromaManager
from rag_system.vector_store.postgres_store import PostgresVectorStore
import json
from tqdm import tqdm


def migrate_embeddings():
    """Migrar embeddings de ChromaDB a PostgreSQL"""
    
    print("[SYNC] Iniciando migración de embeddings...")
    print("=" * 60)

    # 1. Conectar a ChromaDB local
    print("[DIR] Conectando a ChromaDB local...")
    chroma = ChromaManager()

    if not chroma.is_ready():
        print("[ERROR] ChromaDB no está disponible")
        return False

    # 2. Obtener estadísticas
    stats = chroma.get_collection_stats()
    total_docs = stats.get('total_documents', 0)

    if total_docs == 0:
        print("[WARN]  No hay documentos en ChromaDB para migrar")
        return False

    print(f"[OK] ChromaDB listo: {total_docs} documentos encontrados")

    # 3. Conectar a PostgreSQL
    print("[INFO] Conectando a PostgreSQL...")
    postgres = PostgresVectorStore()

    if not postgres.is_ready():
        print("[ERROR] PostgreSQL no está disponible")
        print("[TIP] Asegúrate de tener DATABASE_URL configurado")
        return False

    print("[OK] PostgreSQL listo")

    # 4. Obtener TODOS los documentos de ChromaDB
    print(f"[INFO] Obteniendo {total_docs} documentos de ChromaDB...")
    
    try:
        collection = chroma.collection
        all_data = collection.get(
            include=['documents', 'metadatas', 'embeddings']
        )
        
        ids = all_data.get('ids', [])
        documents = all_data.get('documents', [])
        metadatas = all_data.get('metadatas', [])
        embeddings = all_data.get('embeddings', [])
        
        print(f"[OK] Datos obtenidos: {len(documents)} documentos")

    except Exception as e:
        print(f"[ERROR] Error obteniendo datos de ChromaDB: {e}")
        return False

    # 5. Preparar documentos para PostgreSQL
    print("[SYNC] Preparando documentos para PostgreSQL...")
    
    docs_to_insert = []
    embeddings_to_insert = []
    
    for i, (doc_id, doc_text, metadata, embedding) in enumerate(zip(ids, documents, metadatas, embeddings)):
        if not embedding:
            continue
        
        # Preparar documento en formato compatible
        doc = {
            'text': doc_text,
            'metadata': metadata
        }
        
        docs_to_insert.append(doc)
        embeddings_to_insert.append(embedding)
    
    print(f"[OK] {len(docs_to_insert)} documentos preparados")

    # 6. Insertar en PostgreSQL en lotes
    print("[SAVE] Insertando en PostgreSQL...")
    
    batch_size = 100
    total_batches = (len(docs_to_insert) + batch_size - 1) // batch_size
    
    successful = 0
    failed = 0
    
    for batch_num in tqdm(range(0, len(docs_to_insert), batch_size), 
                          desc="Migrando", 
                          total=total_batches):
        
        batch_docs = docs_to_insert[batch_num:batch_num + batch_size]
        batch_embeddings = embeddings_to_insert[batch_num:batch_num + batch_size]
        
        try:
            result = postgres.add_documents(batch_docs, batch_embeddings)
            if result:
                successful += len(batch_docs)
            else:
                failed += len(batch_docs)
        except Exception as e:
            print(f"[ERROR] Error en batch {batch_num//batch_size + 1}: {e}")
            failed += len(batch_docs)

    # 7. Verificar migración
    print("\n" + "=" * 60)
    print("[STATS] Resumen de migración:")
    print(f"   Total documentos: {total_docs}")
    print(f"   [OK] Exitosos: {successful}")
    print(f"   [ERROR] Fallidos: {failed}")

    # Verificar en PostgreSQL
    pg_stats = postgres.get_collection_stats()
    pg_total = pg_stats.get('total_documents', 0)

    print(f"\n[INFO] PostgreSQL ahora tiene: {pg_total} documentos")
    print(f"   Tamaño en disco: {pg_stats.get('table_size', 'N/A')}")

    if pg_total >= total_docs * 0.95:  # Al menos 95% migrado
        print("\n[OK] Migración EXITOSA")
        print("[TIP] Ahora puedes hacer deploy sin regenerar embeddings")
        return True
    else:
        print("\n[WARN]  Migración PARCIAL")
        print("[TIP] Algunos documentos no se migraron correctamente")
        return False


def verify_migration():
    """Verificar que la migración fue exitosa"""

    print("\n[SEARCH] Verificando migración...")
    
    chroma = ChromaManager()
    postgres = PostgresVectorStore()
    
    chroma_stats = chroma.get_collection_stats()
    postgres_stats = postgres.get_collection_stats()
    
    chroma_count = chroma_stats.get('total_documents', 0)
    postgres_count = postgres_stats.get('total_documents', 0)
    
    print(f"\n[STATS] Comparación:")
    print(f"   ChromaDB:   {chroma_count} documentos")
    print(f"   PostgreSQL: {postgres_count} documentos")

    if postgres_count >= chroma_count * 0.95:
        print("   [OK] Migración verificada correctamente")
    else:
        print("   [WARN]  Discrepancia detectada")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrar embeddings de ChromaDB a PostgreSQL')
    parser.add_argument('--verify', action='store_true', help='Solo verificar migración')
    
    args = parser.parse_args()
    
    if args.verify:
        verify_migration()
    else:
        success = migrate_embeddings()
        
        if success:
            print("\n" + "=" * 60)
            print("[DONE] ¡MIGRACIÓN COMPLETADA!")
            print("=" * 60)
            print("\nPróximos pasos:")
            print("1. git add .")
            print("2. git commit -m 'feat: Migrar embeddings a PostgreSQL'")
            print("3. git push origin main")
            print("4. Deploy en DigitalOcean será INSTANTÁNEO (sin regenerar)")
