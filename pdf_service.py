# pdf_service.py
import os
import logging
from typing import List, Dict, Any
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings

logger = logging.getLogger(__name__)

class PDFService:
    def __init__(self, pdf_directory: str, cache_directory: str):
        # Initialize embeddings as None. It will be loaded on first use.
        self.embeddings = None
        self.cache_directory = cache_directory
        self.db = None

    def _load_embeddings(self):
        """Loads the SentenceTransformerEmbeddings model only if it hasn't been loaded yet."""
        if self.embeddings is None:
            print("🚀 Loading SentenceTransformer embeddings model...")
            try:
                self.embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
                print("✅ SentenceTransformer embeddings model loaded successfully.")
            except Exception as e:
                logger.error(f"Error loading SentenceTransformer embeddings: {e}")
                print("❌ Failed to load SentenceTransformer embeddings. PDF search functionality may be limited.")
                self.embeddings = None # Ensure it remains None if loading fails

    def _load_vector_db(self):
        """Loads the vector database only if it hasn't been loaded yet."""
        if self.db is None:
            # Ensure embeddings are loaded before attempting to load the DB
            self._load_embeddings()

            if self.embeddings is None: # Check again if embeddings failed to load
                print("⚠️ Embeddings model not available, cannot load vector database.")
                return

            try:
                print(f"📂 Loading FAISS database from: {self.cache_directory}")
                self.db = FAISS.load_local(
                    folder_path=self.cache_directory,
                    index_name="index",
                    embeddings=self.embeddings,
                    allow_dangerous_deserialization=True
                )
                print("✅ Vector database loaded successfully.")
            except Exception as e:
                logger.error(f"Error loading vector database: {e}")
                print("❌ Failed to load vector database. PDF search functionality will not be available.")
                self.db = None

    def search_documents(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        # Load embeddings and DB if not already loaded, right before the search
        self._load_vector_db()

        if not self.db:
            print("⚠️ Database not available. Document search is disabled.")
            return []
            
        print(f"🔍 Searching documents for query: '{query}' (k={k})")
        
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
            
            print(f"✅ Search completed. Found {len(formatted_results)} results.")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error during document search: {e}")
            return []