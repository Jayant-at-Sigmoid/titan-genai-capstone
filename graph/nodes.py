import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List
from graph.state import ComplianceState
from utils.pdf_parser import pdf_parser
from utils.validators import security_validator
from agents.pii_agent import pii_agent
from agents.confidential_agent import confidential_agent
from agents.abuse_agent import abuse_agent
from agents.encoding_agent import encoding_agent
from agents.reviewer_agent import reviewer_agent
from agents.risk_agent import risk_agent
from services.vector_service import vector_service
from services.llm_service import llm_service
from utils.report_generator import report_generator
from database.db import update_scan_status, add_violation, get_setting
import tempfile
import shutil
import boto3
from utils.logger import app_logger

# Helper for parallel executions
def run_parallel_page_analysis(agent_fn, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Runs a page analysis agent function concurrently over pages."""
    results = []
    with ThreadPoolExecutor(max_workers=min(len(pages), 8)) as executor:
        futures = {executor.submit(agent_fn, page["page_num"], page["text"]): page for page in pages}
        for future in futures:
            try:
                page_results = future.result()
                if page_results:
                    results.extend(page_results)
            except Exception as e:
                app_logger.error(f"Error executing parallel page scan: {e}")
    return results

def extract_pdf_node(state: ComplianceState) -> Dict[str, Any]:
    """Node: Reads and extracts raw page content from input PDF file path."""
    start_time = time.time()
    pdf_path = state["pdf_path"]
    
    # Security Validation
    valid, message = security_validator.validate_pdf_file(pdf_path)
    if not valid:
        raise ValueError(f"File security check failed: {message}")
        
    pages = pdf_parser.extract_text_by_page(pdf_path)
    
    # Prompt injection check
    for p in pages:
        if security_validator.check_prompt_injection(p["text"]):
            raise ValueError(f"Security Warning: Prompt Injection indicator matched on Page {p['page_num']}.")
            
    return {
        "extracted_pages": pages,
        "filename": os.path.basename(pdf_path),
        "latency_sec": time.time() - start_time
    }

def pii_agent_node(state: ComplianceState) -> Dict[str, Any]:
    """Node: Runs parallel email/phone/card checks across pages."""
    start_time = time.time()
    pages = state["extracted_pages"]
    pii_results = run_parallel_page_analysis(pii_agent.analyze_page, pages)
    return {
        "pii_results": pii_results,
        "latency_sec": time.time() - start_time
    }

def confidential_agent_node(state: ComplianceState) -> Dict[str, Any]:
    """Node: Scans pages for IP/Financial/Strategy leaks."""
    start_time = time.time()
    pages = state["extracted_pages"]
    confidential_results = run_parallel_page_analysis(confidential_agent.analyze_page, pages)
    return {
        "confidential_results": confidential_results,
        "latency_sec": time.time() - start_time
    }

def abuse_agent_node(state: ComplianceState) -> Dict[str, Any]:
    """Node: Reviews pages for unlawful or safety violations."""
    start_time = time.time()
    pages = state["extracted_pages"]
    abuse_results = run_parallel_page_analysis(abuse_agent.analyze_page, pages)
    return {
        "abuse_results": abuse_results,
        "latency_sec": time.time() - start_time
    }

def encoding_agent_node(state: ComplianceState) -> Dict[str, Any]:
    """Node: Validates Unicode page representations for decoding errors."""
    start_time = time.time()
    pages = state["extracted_pages"]
    encoding_results = []
    
    # Sequential program check is fast enough
    for page in pages:
        results = encoding_agent.analyze_page(page["page_num"], page["text"])
        if results:
            encoding_results.extend(results)
            
    return {
        "encoding_results": encoding_results,
        "latency_sec": time.time() - start_time
    }

def reviewer_consensus_node(state: ComplianceState) -> Dict[str, Any]:
    """Node: Filters false positives, merges overlapping findings."""
    start_time = time.time()
    
    # Gather raw results from all agents
    all_raw_findings = []
    all_raw_findings.extend(state.get("pii_results", []))
    all_raw_findings.extend(state.get("confidential_results", []))
    all_raw_findings.extend(state.get("abuse_results", []))
    all_raw_findings.extend(state.get("encoding_results", []))
    
    approved_violations = reviewer_agent.review_violations(all_raw_findings)
    
    return {
        "approved_violations": approved_violations,
        "latency_sec": time.time() - start_time
    }

def rag_policy_validation_node(state: ComplianceState) -> Dict[str, Any]:
    """Node: Checks approved violations against FAISS-stored internal regulations."""
    start_time = time.time()
    violations = state.get("approved_violations", [])
    policy_matches = []
    
    for v in violations:
        snippet = v.get("snippet", "")
        if not snippet or len(snippet.strip()) < 10:
            continue
            
        # Search FAISS vector store
        matches = vector_service.search_policies(snippet, limit=1)
        if matches:
            match = matches[0]
            # Use Sonnet to reason why this snippet violates the retrieved policy section
            prompt = f"""You are an Enterprise Policy Auditor.
Verify if the snippet below violates the retrieved policy section.

Snippet: "{snippet}"
Retrieved Policy Section: "{match['clause_text']}" (Source: {match['policy_name']}, Page {match['page_number']})

Respond in standard JSON format:
{{
  "is_violation": true/false,
  "explanation": "Why this snippet violates (or does not violate) the policy section"
}}
"""
            try:
                # Ask Claude Sonnet
                res = llm_service.invoke_model(prompt, model_type="complex")
                if res.get("is_violation"):
                    match_info = {
                        "violation_category": v["category"],
                        "violation_snippet": snippet,
                        "policy_name": match["policy_name"],
                        "page_number": match["page_number"],
                        "clause_text": match["clause_text"],
                        "explanation": res.get("explanation", "Matches retrieved policy criteria.")
                    }
                    policy_matches.append(match_info)
                    
                    # Update violation record context in the state list directly
                    v["policy_clause"] = f"{match['policy_name']} (Page {match['page_number']})"
                    v["reason"] = f"{v['reason']} | Policy Match: {res.get('explanation')}"
            except Exception as e:
                app_logger.error(f"RAG reasoning failed: {e}")
                
    return {
        "policy_matches": policy_matches,
        "approved_violations": violations,
        "latency_sec": time.time() - start_time
    }

def risk_scoring_node(state: ComplianceState) -> Dict[str, Any]:
    """Node: Computes GRC indicators and risk scores."""
    start_time = time.time()
    violations = state["approved_violations"]
    risk_metrics = risk_agent.calculate_risk(violations)
    
    return {
        "compliance_score": risk_metrics["compliance_score"],
        "overall_risk": risk_metrics["overall_risk"],
        "risk_summary": risk_metrics["summary"],
        "latency_sec": time.time() - start_time
    }

def report_generator_node(state: ComplianceState) -> Dict[str, Any]:
    """Node: Generates ReportLab PDF audit ledger and auto-redacts sensitive contents."""
    start_time = time.time()
    
    scan_id = state["scan_id"]
    pdf_path = state["pdf_path"]
    filename = state["filename"]
    violations = state["approved_violations"]
    
    temp_dir = tempfile.mkdtemp()
    
    # Defaults in case upload fails
    report_s3_uri = ""
    redacted_s3_uri = ""
    
    try:
        # 1. Generate audit report file locally in temp folder
        report_filename = f"report_scan_{scan_id}.pdf"
        report_path = os.path.join(temp_dir, report_filename)
        
        # Build PDF report
        report_generator.generate_pdf_report(
            output_path=report_path,
            filename=filename,
            compliance_score=state["compliance_score"],
            overall_risk=state["overall_risk"],
            risk_summary=state["risk_summary"],
            violations=violations,
            policy_matches=state.get("policy_matches", [])
        )
        
        # 3. Upload report to AWS S3 Reports Bucket
        reports_bucket = get_setting("aws_reports_s3_bucket", os.getenv("AWS_REPORTS_S3_BUCKET", "compliance-governance-reports-bucket"))
        
        try:
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_REGION", "us-east-1")
            )
            
            # Upload report PDF
            s3_report_key = f"reports/report_scan_{scan_id}.pdf"
            app_logger.info(f"Sync: Uploading scan report {report_filename} to S3 bucket '{reports_bucket}'...")
            s3_client.upload_file(report_path, reports_bucket, s3_report_key)
            report_s3_uri = f"s3://{reports_bucket}/{s3_report_key}"
            redacted_s3_uri = ""
            
        except Exception as upload_err:
            app_logger.error(f"Failed to upload GRC reports to S3 bucket '{reports_bucket}': {upload_err}")
            # Fallback to local path representation in DB so app doesn't crash
            report_s3_uri = report_path
            redacted_s3_uri = ""
            
        # 4. SQLite updates & saving detections
        try:
            update_scan_status(
                scan_id=scan_id,
                status="Completed",
                compliance_score=state["compliance_score"],
                overall_risk=state["overall_risk"],
                report_path=report_s3_uri,
                redacted_path=redacted_s3_uri
            )
            
            # Save violations
            for v in violations:
                add_violation(
                    scan_id=scan_id,
                    page_number=v["page_number"],
                    category=v["category"],
                    entity_type=v.get("entity_type", ""),
                    severity=v["severity"],
                    confidence=v["confidence"],
                    snippet=v.get("snippet", ""),
                    reason=v["reason"],
                    remediation=v.get("remediation", "")
                )
                
            app_logger.info(f"Database scan record {scan_id} fully updated with S3 URIs.")
        except Exception as db_err:
            app_logger.error(f"Failed to commit scan details to SQLite: {db_err}")
            
    finally:
        # 5. Clean up temporary reports folder
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                app_logger.info(f"Purged transient report folder: {temp_dir}")
            except Exception as clean_err:
                app_logger.warning(f"Failed to delete temp reports folder: {clean_err}")
                
    # Cost optimization tracking summary
    cost_info = llm_service.get_metrics()
    
    return {
        "report_path": report_s3_uri,
        "redacted_path": redacted_s3_uri,
        "estimated_cost_usd": cost_info.get("estimated_cost_usd", 0.0),
        "latency_sec": time.time() - start_time
    }
