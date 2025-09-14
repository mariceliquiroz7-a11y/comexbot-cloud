import os
import re
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings

docs_path = "docs"
vectorstore_path = "vectorstore"

# Crear carpeta vectorstore si no existe
os.makedirs(vectorstore_path, exist_ok=True)

embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

def clean_filename(filename):
    """Limpiar nombre de archivo para uso seguro"""
    # Remover extensión .pdf
    name = filename.replace('.pdf', '')
    # Mantener solo letras, números y algunos caracteres seguros
    name = re.sub(r'[^\w\s-]', '', name)
    # Reemplazar espacios y guiones múltiples por underscore
    name = re.sub(r'[-\s]+', '_', name)
    # Limitar longitud
    name = name[:30]  # Máximo 30 caracteres
    # Remover underscores al inicio y final
    name = name.strip('_')
    return name if name else "documento"

for file in os.listdir(docs_path):
    if file.lower().endswith(".pdf"):
        try:
            print(f"\n🔄 Procesando: {file}")
            
            loader = PyPDFLoader(os.path.join(docs_path, file))
            docs = loader.load()
            print(f"   📄 Cargado con {len(docs)} páginas")
            
            if docs:  # Solo si hay contenido
                db = FAISS.from_documents(docs, embeddings)
                
                # Nombre limpio y corto para la carpeta
                clean_name = clean_filename(file)
                vectorstore_dir = os.path.join(vectorstore_path, clean_name)
                
                # Crear directorio si no existe
                os.makedirs(vectorstore_dir, exist_ok=True)
                
                # Guardar vectorstore
                db.save_local(vectorstore_dir)
                print(f"   ✅ Vectorstore creado: {clean_name}")
            else:
                print(f"   ⚠️ No se pudo extraer contenido")
                
        except Exception as e:
            print(f"   ❌ Error procesando {file}: {str(e)}")

print("\n🎉 ¡Procesamiento completado!")