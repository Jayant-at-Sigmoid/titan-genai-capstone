from typing import List, Dict, Any
from rag.vector_store import vector_store
from utils.logger import app_logger

class PolicyRetriever:
    @staticmethod
    def retrieve_relevant_policies(query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Queries FAISS vector store to find standard policy items related to the input violation string.
        """
        app_logger.info(f"Retrieving policies for query: '{query[:60]}...'")
        matches = vector_store.similarity_search(query, k=limit)
        
        # Format results nicely
        formatted_matches = []
        for match in matches:
            formatted_matches.append({
                "policy_name": match.get("source"),
                "page_number": match.get("page"),
                "clause_text": match.get("text"),
                "distance_score": match.get("score")
            })
            
        return formatted_matches

# Global policy retriever instance
policy_retriever = PolicyRetriever()
