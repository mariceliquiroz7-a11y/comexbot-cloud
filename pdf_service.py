# pdf_service.py
import os
import logging
from typing import List, Dict, Any
from langchain_community.vectorstores import FAISS
# Import the specific embedding class if you were using HuggingFaceEmbeddings before.
# If you stick to SentenceTransformerEmbeddings, this import might not be needed
# unless you're switching to the newer langchain_huggingface package.
# from langchain_huggingface import HuggingFaceEmbeddings 
from langchain_community.embeddings import SentenceTransformerEmbeddings # Keep this if you're using SentenceTransformer

logger = logging.getLogger(__name__)

class PDFService:
    def __init__(self, pdf_directory: str, cache_directory: str):
        # Initialize embeddings to None. It will be loaded on demand.
        self.embeddings = None  
        self.cache_directory = cache_directory
        self.db = None

    def _load_embeddings(self):
        """Loads the SentenceTransformer embeddings model lazily."""
        if self.embeddings is None:
            print("🚀 Cargando modelo de embeddings SentenceTransformer...")
            # Use the correct class based on your installation.
            # If you installed `langchain-huggingface`, you might use:
            # self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            # Otherwise, SentenceTransformerEmbeddings is fine.
            self.embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
            print("✅ Modelo de embeddings cargado correctamente.")

    def _load_vector_db(self):
        """Loads the vector database lazily, ensuring embeddings are loaded first."""
        if self.db is None:
            # Ensure embeddings are loaded before loading the DB
            self._load_embeddings()
            
            try:
                self.db = FAISS.load_local(
                    folder_path=self.cache_directory, 
                    index_name="index", 
                    embeddings=self.embeddings, # Use the loaded embeddings
                    allow_dangerous_deserialization=True
                )
                print("✅ Base de datos vectorial cargada correctamente.")
            except FileNotFoundError: # More specific error for missing files
                logger.error(f"Error: Vector store files not found in {self.cache_directory}. Please run ingest_docs.py.")
                print("❌ No se pudo cargar la base de datos vectorial. Archivos no encontrados.")
                self.db = None
            except Exception as e:
                logger.error(f"Error al cargar la base de datos vectorial: {e}")
                print("❌ No se pudo cargar la base de datos vectorial. El servicio de búsqueda en PDF no estará disponible.")
                self.db = None

    def search_documents(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        # This is where the loading of embeddings and DB will happen on first use
        self._load_vector_db()

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