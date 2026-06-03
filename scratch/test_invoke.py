import boto3
import os
import json
from dotenv import load_dotenv

load_dotenv()

client = boto3.client(
    service_name="bedrock-runtime",
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

# Test Llama 3, Llama 3.1, Mistral, and Nova model payloads
tests = [
    {
        "id": "meta.llama3-1-8b-instruct-v1:0",
        "payload": {
            "prompt": "<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\nHello<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
            "max_gen_len": 50,
            "temperature": 0.0
        }
    },
    {
        "id": "amazon.nova-lite-v1:0",
        "payload": {
            "inferenceConfig": {
                "maxTokens": 50,
                "temperature": 0.0
            },
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": "Hello"}]
                }
            ]
        }
    },
    {
        "id": "amazon.nova-micro-v1:0",
        "payload": {
            "inferenceConfig": {
                "maxTokens": 50,
                "temperature": 0.0
            },
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": "Hello"}]
                }
            ]
        }
    },
    {
        "id": "mistral.mistral-large-2402-v1:0",
        "payload": {
            "prompt": "<s>[INST] Hello [/INST]",
            "max_tokens": 50,
            "temperature": 0.0
        }
    }
]

for test in tests:
    model = test["id"]
    payload = test["payload"]
    print(f"\nTesting model: {model}")
    try:
        response = client.invoke_model(
            modelId=model,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(payload)
        )
        body = json.loads(response.get("body").read().decode("utf-8"))
        print(f"Success!")
        print(body)
    except Exception as e:
        print(f"Failed: {e}")
