import os
import pickle
import numpy as np
import faiss
from typing import List, Dict, Any
from services.embedding_service import embedding_service
from utils.logger import app_logger

# Define local directory for FAISS storage
INDEX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index")
INDEX_FILE = os.path.join(INDEX_DIR, "faiss.index")
METADATA_FILE = os.path.join(INDEX_DIR, "metadata.pkl")

class FAISSVectorStore:
    def __init__(self, dimension: int = 1024):
        self.dimension = dimension
        self.index = None
        self.metadata: List[Dict[str, Any]] = []
        os.makedirs(INDEX_DIR, exist_ok=True)
        self._load_index()

    def _load_index(self):
        """Loads FAISS index and metadata from disk if they exist."""
        try:
            if os.path.exists(INDEX_FILE) and os.path.exists(METADATA_FILE):
                self.index = faiss.read_index(INDEX_FILE)
                with open(METADATA_FILE, "rb") as f:
                    self.metadata = pickle.load(f)
                app_logger.info(f"Loaded existing FAISS index with {len(self.metadata)} records.")
            else:
                self.index = faiss.IndexFlatL2(self.dimension)
                self.metadata = []
                app_logger.info("Initialized new empty FAISS IndexFlatL2 index.")
        except Exception as e:
            app_logger.error(f"Error loading FAISS index: {e}. Reinitializing.")
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = []

    def _save_index(self):
        """Persists the FAISS index and metadata to disk."""
        try:
            faiss.write_index(self.index, INDEX_FILE)
            with open(METADATA_FILE, "wb") as f:
                pickle.dump(self.metadata, f)
            app_logger.info(f"Saved FAISS index to {INDEX_FILE} successfully.")
        except Exception as e:
            app_logger.error(f"Error saving FAISS index: {e}")

    def add_documents(self, chunks: List[Dict[str, Any]]):
        """
        Embeds and adds text chunks to the vector store.
        Each chunk is dict: {"text": str, "source": str, "page": int}
        """
        if not chunks:
            return
            
        app_logger.info(f"Vectorizing {len(chunks)} document chunks...")
        texts = [chunk["text"] for chunk in chunks]
        embeddings = embedding_service.get_embeddings_batch(texts)
        
        # Convert to numpy array of float32
        embeddings_np = np.array(embeddings).astype(np.float32)
        
        # Add to FAISS index
        self.index.add(embeddings_np)
        
        # Append metadata
        self.metadata.extend(chunks)
        self._save_index()

    def similarity_search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Queries the vector index for top k matching document chunks."""
        if not self.index or self.index.ntotal == 0:
            app_logger.warning("FAISS search requested on an empty index.")
            return []
            
        try:
            query_embedding = embedding_service.get_embedding(query)
            query_np = np.array([query_embedding]).astype(np.float32)
            
            distances, indices = self.index.search(query_np, k)
            
            results = []
            for i, idx in enumerate(indices[0]):
                if idx == -1 or idx >= len(self.metadata):
                    continue
                chunk_meta = self.metadata[idx].copy()
                chunk_meta["score"] = float(distances[0][i])
                results.append(chunk_meta)
                
            return results
        except Exception as e:
            app_logger.error(f"Error executing FAISS similarity search: {e}")
            return []

    def clear_all(self):
        """Clears the local vector index and database contents."""
        try:
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = []
            if os.path.exists(INDEX_FILE):
                os.remove(INDEX_FILE)
            if os.path.exists(METADATA_FILE):
                os.remove(METADATA_FILE)
            app_logger.info("Cleared FAISS index and metadata cache.")
        except Exception as e:
            app_logger.error(f"Error resetting FAISS vector store: {e}")

# Global vector store instance
vector_store = FAISSVectorStore()
