import boto3
import os
from dotenv import load_dotenv

load_dotenv()

client = boto3.client(
    service_name="bedrock",
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

response = client.list_foundation_models()
for model in response.get("modelSummaries", []):
    modes = model.get("outputModalities", [])
    if "TEXT" in modes and "EMBEDDING" not in model.get("inputModalities", []):
        print(f"- ID: {model.get('modelId')} ({model.get('modelName')}) | Lifecycle: {model.get('modelLifecycle', {}).get('status')}")
