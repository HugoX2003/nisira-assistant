#!/usr/bin/env python
"""
Script para diagnosticar los embeddings en PostgreSQL de producción
"""
import os
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

def main():
    # Verificar que tenemos la URL de la base de datos
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("[ERROR] DATABASE_URL no está configurada")
        print("   Configura la variable de entorno con la URL de PostgreSQL de producción")
        return

    print(f"[INFO] Conectando a: {database_url[:50]}...")

    try:
        import psycopg2
    except ImportError:
        print("[ERROR] psycopg2 no está instalado. Ejecuta: pip install psycopg2-binary")
        return

    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()

        # 1. Contar total de embeddings
        cur.execute("SELECT COUNT(*) FROM rag_embeddings")
        total = cur.fetchone()[0]
        print(f"\n[STATS] Total de embeddings en PostgreSQL: {total}")

        # 2. Listar documentos únicos con sus chunks
        print("\n[DIR] Documentos únicos por nombre de archivo:")
        cur.execute("""
            SELECT 
                COALESCE(metadata->>'source', metadata->>'file_name', 'Desconocido') as doc_name,
                COUNT(*) as chunks
            FROM rag_embeddings
            GROUP BY COALESCE(metadata->>'source', metadata->>'file_name', 'Desconocido')
            ORDER BY doc_name
        """)
        
        for row in cur.fetchall():
            doc_name, chunks = row
            # Resaltar si contiene "despliegue" o "gua"
            highlight = ""
            if 'despliegue' in doc_name.lower() or 'gua' in doc_name.lower():
                highlight = " [GOAL] <-- RELEVANTE"
            print(f"   - {doc_name}: {chunks} chunks{highlight}")

        # 3. Buscar específicamente documentos que contengan "despliegue" o "gua"
        print("\n[SEARCH] Buscando documentos con 'despliegue' o 'gua' en el nombre:")
        cur.execute("""
            SELECT DISTINCT 
                COALESCE(metadata->>'source', metadata->>'file_name', 'Desconocido') as doc_name
            FROM rag_embeddings
            WHERE metadata->>'source' ILIKE '%despliegue%'
               OR metadata->>'source' ILIKE '%gua%'
               OR metadata->>'file_name' ILIKE '%despliegue%'
               OR metadata->>'file_name' ILIKE '%gua%'
        """)
        
        results = cur.fetchall()
        if results:
            for row in results:
                print(f"   [OK] {row[0]}")
        else:
            print("   [ERROR] No se encontraron documentos con esos términos en el nombre")

        # 4. Buscar en el contenido de los chunks
        print("\n[SEARCH] Buscando chunks que contengan 'autores' Y 'despliegue':")
        cur.execute("""
            SELECT 
                COALESCE(metadata->>'source', 'Desconocido') as doc_name,
                LEFT(chunk_text, 200) as preview
            FROM rag_embeddings
            WHERE chunk_text ILIKE '%autor%'
              AND (chunk_text ILIKE '%despliegue%' OR metadata->>'source' ILIKE '%despliegue%')
            LIMIT 5
        """)
        
        results = cur.fetchall()
        if results:
            for row in results:
                print(f"\n   [INFO] Documento: {row[0]}")
                print(f"   [NOTE] Preview: {row[1][:150]}...")
        else:
            print("   [ERROR] No se encontraron chunks con 'autores' y 'despliegue'")

        # 5. Verificar dimensión de embeddings
        print("\n[INFO] Verificando dimensión de embeddings:")
        cur.execute("""
            SELECT 
                vector_dims(embedding_vector) as dim
            FROM rag_embeddings
            LIMIT 1
        """)
        result = cur.fetchone()
        if result:
            print(f"   Dimensión: {result[0]}")
        
        cur.close()
        conn.close()
        print("\n[OK] Conexión cerrada")

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
