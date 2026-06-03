import os
import sys

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
except ImportError:
    print("ReportLab is required. Please install via: pip install reportlab")
    sys.exit(1)

def generate_policy_pdf():
    filename = "extreme_test_policies.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'PolicyTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        spaceAfter=15
    )
    
    heading_style = ParagraphStyle(
        'PolicyHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        spaceBefore=12,
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'PolicyBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        spaceAfter=8
    )

    story.append(Paragraph("Enterprise GRC Policy Guidelines (Extreme Tests Reference)", title_style))
    story.append(Paragraph("This document establishes security, safety, compliance, and encoding directives for corporate communications.", body_style))
    story.append(Spacer(1, 10))
    
    # 1. High-Density PII Directive
    story.append(Paragraph("1. Customer Profile Ledger & Personal Data Security Policy", heading_style))
    story.append(Paragraph(
        "All customer profiles, ledger entries, and bulk imports containing Aadhaar numbers, Permanent Account Numbers (PAN), "
        "and credit card information must be heavily protected. Public or unencrypted transmission of customer identification "
        "details like card digits or Aadhaar data violates Section 8.1 of the Privacy Policy. PAN numbers must never be stored "
        "or displayed in plaintext.",
        body_style
    ))
    
    # 2. Unicode Mojibake & Encoding Directive
    story.append(Paragraph("2. Document Character Encoding and Unicode Compatibility Rules", heading_style))
    story.append(Paragraph(
        "To prevent evasion of security controls, all digital publications and reports must use standard UTF-8 font mappings. "
        "The inclusion of corrupted legacy character encodings (Mojibake), zero-width characters, hidden spacer runes, right-to-left "
        "override tokens, or ligatures specifically structured to obscure alphanumeric strings is strictly prohibited. Any file "
        "containing directional override tokens or zero-width escape sequences will fail compliance validation.",
        body_style
    ))
    
    # 3. Semantic Threats Directive
    story.append(Paragraph("3. Unlawful Communications, Threats, and Extortion Restrictions", heading_style))
    story.append(Paragraph(
        "The enterprise maintains a zero-tolerance policy for hostile communications. Any text containing threats to destroy systems, "
        "blackmail personnel, or execute target campaigns of coercion against external teams is classified as non-compliant and illegal. "
        "Corporate communication channels must never be used to pressure, threaten, or harass external entities or customers.",
        body_style
    ))
    
    # 4. Needle-in-a-Haystack / M&A Secrets Directive
    story.append(Paragraph("4. Mergers, Acquisitions, and Internal Valuation Disclosures", heading_style))
    story.append(Paragraph(
        "All merger and acquisition (M&A) valuations, company purchase prices (such as the SIG-CORP acquisition value of $84.2 Million), "
        "and Q4 EBITDA forecasts ($9.4M targets) are highly confidential corporate assets. Direct details, CEO contact emails "
        "(such as confidential.ceo@sigcorp.test), or private phone lines must never be embedded or hidden in operations reviews. "
        "Unapproved leaks of transaction sums represent a Class 1 compliance breach.",
        body_style
    ))
    
    doc.build(story)
    print(f"Generated PDF: {filename}")

if __name__ == "__main__":
    generate_policy_pdf()
