import boto3
import os
from dotenv import load_dotenv

load_dotenv()

try:
    client = boto3.client(
        service_name="bedrock",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )
    response = client.list_foundation_models()
    print("Available Models:")
    for model in response.get("modelSummaries", []):
        if "anthropic" in model.get("modelId", "") or "titan" in model.get("modelId", ""):
            print(f"- ID: {model.get('modelId')}")
            print(f"  Name: {model.get('modelName')}")
            print(f"  Status: {model.get('modelLifecycle', {}).get('status')}")
except Exception as e:
    print(f"Error querying Bedrock: {e}")
