import os
import unittest
import sqlite3

# Override DB path for clean isolated testing before importing database functions
TEST_DB_NAME = "test_compliance.db"
os.environ["COMPLIANCE_DB_PATH"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), TEST_DB_NAME)

from database.db import (
    init_db,
    add_scan,
    update_scan_status,
    get_scan,
    add_violation,
    get_violations_for_scan,
    update_violation_status,
    add_rule,
    get_rules_list,
    delete_scan,
    delete_event,
    clear_events,
    log_event,
    get_events_list
)

class TestDatabaseOperations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize schema
        init_db()

    @classmethod
    def tearDownClass(cls):
        # Clean up test database file
        db_path = os.environ.get("COMPLIANCE_DB_PATH")
        if db_path and os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass

    def test_scan_management(self):
        # Create scan
        scan_id = add_scan("test_document.pdf", "/tmp/test_document.pdf", "Pending")
        self.assertIsNotNone(scan_id)
        
        # Update status
        update_scan_status(
            scan_id=scan_id,
            status="Completed",
            compliance_score=95.0,
            overall_risk="LOW",
            report_path="/tmp/report.pdf",
            redacted_path="/tmp/redacted.pdf"
        )
        
        # Verify scan record
        scan = get_scan(scan_id)
        self.assertIsNotNone(scan)
        self.assertEqual(scan["status"], "Completed")
        self.assertEqual(scan["compliance_score"], 95.0)
        self.assertEqual(scan["overall_risk"], "LOW")

    def test_violation_management(self):
        # Create scan parent
        scan_id = add_scan("viol_test.pdf", "/tmp/viol_test.pdf", "Running")
        
        # Add violation
        viol_id = add_violation(
            scan_id=scan_id,
            page_number=1,
            category="PII",
            entity_type="Email",
            severity="MEDIUM",
            confidence=0.95,
            snippet="admin@company.com",
            reason="Exposes administrator credentials.",
            remediation="Redact email sequence."
        )
        self.assertIsNotNone(viol_id)
        
        # Retrieve list
        viols = get_violations_for_scan(scan_id)
        self.assertEqual(len(viols), 1)
        self.assertEqual(viols[0]["snippet"], "admin@company.com")
        self.assertEqual(viols[0]["review_status"], "Pending")
        
        # Update status
        update_violation_status(viol_id, "Approved", "Verified correct.")
        
        # Verify update
        viols_updated = get_violations_for_scan(scan_id)
        self.assertEqual(viols_updated[0]["review_status"], "Approved")

    def test_rules_loading(self):
        # Add rule
        add_rule("PII", "IP Address", r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "MEDIUM")
        
        rules = get_rules_list()
        self.assertTrue(len(rules) > 0)
        has_ip_rule = any(r["name"] == "IP Address" for r in rules)
        self.assertTrue(has_ip_rule)

    def test_deletion_helpers(self):
        # 1. Scan deletion
        scan_id = add_scan("temp_del.pdf", "/tmp/temp_del.pdf", "Completed")
        self.assertIsNotNone(get_scan(scan_id))
        delete_scan(scan_id)
        self.assertIsNone(get_scan(scan_id))
        
        # 2. Event deletion
        log_event("TEST_EVENT", "test_resource", "test log description")
        events = get_events_list()
        self.assertTrue(len(events) > 0)
        
        # Test individual event deletion
        event_id = events[0]["id"]
        delete_event(event_id)
        events_after_del = [e for e in get_events_list() if e["id"] == event_id]
        self.assertEqual(len(events_after_del), 0)
        
        # Test clearing all events
        log_event("TEST_EVENT_2", "res2", "desc2")
        self.assertTrue(len(get_events_list()) > 0)
        clear_events()
        self.assertEqual(len(get_events_list()), 0)

if __name__ == "__main__":
    unittest.main()
