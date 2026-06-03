# Save this as generate_test_pdfs.py and run: python generate_test_pdfs.py
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_pdf(filename, title, content_lines):
    c = canvas.Canvas(filename, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, title)
    c.setFont("Helvetica", 10)
    y = 700
    for line in content_lines:
        c.drawString(50, y, line)
        y -= 20
    c.save()
    print(f"Created PDF: {filename}")

# 1. Corporate Policy Directive (for RAG vector store)
create_pdf(
    "policy_sec_disclosure.pdf",
    "SEC Financial Disclosure Policy (Directive 4.2)",
    [
        "Section 4.2 - Forward-Looking Statements:",
        "All forward-looking financial earnings, projected revenue forecasts, and EBITDA",
        "projections are strictly internal and proprietary. Such data must not be disclosed",
        "in public materials without prior GRC auditor clearance."
    ]
)

# 2. Document with PII and Confidentiality leaks (Triggers PII, Confidentiality, and RAG Policy)
create_pdf(
    "q4_internal_report.pdf",
    "Q4 Financial Report - CONFIDENTIAL",
    [
        "CONFIDENTIAL: Internal Use Only",
        "Author: John Doe (john.doe@company.com) - Phone: +1 555-0199",
        "Projected Q4 revenue is expected to grow by 25% with EBITDA of $4.2M.",
        "The proprietary design of our anti-gravity system is protected under trade secret policies."
    ]
)

# 3. Document with Abuse/Unlawful strings (Triggers Safety scan)
create_pdf(
    "customer_feedback_complaint.pdf",
    "Urgent Customer Complaint Response",
    [
        "Subject: Account Cancellation Threat",
        "The customer sent a message saying: 'we will destroy your systems if you do not comply'",
        "and threatened to blackmail our customer support lead."
    ]
)
