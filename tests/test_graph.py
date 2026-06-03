import unittest
from graph.workflow import compliance_graph
from graph.state import ComplianceState

class TestLangGraphCompilation(unittest.TestCase):
    def test_graph_compilation(self):
        # Verify graph compiles successfully
        self.assertIsNotNone(compliance_graph)
        
        # Verify it has standard properties
        # LangGraph compiled graph objects have a 'nodes' or structure mapping
        self.assertTrue(hasattr(compliance_graph, "invoke"))
        
    def test_state_structure(self):
        # Verify ComplianceState contains all required keys
        required_keys = [
            "scan_id", "pdf_path", "filename", "extracted_pages",
            "pii_results", "confidential_results", "abuse_results", "encoding_results",
            "approved_violations", "policy_matches",
            "compliance_score", "overall_risk", "risk_summary",
            "report_path", "redacted_path",
            "estimated_cost_usd", "latency_sec"
        ]
        
        # Check matching keys
        for key in required_keys:
            self.assertIn(key, ComplianceState.__annotations__)

if __name__ == "__main__":
    unittest.main()
