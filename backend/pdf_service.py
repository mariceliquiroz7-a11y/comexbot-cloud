import os
import logging
from typing import List, Dict, Any
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings

logger = logging.getLogger(__name__)

class PDFService:
    def __init__(self, pdf_directory: str, cache_directory: str):
        self.embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        self.cache_directory = cache_directory
        self.db = None
        self._load_vector_db()

    def _load_vector_db(self):
        try:
            # ⬇️⬇️⬇️ CÓDIGO CORREGIDO ⬇️⬇️⬇️
            # Carga la base de datos vectorial principal
            self.db = FAISS.load_local(
                folder_path=self.cache_directory, 
                index_name="index", # Carga el archivo llamado 'index'
                embeddings=self.embeddings,
                allow_dangerous_deserialization=True
            )
            # ⬆️⬆️⬆️ CÓDIGO CORREGIDO ⬆️⬆️⬆️
            print("✅ Base de datos vectorial cargada correctamente.")
        except Exception as e:
            logger.error(f"Error al cargar la base de datos vectorial: {e}")
            print("❌ No se pudo cargar la base de datos vectorial. El servicio de búsqueda en PDF no estará disponible.")
            self.db = None

    def search_documents(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        if not self.db:
            print("⚠️ Base de datos no disponible. La búsqueda de documentos está deshabilitada.")
            return []
            
        print(f"🔍 Buscando documentos para la consulta: '{query}' (k={k})")
        
        try:
            results = self.db.similarity_search_with_score(query, k=k)
            
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "source_pdf": doc.metadata.get("source", "N/A"),
                    "page": doc.metadata.get("page", "N/A"),
                    "score": score
                })
            
            print(f"✅ Búsqueda completada. Encontrados {len(formatted_results)} resultados.")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error durante la búsqueda de documentos: {e}")
            return []