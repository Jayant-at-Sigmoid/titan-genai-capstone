from langgraph.graph import StateGraph, END
from graph.state import ComplianceState
from graph.nodes import (
    extract_pdf_node,
    pii_agent_node,
    confidential_agent_node,
    abuse_agent_node,
    encoding_agent_node,
    reviewer_consensus_node,
    rag_policy_validation_node,
    risk_scoring_node,
    report_generator_node
)

def create_compliance_workflow():
    """
    Compiles the LangGraph workflow engine.
    Orchestrates parallel scanning and consensus reviews.
    """
    workflow = StateGraph(ComplianceState)
    
    # 1. Add all graph nodes
    workflow.add_node("pdf_extractor", extract_pdf_node)
    workflow.add_node("pii_agent", pii_agent_node)
    workflow.add_node("confidential_agent", confidential_agent_node)
    workflow.add_node("abuse_agent", abuse_agent_node)
    workflow.add_node("encoding_agent", encoding_agent_node)
    workflow.add_node("reviewer_consensus", reviewer_consensus_node)
    workflow.add_node("rag_policy_validation", rag_policy_validation_node)
    workflow.add_node("risk_scoring", risk_scoring_node)
    workflow.add_node("report_generator", report_generator_node)
    
    # 2. Define compilation branches and execution order
    workflow.set_entry_point("pdf_extractor")
    
    # Parallel execution paths from extractor
    workflow.add_edge("pdf_extractor", "pii_agent")
    workflow.add_edge("pdf_extractor", "confidential_agent")
    workflow.add_edge("pdf_extractor", "abuse_agent")
    workflow.add_edge("pdf_extractor", "encoding_agent")
    
    # Join parallel paths into Consensus Reviewer node
    workflow.add_edge("pii_agent", "reviewer_consensus")
    workflow.add_edge("confidential_agent", "reviewer_consensus")
    workflow.add_edge("abuse_agent", "reviewer_consensus")
    workflow.add_edge("encoding_agent", "reviewer_consensus")
    
    # Sequential validation, scoring, and output nodes
    workflow.add_edge("reviewer_consensus", "rag_policy_validation")
    workflow.add_edge("rag_policy_validation", "risk_scoring")
    workflow.add_edge("risk_scoring", "report_generator")
    
    # Final step transition to end state
    workflow.add_edge("report_generator", END)
    
    return workflow.compile()

# Global compiled application graph
compliance_graph = create_compliance_workflow()
