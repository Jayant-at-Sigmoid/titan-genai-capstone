import os
from typing import List, Dict, Any
from rag.policy_loader import policy_loader
from rag.retriever import policy_retriever
from rag.vector_store import vector_store
from database.db import get_policies_list
from utils.logger import app_logger

class PolicyVectorService:
    @staticmethod
    def index_policy_file(file_path: str) -> Dict[str, Any]:
        """Indices a policy document in the system."""
        if not os.path.exists(file_path):
            app_logger.error(f"Policy file not found: {file_path}")
            return {"success": False, "error": "File not found"}
        return policy_loader.load_and_index_policy(file_path)

    @staticmethod
    def search_policies(query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Queries policies by query string."""
        return policy_retriever.retrieve_relevant_policies(query, limit)

    @staticmethod
    def get_policies() -> List[Dict[str, Any]]:
        """Returns metadata of uploaded policies."""
        return get_policies_list()

    @staticmethod
    def reset_vector_store():
        """Clears all vectorized policies."""
        vector_store.clear_all()
        app_logger.info("Policies vector database reset completed.")

# Global service instance
vector_service = PolicyVectorService()
