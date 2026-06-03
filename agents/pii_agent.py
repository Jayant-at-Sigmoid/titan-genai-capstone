from typing import List, Dict, Any
from services.llm_service import llm_service
from services.rule_service import rule_service
from prompts.pii_prompts import PII_DETECTION_SYSTEM_PROMPT, PII_DETECTION_USER_PROMPT
from utils.logger import app_logger

class PIIAgent:
    def __init__(self):
        self.system_prompt = PII_DETECTION_SYSTEM_PROMPT
        self.user_prompt = PII_DETECTION_USER_PROMPT

    def analyze_page(self, page_num: int, page_text: str) -> List[Dict[str, Any]]:
        """
        Scans page text for PII violations.
        Uses local regex pre-checks for cost optimization. If candidates are found,
        queries Claude Haiku to validate the classification in context.
        """
        app_logger.info(f"PII Agent checking page {page_num}...")
        
        # Cost Optimization: Regex Pre-check
        regex_matches = rule_service.pre_check_text(page_text, category_filter="PII")
        if not regex_matches:
            # If no PII regex matches, return empty violation set immediately (Cost Optimization)
            app_logger.info(f"Page {page_num} passed PII pre-check (No candidates matched).")
            return []
            
        app_logger.info(f"PII pre-check found {len(regex_matches)} candidates on page {page_num}. Invoking LLM verification...")
        
        # Inject candidate snippets as guidance context for LLM to review
        candidates_str = ", ".join([f"'{m['snippet']}' ({m['name']})" for m in regex_matches])
        guided_prompt = (
            f"{self.system_prompt}\n\n"
            f"Pre-check identified potential PII entities: {candidates_str}. "
            "Examine the text carefully to verify if these are actual PII disclosures."
        )
        
        user_formatted = self.user_prompt.format(page_num=page_num, page_text=page_text)
        
        try:
            result = llm_service.invoke_model(
                prompt=f"{guided_prompt}\n\n{user_formatted}",
                model_type="fast",  # Haiku is used for PII
                temperature=0.0
            )
            
            if result.get("violation_detected"):
                violation = {
                    "page_number": page_num,
                    "category": "PII",
                    "entity_type": result.get("entity_type"),
                    "severity": result.get("severity", "MEDIUM"),
                    "confidence": result.get("confidence", 0.9),
                    "snippet": result.get("snippet"),
                    "reason": result.get("reason"),
                    "remediation": result.get("remediation", "Redact this sequence")
                }
                return [violation]
                
            return []
        except Exception as e:
            app_logger.error(f"PII Agent invocation failed on page {page_num}: {e}")
            # If LLM fails, fall back to the regex precheck candidates as safe backup
            fallback_violations = []
            for match in regex_matches:
                fallback_violations.append({
                    "page_number": page_num,
                    "category": "PII",
                    "entity_type": match["name"],
                    "severity": match["severity"],
                    "confidence": 0.8,
                    "snippet": match["snippet"],
                    "reason": f"Flagged by regex precheck: {match['name']}.",
                    "remediation": "Redact sequence."
                })
            return fallback_violations

# Global agent instantiator
pii_agent = PIIAgent()
