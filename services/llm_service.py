import os
import json
import time
import re
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from typing import Dict, Any, Optional
from utils.logger import app_logger
from dotenv import load_dotenv

load_dotenv()

# Pricing constants for Bedrock Models (approximate cost per 1k tokens)
PRICE_SONNET_INPUT = 0.003
PRICE_SONNET_OUTPUT = 0.015
PRICE_HAIKU_INPUT = 0.00025
PRICE_HAIKU_OUTPUT = 0.00125

class BedrockLLMService:
    def __init__(self):
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.text_model = os.getenv("BEDROCK_TEXT_MODEL", "anthropic.claude-3-5-sonnet-20241022-v2:0")
        self.fast_model = os.getenv("BEDROCK_FAST_MODEL", "anthropic.claude-3-haiku-20240307-v1:0")
        
        # Token metrics tracking for Cost Optimization Engine
        self.metrics = {
            "total_calls": 0,
            "simulated_calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
            "total_latency_sec": 0.0
        }
        
        try:
            # Initialize Bedrock Client
            self.client = boto3.client(
                service_name="bedrock-runtime",
                region_name=self.region,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID") or None,
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY") or None
            )
            app_logger.info("AWS Bedrock runtime client initialized successfully.")
        except Exception as e:
            app_logger.error(f"AWS Bedrock client failed to initialize: {e}")
            raise e

    def invoke_model(
        self,
        prompt: str,
        model_type: str = "fast",
        temperature: float = 0.0,
        max_tokens: int = 4000
    ) -> Dict[str, Any]:
        """
        Invokes Claude model via Bedrock. Uses model_type = 'complex' (Sonnet) or 'fast' (Haiku).
        Returns a dictionary containing the parsed JSON model response, latency, and token details.
        """
        start_time = time.time()
        self.metrics["total_calls"] += 1
        model_id = self.text_model if model_type == "complex" else self.fast_model
        
        # Real AWS Bedrock invocation
        if "nova" in model_id:
            payload = {
                "inferenceConfig": {
                    "maxTokens": max_tokens,
                    "temperature": temperature
                },
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ]
            }
        else:
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        
        # Retry parameters
        max_retries = 3
        backoff_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                response = self.client.invoke_model(
                    modelId=model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps(payload)
                )
                
                response_body = json.loads(response.get("body").read().decode("utf-8"))
                latency = time.time() - start_time
                self.metrics["total_latency_sec"] += latency
                
                if "nova" in model_id:
                    in_tokens = response_body.get("usage", {}).get("inputTokens", len(prompt) // 4)
                    out_tokens = response_body.get("usage", {}).get("outputTokens", 100)
                    self._update_metrics_for_model(model_id, model_type, in_tokens, out_tokens, latency)
                    
                    content_list = response_body.get("output", {}).get("message", {}).get("content", [])
                    text_response = ""
                    for content in content_list:
                        if "text" in content:
                            text_response += content["text"]
                else:
                    in_tokens = response_body.get("usage", {}).get("input_tokens", len(prompt) // 4)
                    out_tokens = response_body.get("usage", {}).get("output_tokens", 100)
                    self._update_metrics_for_model(model_id, model_type, in_tokens, out_tokens, latency)
                    
                    content_list = response_body.get("content", [])
                    text_response = ""
                    for content in content_list:
                        if content.get("type") == "text":
                            text_response += content.get("text", "")
                
                # Attempt to extract and parse JSON from the response text
                parsed_json = self._extract_json(text_response)
                if parsed_json:
                    return parsed_json
                else:
                    app_logger.warning("LLM response did not contain valid JSON. Returning raw content.")
                    return {"violation_detected": False, "raw_response": text_response}
                    
            except (ClientError, BotoCoreError) as e:
                is_throttling = False
                if isinstance(e, ClientError):
                    error_code = e.response.get("Error", {}).get("Code", "")
                    if error_code in ["ThrottlingException", "RequestLimitExceeded", "TooManyRequestsException"]:
                        is_throttling = True
                        
                app_logger.warning(
                    f"Bedrock invocation failed on attempt {attempt + 1}: {e}. Throttling={is_throttling}"
                )
                
                if attempt < max_retries - 1:
                    sleep_time = backoff_delay * (2 ** attempt)
                    app_logger.info(f"Retrying in {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
                else:
                    app_logger.error("All retries exhausted for Bedrock LLM invocation.")
                    raise e
            except Exception as ex:
                app_logger.error(f"Unexpected error in LLM service: {ex}")
                raise ex

    def get_metrics(self) -> Dict[str, Any]:
        """Returns cumulative performance and cost metrics."""
        return self.metrics

    def _update_metrics_for_model(self, model_id: str, model_type: str, input_tokens: int, output_tokens: int, latency: float):
        """Updates internal billing and token count values."""
        self.metrics["input_tokens"] += input_tokens
        self.metrics["output_tokens"] += output_tokens
        
        # Calculate cost
        if "nova" in model_id:
            if model_type == "complex":
                cost = ((input_tokens / 1000) * 0.00006) + ((output_tokens / 1000) * 0.00024)
                model_name = "Nova Lite"
            else:
                cost = ((input_tokens / 1000) * 0.000035) + ((output_tokens / 1000) * 0.00014)
                model_name = "Nova Micro"
        else:
            if model_type == "complex":
                cost = ((input_tokens / 1000) * PRICE_SONNET_INPUT) + ((output_tokens / 1000) * PRICE_SONNET_OUTPUT)
                model_name = "Claude 3.5 Sonnet"
            else:
                cost = ((input_tokens / 1000) * PRICE_HAIKU_INPUT) + ((output_tokens / 1000) * PRICE_HAIKU_OUTPUT)
                model_name = "Claude 3 Haiku"
            
        self.metrics["estimated_cost_usd"] += cost

        try:
            from database.db import log_model_metric
            log_model_metric(model_name, latency, input_tokens, output_tokens, cost)
        except Exception as e:
            app_logger.error(f"Failed to write model metric to SQLite: {e}")

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Finds and parses the first JSON block within text."""
        try:
            match = re.search(r"(\{.*\})", text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            return json.loads(text)
        except Exception:
            return None

# Global reference instantiator
llm_service = BedrockLLMService()
