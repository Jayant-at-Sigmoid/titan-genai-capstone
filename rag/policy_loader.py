import os
import fitz  # PyMuPDF
from typing import List, Dict, Any
from rag.vector_store import vector_store
from database.db import add_policy_document
from utils.logger import app_logger

class PolicyLoader:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def load_and_index_policy(self, file_path: str) -> Dict[str, Any]:
        """
        Parses a policy PDF, chunks the text, indices in FAISS, and records in SQLite.
        """
        filename = os.path.basename(file_path)
        app_logger.info(f"Ingesting policy document: {filename}...")
        
        try:
            doc = fitz.open(file_path)
            chunks = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                # Check for empty text
                if not text.strip():
                    continue
                    
                # Clean text a bit
                text = " ".join(text.split())
                
                # Dynamic sliding window chunking
                start = 0
                while start < len(text):
                    end = start + self.chunk_size
                    chunk_text = text[start:end]
                    
                    chunks.append({
                        "text": chunk_text,
                        "source": filename,
                        "page": page_num + 1
                    })
                    
                    # Advance by step size (chunk_size - overlap)
                    start += (self.chunk_size - self.chunk_overlap)
            
            doc.close()
            
            # Save vectors to FAISS index
            if chunks:
                vector_store.add_documents(chunks)
                
            # Log inside SQLite
            policy_id = add_policy_document(filename, file_path)
            
            app_logger.info(f"Successfully processed policy document. Policy ID: {policy_id}, Chunks: {len(chunks)}.")
            return {
                "policy_id": policy_id,
                "filename": filename,
                "chunks_count": len(chunks),
                "success": True
            }
        except Exception as e:
            app_logger.error(f"Error loading policy '{filename}': {e}")
            return {
                "filename": filename,
                "success": False,
                "error": str(e)
            }

# Global policy loader
policy_loader = PolicyLoader()
