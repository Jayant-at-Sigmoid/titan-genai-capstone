from typing import List, Dict, Any
from services.llm_service import llm_service
from services.rule_service import rule_service
from prompts.abuse_prompts import ABUSE_DETECTION_SYSTEM_PROMPT, ABUSE_DETECTION_USER_PROMPT
from utils.logger import app_logger

class AbuseAgent:
    def __init__(self):
        self.system_prompt = ABUSE_DETECTION_SYSTEM_PROMPT
        self.user_prompt = ABUSE_DETECTION_USER_PROMPT

    def analyze_page(self, page_num: int, page_text: str) -> List[Dict[str, Any]]:
        """
        Scans page text for abusive, threatening, or unlawful content.
        Uses Claude Haiku (fast model) for detection.
        """
        app_logger.info(f"Abuse Agent checking page {page_num}...")
        
        # Regex safety pre-check
        regex_matches = rule_service.pre_check_text(page_text, category_filter="Abuse")
        
        # Common safety words triggers
        safety_triggers = ["kill", "destroy", "extort", "blackmail", "illegal", "threat", "harass", "hate", "abuse", "fraud"]
        has_triggers = any(trig in page_text.lower() for trig in safety_triggers)
        
        if not regex_matches and not has_triggers:
            app_logger.info(f"Page {page_num} bypassed by Abuse Agent (No threat indicators present).")
            return []

        user_formatted = self.user_prompt.format(page_num=page_num, page_text=page_text)
        
        try:
            result = llm_service.invoke_model(
                prompt=f"{self.system_prompt}\n\n{user_formatted}",
                model_type="fast",  # Haiku is used for safety checks
                temperature=0.0
            )
            
            if result.get("violation_detected"):
                violation = {
                    "page_number": page_num,
                    "category": "Abuse",
                    "entity_type": result.get("entity_type"),
                    "severity": result.get("severity", "CRITICAL"),
                    "confidence": result.get("confidence", 0.95),
                    "snippet": result.get("snippet"),
                    "reason": result.get("reason"),
                    "remediation": result.get("remediation", "Delete or quarantine document")
                }
                return [violation]
                
            return []
        except Exception as e:
            app_logger.error(f"Abuse Agent invocation failed on page {page_num}: {e}")
            fallback_violations = []
            for match in regex_matches:
                fallback_violations.append({
                    "page_number": page_num,
                    "category": "Abuse",
                    "entity_type": match["name"],
                    "severity": match["severity"],
                    "confidence": 0.8,
                    "snippet": match["snippet"],
                    "reason": f"Flagged by safety precheck: {match['name']}.",
                    "remediation": "Audit content and remove threats."
                })
            return fallback_violations

# Global agent instantiator
abuse_agent = AbuseAgent()
