import os
import time
import hashlib
import threading
import shutil
import boto3
import requests
from datetime import datetime
from database.db import (
    get_setting,
    add_sync_record,
    get_sync_records,
    update_sync_status_by_hash,
    log_event,
    add_scan,
    update_scan_status
)
from graph.workflow import compliance_graph
from utils.logger import app_logger
from services.email_service import email_service

class IngestionSyncService:
    def __init__(self):
        self.stop_event = threading.Event()
        self.thread = None

    def start(self):
        """Starts the background monitoring sync daemon."""
        if self.thread is None or not self.thread.is_alive():
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            app_logger.info("Ingestion Sync background daemon started.")

    def stop(self):
        """Stops the background monitoring sync daemon."""
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=3)
            app_logger.info("Ingestion Sync background daemon stopped.")

    def _run_loop(self):
        """Periodically run sync procedures."""
        # Allow main thread database initialization to complete
        time.sleep(5)
        while not self.stop_event.is_set():
            try:
                self.sync_pipeline()
            except Exception as e:
                app_logger.error(f"Error in sync pipeline execution: {e}")
            # Poll every 10 seconds for responsive testing
            time.sleep(10)

    def calculate_sha256(self, file_path: str) -> str:
        """Returns SHA256 checksum of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def sync_pipeline(self):
        """Executes the ingestion sync pipeline: Monitors S3 Bucket -> Verifies metadata -> Scans."""
        import tempfile
        auto_mode = get_setting("auto_analysis_mode", "Manual")
        s3_bucket = get_setting("aws_s3_bucket", os.getenv("AWS_S3_BUCKET", "compliance-governance-bucket"))
        
        sync_records = get_sync_records()
        
        # Real S3 Bucket monitoring using boto3 client
        try:
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_REGION", "us-east-1")
            )
            response = s3_client.list_objects_v2(Bucket=s3_bucket)
        except Exception as e:
            app_logger.error(f"Sync: Failed to list objects in AWS S3 bucket '{s3_bucket}': {e}")
            return
            
        contents = response.get("Contents", [])
        for obj in contents:
            s3_key = obj.get("Key", "")
            allowed_extensions = (".pdf", ".txt", ".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".cs", ".go", ".sh", ".json", ".csv", ".md", ".html", ".css", ".yaml", ".yml")
            if not s3_key.lower().endswith(allowed_extensions):
                continue
                
            # Check if this object key is already processed
            exists = any(r["s3_key"] == s3_key for r in sync_records)
            if exists:
                continue
                
            filename = os.path.basename(s3_key)
            temp_path = None
            
            # Download file to calculate hash and process
            try:
                suffix = os.path.splitext(filename)[1]
                fd, temp_path = tempfile.mkstemp(suffix=suffix)
                os.close(fd)
                
                app_logger.info(f"Sync: Downloading new S3 object '{s3_key}' to calculate checksum...")
                s3_client.download_file(s3_bucket, s3_key, temp_path)
                file_hash = self.calculate_sha256(temp_path)
                
                # Delete temp file immediately after hash check
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
                
                # Verify by hash as well to prevent processing exact duplicate files
                hash_exists = any(r["file_hash"] == file_hash for r in sync_records)
                if hash_exists:
                    # Register S3 key anyway so we skip it next time
                    add_sync_record(filename, str(datetime.now()), file_hash, "Ignored", s3_key, f"s3://{s3_bucket}")
                    continue
                    
                # File is truly new
                log_event("FILE_DETECTED", filename, f"New file detected in AWS S3: {s3_key}")
                
                s3_uri = f"s3://{s3_bucket}/{s3_key}"
                add_sync_record(
                    filename=filename,
                    last_modified=obj.get("LastModified").astimezone().strftime("%Y-%m-%d %H:%M:%S") if obj.get("LastModified") else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    file_hash=file_hash,
                    sync_status="Synced",
                    s3_key=s3_key,
                    source_folder=f"s3://{s3_bucket}"
                )
                
                log_event("FILE_SYNCED", filename, f"Successfully synced metadata from S3 bucket '{s3_bucket}'.")
                
                if auto_mode == "Fully Automatic":
                    self.trigger_analysis(s3_uri, filename, file_hash, is_manual=False)
                    
            except Exception as err:
                app_logger.error(f"Sync: Failed to process S3 object '{s3_key}': {err}")
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass

    def trigger_analysis(self, file_path: str, filename: str, file_hash: str, is_manual: bool = False):
        """Launches the LangGraph workflow for compliance analysis."""
        import tempfile
        scan_type = "Manual Approval" if is_manual else "Auto"
        app_logger.info(f"Sync: Launching {scan_type.lower()} compliance analysis for {filename}...")
        
        # 1. DB log
        scan_id = add_scan(filename, file_path, status="Running")
        log_event("FILE_ANALYZED", filename, f"{scan_type} Analysis initiated. Scan ID: {scan_id}")
        
        # Setup transient download environment if target is S3 URI
        temp_local_path = None
        target_path = file_path
        
        if file_path.startswith("s3://"):
            try:
                parts = file_path[5:].split("/", 1)
                bucket = parts[0]
                key = parts[1]
                
                suffix = os.path.splitext(filename)[1]
                fd, temp_local_path = tempfile.mkstemp(suffix=suffix)
                os.close(fd)
                
                app_logger.info(f"Sync: Downloading S3 file for scanning: {file_path} -> {temp_local_path}")
                s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                    region_name=os.getenv("AWS_REGION", "us-east-1")
                )
                s3_client.download_file(bucket, key, temp_local_path)
                target_path = temp_local_path
            except Exception as d_err:
                app_logger.error(f"Sync: Failed to pull S3 candidate local copy: {d_err}")
                update_scan_status(scan_id, "Failed")
                return
        
        inputs = {
            "scan_id": scan_id,
            "pdf_path": target_path,
            "filename": filename,
            "extracted_pages": [],
            "pii_results": [],
            "confidential_results": [],
            "abuse_results": [],
            "encoding_results": [],
            "approved_violations": [],
            "policy_matches": [],
            "compliance_score": 100.0,
            "overall_risk": "LOW",
            "risk_summary": "",
            "report_path": "",
            "redacted_path": "",
            "estimated_cost_usd": 0.0,
            "latency_sec": 0.0
        }
        
        try:
            output = compliance_graph.invoke(inputs)
            update_sync_status_by_hash(file_hash, "Analyzed")
            log_event("REPORT_GENERATED", filename, f"{scan_type} Scan Complete. Score: {output['compliance_score']:.1f}/100. Report saved.")
            app_logger.info(f"Sync: {scan_type} Analysis for {filename} completed.")
            
            # Check for critical compliance alert
            violations = output.get("pii_results", []) + output.get("confidential_results", []) + output.get("abuse_results", []) + output.get("encoding_results", [])
            has_critical = any(v.get("severity", "").upper() == "CRITICAL" for v in violations) or output.get("overall_risk", "").upper() == "CRITICAL"
            
            if has_critical:
                subject = f"⚠️ CRITICAL COMPLIANCE VIOLATION: {filename}"
                body = (
                    f"Warning: A GRC compliance audit has flagged critical violations in document: '{filename}'.\n\n"
                    f"Scan Details:\n"
                    f"- Final Compliance Score: {output['compliance_score']:.1f}/100\n"
                    f"- Total Violations Found: {len(violations)}\n"
                    f"- System Assessment: CRITICAL RISK DETECTED\n\n"
                    f"Please review the logs immediately in the Case Overrides console."
                )
                email_service.send_alert(subject, body)
                
        except Exception as err:
            update_scan_status(scan_id, "Failed")
            log_event("FILE_ANALYZED", filename, f"{scan_type} Analysis failed. Error: {err}")
            app_logger.error(f"Sync: {scan_type} Analysis failed: {err}")
            
            # Pipeline failure alert
            subject = f"🔴 SYSTEM GRC PIPELINE FAILURE: {filename}"
            body = (
                f"Alert: The automated compliance scanning pipeline encountered a fatal exception.\n\n"
                f"File details:\n"
                f"- Filename: {filename}\n"
                f"- Resource: {file_path}\n"
                f"- Error stack:\n{str(err)}\n\n"
                f"Immediate system investigation is recommended."
            )
            email_service.send_alert(subject, body)
        finally:
            # Clean up transient copy immediately
            if temp_local_path and os.path.exists(temp_local_path):
                try:
                    os.remove(temp_local_path)
                    app_logger.info(f"Sync: Purged temp local copy '{temp_local_path}'.")
                except Exception as clean_err:
                    app_logger.warning(f"Sync: Failed to delete temp scan file: {clean_err}")

# Instantiation and start
sync_service = IngestionSyncService()
sync_service.start()
