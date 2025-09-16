import os
import logging
from typing import List, Dict, Any
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain.docstore.document import Document

logger = logging.getLogger(__name__)

class PDFService:
    def __init__(self, db: FAISS):
        self.db = db

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