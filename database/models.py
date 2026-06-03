from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class ScanModel:
    id: Optional[int]
    filename: str
    file_path: str
    status: str
    compliance_score: float = 100.0
    overall_risk: str = "LOW"
    report_path: Optional[str] = None
    redacted_path: Optional[str] = None
    created_at: Optional[datetime] = None

@dataclass
class ViolationModel:
    id: Optional[int]
    scan_id: int
    page_number: int
    category: str  # PII, Confidential, Abuse, Encoding, Policy
    entity_type: Optional[str]
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    confidence: float = 1.0
    snippet: Optional[str] = None
    reason: Optional[str] = None
    remediation: Optional[str] = None
    review_status: str = "Pending"

@dataclass
class PolicyModel:
    id: Optional[int]
    filename: str
    file_path: str
    created_at: Optional[datetime] = None

@dataclass
class RuleModel:
    id: Optional[int]
    category: str
    name: str
    pattern: str
    severity: str
    is_active: bool = True
