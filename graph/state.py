from typing import TypedDict, List, Dict, Any, Optional, Annotated
import operator

class ComplianceState(TypedDict):
    scan_id: int
    pdf_path: str
    filename: str
    extracted_pages: List[Dict[str, Any]] # [{"page_num": int, "text": str}]
    
    # Raw Agent outputs
    pii_results: List[Dict[str, Any]]
    confidential_results: List[Dict[str, Any]]
    abuse_results: List[Dict[str, Any]]
    encoding_results: List[Dict[str, Any]]
    
    # Consensus validated violations
    approved_violations: List[Dict[str, Any]]
    
    # RAG policy findings mapping violations to standard items
    policy_matches: List[Dict[str, Any]]
    
    # Risk scoring details
    compliance_score: float
    overall_risk: str
    risk_summary: str
    
    # Execution artifacts
    report_path: str
    redacted_path: str
    
    # Usage analytics
    estimated_cost_usd: Annotated[float, operator.add]
    latency_sec: Annotated[float, operator.add]
