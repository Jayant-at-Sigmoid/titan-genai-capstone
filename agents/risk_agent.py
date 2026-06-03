from typing import List, Dict, Any
from services.llm_service import llm_service
from utils.logger import app_logger

class RiskScoringEngine:
    def calculate_risk(self, violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates compliance score and maps overall risk levels (LOW, MEDIUM, HIGH, CRITICAL).
        Generates an executive risk explanation summary using Claude Sonnet.
        """
        app_logger.info("Risk Scoring Engine running analysis...")
        
        # 1. Base Score calculation
        score = 100.0
        critical_count = 0
        high_count = 0
        medium_count = 0
        low_count = 0
        
        for v in violations:
            severity = v["severity"].upper()
            if severity == "CRITICAL":
                score -= 30
                critical_count += 1
            elif severity == "HIGH":
                score -= 15
                high_count += 1
            elif severity == "MEDIUM":
                score -= 7
                medium_count += 1
            else:
                score -= 2
                low_count += 1
                
        score = max(0.0, score)
        
        # 2. Risk Level Map
        if score >= 90:
            overall_risk = "LOW"
        elif score >= 70:
            overall_risk = "MEDIUM"
        elif score >= 45:
            overall_risk = "HIGH"
        else:
            overall_risk = "CRITICAL"
            
        # 3. Request LLM Summary
        summary = ""
        if len(violations) == 0:
            summary = "The document was analyzed and found fully compliant. No policy, PII, safety, or confidentiality violations were detected."
        else:
            prompt = f"""You are a staff-level Governance Risk Compliance (GRC) Auditor.
Provide an executive risk summary for a PDF document scan with the following findings:
- Compliance Score: {score}/100
- Risk Level: {overall_risk}
- Violations breakdown: {critical_count} CRITICAL, {high_count} HIGH, {medium_count} MEDIUM, {low_count} LOW.

Details of violations detected:
{violations}

Generate a professional, concise executive summary (3-4 sentences) outlining:
1. The overall risk exposure of the document.
2. The primary categories of policy leaks (PII, Confidentiality, Safety).
3. Recommendation for remediation.

Return ONLY the summary string. Do not wrap in JSON or any markdown comments.
"""
            try:
                # Sonnet used for GRC explanation layer
                summary = llm_service.invoke_model(
                    prompt=prompt,
                    model_type="complex",
                    temperature=0.0
                )
                # If LLM returned structured output by mistake, extract text
                if isinstance(summary, dict):
                    summary = summary.get("summary", summary.get("raw_response", str(summary)))
            except Exception as e:
                app_logger.error(f"Failed to generate GRC risk summary: {e}")
                summary = f"Document checked with {len(violations)} total violations. Compliance score: {score}. Risk class: {overall_risk}."
                
        return {
            "compliance_score": score,
            "overall_risk": overall_risk,
            "counts": {
                "critical": critical_count,
                "high": high_count,
                "medium": medium_count,
                "low": low_count
            },
            "summary": summary
        }

# Global agent instantiator
risk_agent = RiskScoringEngine()
