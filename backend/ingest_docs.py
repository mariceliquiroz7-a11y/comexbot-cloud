import os
import re
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain.docstore.document import Document

# ⬇️⬇️⬇️ CÓDIGO CORREGIDO ⬇️⬇️⬇️

# La carpeta 'docs' está en el mismo directorio que el script (backend)
docs_path = os.path.join(os.path.dirname(__file__), "docs")

# La carpeta 'vectorstore' que contendrá el índice principal está en la raíz
parent_dir = os.path.dirname(os.path.dirname(__file__))
vectorstore_path = os.path.join(parent_dir, "vectorstore")

# Crear carpeta vectorstore si no existe
os.makedirs(vectorstore_path, exist_ok=True)

embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

def get_all_pdf_docs(docs_folder):
    """Carga todos los documentos PDF de la carpeta especificada."""
    all_docs = []
    for file in os.listdir(docs_folder):
        if file.lower().endswith(".pdf"):
            try:
                print(f"\n🔄 Procesando: {file}")
                loader = PyPDFLoader(os.path.join(docs_folder, file))
                docs = loader.load()
                print(f"   📄 Cargado con {len(docs)} páginas")
                all_docs.extend(docs)
            except Exception as e:
                print(f"   ❌ Error procesando {file}: {str(e)}")
    return all_docs

print("🚀 Iniciando la carga de documentos PDF...")

# Cargar todos los PDFs en una sola lista de documentos
documents = get_all_pdf_docs(docs_path)

if not documents:
    print("⚠️ No se encontraron documentos PDF para procesar. Asegúrate de que están en la carpeta 'backend/docs'.")
else:
    print(f"\n✅ Cargados {len(documents)} páginas de documentos en total.")

    # Crear una única base de datos vectorial a partir de todos los documentos
    print("🧠 Creando la base de datos vectorial...")
    db = FAISS.from_documents(documents, embeddings)

    # Guardar la base de datos vectorial principal en la raíz
    db.save_local(vectorstore_path)
    
    print("\n🎉 ¡Procesamiento y guardado de la base de datos principal completado!")
    print(f"La base de datos se encuentra en la ruta: {vectorstore_path}")