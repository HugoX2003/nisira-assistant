#!/usr/bin/env python
"""Script para inspeccionar documentos en ChromaDB"""

from rag_system.vector_store.chroma_manager import ChromaManager

# Inicializar ChromaDB
cm = ChromaManager()

# Obtener documentos
results = cm.collection.get(limit=50, include=['documents', 'metadatas'])

# Filtrar documentos con contenido real (más de 100 caracteres)
docs_with_content = [
    (doc, meta) 
    for doc, meta in zip(results['documents'], results['metadatas']) 
    if len(doc) > 100
]

print(f"=== DOCUMENTOS CON CONTENIDO ===")
print(f"Total fragmentos en DB: {cm.collection.count()}")
print(f"Fragmentos con contenido >100 chars: {len(docs_with_content)}")
print("\n" + "="*80 + "\n")

# Mostrar los primeros 5 documentos
for i, (doc, meta) in enumerate(docs_with_content[:5], 1):
    source = meta.get('source', 'N/A')
    print(f"[Documento {i}]")
    print(f"Archivo: {source}")
    print(f"Tamaño: {len(doc)} caracteres")
    print(f"Contenido (primeros 500 chars):")
    print(doc[:500])
    print("\n" + "="*80 + "\n")

# Mostrar tipos de archivos únicos
unique_sources = set(meta.get('source', 'N/A') for meta in results['metadatas'])
print(f"\n=== ARCHIVOS ÚNICOS ({len(unique_sources)}) ===")
for source in sorted(unique_sources)[:20]:
    print(f"  - {source}")
