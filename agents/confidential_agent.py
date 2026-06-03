from typing import List, Dict, Any
from services.llm_service import llm_service
from services.rule_service import rule_service
from prompts.confidential_prompts import CONFIDENTIAL_DETECTION_SYSTEM_PROMPT, CONFIDENTIAL_DETECTION_USER_PROMPT
from utils.logger import app_logger

class ConfidentialAgent:
    def __init__(self):
        self.system_prompt = CONFIDENTIAL_DETECTION_SYSTEM_PROMPT
        self.user_prompt = CONFIDENTIAL_DETECTION_USER_PROMPT

    def analyze_page(self, page_num: int, page_text: str) -> List[Dict[str, Any]]:
        """
        Scans page text for Confidential information leaks.
        Uses Claude Sonnet (complex model) for deep logical reasoning.
        """
        app_logger.info(f"Confidential Agent checking page {page_num}...")
        
        # Cost Optimization pre-check
        regex_matches = rule_service.pre_check_text(page_text, category_filter="Confidential")
        
        # If no regex flags match and text length is tiny, we might bypass, but confidential analysis 
        # is complex and needs semantic context. We will invoke LLM if keywords or general markers match.
        # Check if contains any general business keywords if regex_matches is empty to avoid scanning raw empty content
        business_keywords = ["revenue", "project", "ebitda", "margin", "patent", "code", "client", "salary", "confidential", "proprietary", "secret"]
        has_keywords = any(kw in page_text.lower() for kw in business_keywords)
        
        if not regex_matches and not has_keywords:
            app_logger.info(f"Page {page_num} bypassed by Confidential Agent (No corporate risk keywords present).")
            return []

        user_formatted = self.user_prompt.format(page_num=page_num, page_text=page_text)
        
        try:
            result = llm_service.invoke_model(
                prompt=f"{self.system_prompt}\n\n{user_formatted}",
                model_type="complex",  # Claude Sonnet
                temperature=0.0
            )
            
            if result.get("violation_detected"):
                violation = {
                    "page_number": page_num,
                    "category": "Confidential",
                    "entity_type": result.get("entity_type"),
                    "severity": result.get("severity", "HIGH"),
                    "confidence": result.get("confidence", 0.9),
                    "snippet": result.get("snippet"),
                    "reason": result.get("reason"),
                    "remediation": result.get("remediation", "Restrict document access")
                }
                return [violation]
                
            return []
        except Exception as e:
            app_logger.error(f"Confidential Agent invocation failed on page {page_num}: {e}")
            # SQLite fallback for regex rules matched
            fallback_violations = []
            for match in regex_matches:
                fallback_violations.append({
                    "page_number": page_num,
                    "category": "Confidential",
                    "entity_type": match["name"],
                    "severity": match["severity"],
                    "confidence": 0.7,
                    "snippet": match["snippet"],
                    "reason": f"Flagged by regex precheck: {match['name']}.",
                    "remediation": "Restrict document distribution."
                })
            return fallback_violations

# Global agent instantiator
confidential_agent = ConfidentialAgent()
