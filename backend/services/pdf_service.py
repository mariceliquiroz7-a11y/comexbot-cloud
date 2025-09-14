import os
import pickle
from typing import List, Dict, Any, Optional
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings  # Nueva importación
from langchain.schema import Document
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFService:
    def __init__(self, pdf_directory: str = "data/pdfs", cache_directory: str = "data/cache"):
        """
        Inicializa el servicio de procesamiento de PDFs
        
        Args:
            pdf_directory: Directorio donde están los PDFs
            cache_directory: Directorio para cache de vectorstores
        """
        self.pdf_directory = Path(pdf_directory)
        self.cache_directory = Path(cache_directory)
        self.cache_directory.mkdir(parents=True, exist_ok=True)
        
        # Inicializar embeddings - Versión corregida
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}  # Ahora va dentro de model_kwargs
        )
        
        # Configurar text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        self.vectorstores = {}
        
    def _get_cache_path(self, pdf_name: str) -> Path:
        """Obtiene la ruta del cache para un PDF específico"""
        return self.cache_directory / f"{pdf_name}_vectorstore.pkl"
    
    def _load_cached_vectorstore(self, pdf_name: str) -> Optional[FAISS]:
        """Carga un vectorstore desde cache si existe"""
        cache_path = self._get_cache_path(pdf_name)
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                logger.warning(f"Error cargando cache para {pdf_name}: {e}")
                return None
        return None
    
    def _save_vectorstore_to_cache(self, pdf_name: str, vectorstore: FAISS):
        """Guarda un vectorstore en cache"""
        cache_path = self._get_cache_path(pdf_name)
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(vectorstore, f)
        except Exception as e:
            logger.warning(f"Error guardando cache para {pdf_name}: {e}")
    
    def _process_pdf(self, pdf_path: Path) -> List[Document]:
        """Procesa un PDF y extrae documentos"""
        try:
            loader = PyPDFLoader(str(pdf_path))
            documents = loader.load()
            
            # Dividir documentos en chunks
            chunks = self.text_splitter.split_documents(documents)
            
            # Agregar metadata adicional
            for chunk in chunks:
                chunk.metadata.update({
                    'source_file': pdf_path.name,
                    'file_path': str(pdf_path)
                })
            
            return chunks
        except Exception as e:
            logger.error(f"Error procesando {pdf_path}: {e}")
            return []
    
    def _create_vectorstore(self, documents: List[Document], pdf_name: str) -> Optional[FAISS]:
        """Crea un vectorstore desde documentos"""
        if not documents:
            return None
        
        try:
            vectorstore = FAISS.from_documents(documents, self.embeddings)
            return vectorstore
        except Exception as e:
            logger.error(f"Error creando vectorstore para {pdf_name}: {e}")
            return None
    
    def load_pdf(self, pdf_name: str) -> bool:
        """
        Carga un PDF específico y crea su vectorstore
        
        Args:
            pdf_name: Nombre del archivo PDF (sin extensión)
            
        Returns:
            bool: True si se cargó correctamente, False en caso contrario
        """
        # Intentar cargar desde cache primero
        vectorstore = self._load_cached_vectorstore(pdf_name)
        
        if vectorstore:
            self.vectorstores[pdf_name] = vectorstore
            print(f"✅ Cargado desde cache: {pdf_name}")
            return True
        
        # Si no hay cache, procesar el PDF
        pdf_path = self.pdf_directory / f"{pdf_name}.pdf"
        
        if not pdf_path.exists():
            logger.error(f"PDF no encontrado: {pdf_path}")
            return False
        
        print(f"📄 Procesando: {pdf_name}")
        documents = self._process_pdf(pdf_path)
        
        if not documents:
            logger.error(f"No se pudieron extraer documentos de {pdf_name}")
            return False
        
        vectorstore = self._create_vectorstore(documents, pdf_name)
        
        if vectorstore:
            self.vectorstores[pdf_name] = vectorstore
            self._save_vectorstore_to_cache(pdf_name, vectorstore)
            print(f"✅ Cargado: {pdf_name}")
            return True
        
        return False
    
    def load_all_pdfs(self) -> int:
        """
        Carga todos los PDFs del directorio
        
        Returns:
            int: Número de PDFs cargados exitosamente
        """
        if not self.pdf_directory.exists():
            logger.error(f"Directorio no encontrado: {self.pdf_directory}")
            return 0
        
        pdf_files = list(self.pdf_directory.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No se encontraron PDFs en {self.pdf_directory}")
            return 0
        
        loaded_count = 0
        for pdf_path in pdf_files:
            pdf_name = pdf_path.stem  # Nombre sin extensión
            if self.load_pdf(pdf_name):
                loaded_count += 1
        
        return loaded_count
    
    def search_documents(self, query: str, pdf_names: List[str] = None, k: int = 5) -> List[Dict[str, Any]]:
        """
        Busca documentos relevantes usando similarity search
        
        Args:
            query: Consulta de búsqueda
            pdf_names: Lista de nombres de PDFs específicos para buscar (opcional)
            k: Número máximo de resultados por PDF
            
        Returns:
            List[Dict]: Lista de documentos encontrados con metadata
        """
        if not self.vectorstores:
            logger.warning("No hay vectorstores cargados")
            return []
        
        # Si no se especifican PDFs, buscar en todos
        if pdf_names is None:
            pdf_names = list(self.vectorstores.keys())
        
        results = []
        
        for pdf_name in pdf_names:
            if pdf_name not in self.vectorstores:
                logger.warning(f"PDF no encontrado en vectorstores: {pdf_name}")
                continue
            
            try:
                vectorstore = self.vectorstores[pdf_name]
                docs_with_scores = vectorstore.similarity_search_with_score(query, k=k)
                
                for doc, score in docs_with_scores:
                    results.append({
                        'content': doc.page_content,
                        'metadata': doc.metadata,
                        'score': score,
                        'source_pdf': pdf_name
                    })
            except Exception as e:
                logger.error(f"Error buscando en {pdf_name}: {e}")
        
        # Ordenar por score (menor score = mayor similitud)
        results.sort(key=lambda x: x['score'])
        
        return results
    
    def get_vectorstore_info(self) -> Dict[str, Any]:
        """Retorna información sobre los vectorstores cargados"""
        info = {
            'total_vectorstores': len(self.vectorstores),
            'loaded_pdfs': list(self.vectorstores.keys()),
            'cache_directory': str(self.cache_directory),
            'pdf_directory': str(self.pdf_directory)
        }
        
        return info