import os
import json
import boto3
from typing import List
from utils.logger import app_logger
from dotenv import load_dotenv

load_dotenv()

class BedrockEmbeddingService:
    def __init__(self):
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.model_id = os.getenv("BEDROCK_EMBEDDING_MODEL", "amazon.titan-embed-text-v2:0")
        
        try:
            self.client = boto3.client(
                service_name="bedrock-runtime",
                region_name=self.region,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID") or None,
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY") or None
            )
            app_logger.info("AWS Bedrock runtime client for Embeddings initialized.")
        except Exception as e:
            app_logger.error(f"AWS Bedrock client for Embeddings failed to initialize: {e}")
            raise e

    def get_embedding(self, text: str) -> List[float]:
        """Generates a 1536-dimensional embedding vector for input text."""
        payload = {
            "inputText": text,
            "dimensions": 1024
        }
        
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(payload)
            )
            response_body = json.loads(response.get("body").read().decode("utf-8"))
            embedding = response_body.get("embedding", [])
            return embedding
        except Exception as e:
            app_logger.error(f"Failed to generate Titan Embedding via Bedrock: {e}")
            raise e

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a batch of texts."""
        return [self.get_embedding(t) for t in texts]

# Global reference instantiator
embedding_service = BedrockEmbeddingService()
