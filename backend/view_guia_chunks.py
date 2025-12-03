#!/usr/bin/env python
"""Ver chunks de Gua_de_Despliegue"""
import os
import psycopg2

database_url = os.getenv('DATABASE_URL')
conn = psycopg2.connect(database_url)
cur = conn.cursor()

cur.execute("""
    SELECT chunk_text, metadata->>'source'
    FROM rag_embeddings
    WHERE metadata->>'source' ILIKE '%Gua_de_Despliegue%'
""")

for i, row in enumerate(cur.fetchall()):
    print(f"\n{'='*80}")
    print(f"Chunk {i+1} de {row[1]}")
    print('='*80)
    print(row[0][:800])

cur.close()
conn.close()
