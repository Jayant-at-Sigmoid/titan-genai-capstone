import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle

def build_violations_pdf(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=15
    )
    
    h1_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor('#2C3E50'),
        spaceBefore=15,
        spaceAfter=10
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        spaceAfter=8
    )

    story = []
    
    # ================= PAGE 1: PII LEAKS =================
    story.append(Paragraph("Demo Artifact: Phase 1 Compliance Scan Test", title_style))
    story.append(Paragraph("Document Type: Project Kickoff & Resource Directory", h1_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("This page contains various PII elements including emails, phone numbers, credit card numbers, and government identification numbers to test the regex and LLM verification pipelines.", body_style))
    story.append(Spacer(1, 10))
    
    # Contact Info Table
    data = [
        [Paragraph("<b>Role</b>", body_style), Paragraph("<b>Name</b>", body_style), Paragraph("<b>Email</b>", body_style), Paragraph("<b>Direct Phone</b>", body_style)],
        [Paragraph("Project Sponsor", body_style), Paragraph("Sarah Jenkins", body_style), Paragraph("sarah.jenkins@compliance-demo.org", body_style), Paragraph("+1 (555) 234-5678", body_style)],
        [Paragraph("Lead Engineer", body_style), Paragraph("Rajesh Kumar", body_style), Paragraph("rajesh.kumar@compliance-demo.org", body_style), Paragraph("0987654321", body_style)],
        [Paragraph("Financial Lead", body_style), Paragraph("Emily Davis", body_style), Paragraph("emily.davis@compliance-demo.org", body_style), Paragraph("+44 20 7946 0958", body_style)]
    ]
    t = Table(data, colWidths=[110, 110, 180, 120])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#ECF0F1')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("<b>Corporate Purchasing Card Details:</b>", body_style))
    story.append(Paragraph("For hosting services, use the shared credit card: <b>4111 2222 3333 4444</b> (Exp: 12/28, CVV: 999). Keep this secure.", body_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("<b>Employee Onboarding Verification Identifiers:</b>", body_style))
    story.append(Paragraph("To complete the team verification, the following records are verified:", body_style))
    story.append(Paragraph("- Lead Developer Aadhaar: <b>2345 6789 0123</b>", body_style))
    story.append(Paragraph("- Lead Developer PAN: <b>ABCDE1234F</b>", body_style))
    
    story.append(PageBreak())
    
    # ================= PAGE 2: CONFIDENTIALITY LEAKS =================
    story.append(Paragraph("Internal Operations & Financial Strategy", title_style))
    story.append(Paragraph("Document Classification: STRICTLY CONFIDENTIAL - INTERNAL USE ONLY", h1_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("This document contains proprietary trade secret materials and internal financial forecasts. Distribution is strictly prohibited under NDA.", body_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("<b>Q3 Financial Projections & Margin Strategy:</b>", body_style))
    story.append(Paragraph("Our Q3 financial forecast indicates a massive shift. The projected revenue forecast for the anti-gravity division indicates a target of $12.5M with a target EBITDA projection of $3.8M. Our profit margin is expected to reach 30% by year-end.", body_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("<b>Intellectual Property & Core Algorithmic Framework:</b>", body_style))
    story.append(Paragraph("The proprietary algorithm powering our real-time scanning agent is a trade secret. Below is the source code disclosure of the scoring function:", body_style))
    
    # Mock code representation
    code_text = "def calculate_risk(violations):\n    # Proprietary core scoring method\n    score = 100.0 - sum(v['severity_weight'] for v in violations)\n    return max(0.0, score)"
    code_formatted = code_text.replace('\n', '<br/>').replace(' ', '&nbsp;')
    story.append(Paragraph(f"<font face='Courier' size='9'>{code_formatted}</font>", body_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("This scoring formula is patent pending and subject to trade secret protections.", body_style))
    
    story.append(PageBreak())
    
    # ================= PAGE 3: SAFETY & ABUSE VIOLATIONS =================
    story.append(Paragraph("Escalated Threat Intelligence & Feedback Logs", title_style))
    story.append(Paragraph("Document Section: Safety Vetting & External Correspondence", h1_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("The platform must scan incoming text communications for physical or digital threats, extortion attempts, and hate speech indicators to ensure compliance with our zero-tolerance policies.", body_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("<b>Incident Case Log #9011 (Extortion/Threat Case):</b>", body_style))
    story.append(Paragraph("The security team flagged an email from a disgruntled supplier containing explicit threats. The email read: <i>'I will destroy your reputation and destroy you unless you wire $50,000 immediately. I will extort every partner you have and blackmail your entire board of directors.'</i>", body_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("<b>Incident Case Log #9012 (Hate Speech Audit):</b>", body_style))
    story.append(Paragraph("We flagged internal communication chat messages containing slurs, derogatory racial comments, and links to online hate groups. The review committee approved immediate termination of the offending account.", body_style))
    
    story.append(PageBreak())
    
    # ================= PAGE 4: ENCODING ANOMALIES (MOJIBAKE) =================
    story.append(Paragraph("System Database Recovery Logs", title_style))
    story.append(Paragraph("Log Status: Encoding Diagnostics Output", h1_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("This page displays raw database outputs with invalid encoding mappings to trigger the Mojibake and character set corruption checkers.", body_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("<b>Raw Event Log dump with encoding corruption:</b>", body_style))
    story.append(Paragraph("Event 420: User updated profile information, but the database translation layer returned corrupted bytes: <b>â‚¬150.00</b> instead of €150.00.", body_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Event 421: German location string saved with encoding translation anomaly: Düsseldorf was loaded as <b>DÃ¼sseldorf</b> and stored as a mixed encoding Mojibake.", body_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Event 422: The database session character stream contains standard character replacements like: <b>\ufffd</b> which indicates a fallback character from decoding failure.", body_style))
    
    # Build document
    doc.build(story)
    print(f"Complex violations PDF generated successfully: {filename}")

if __name__ == "__main__":
    output_path = "/Users/as-mac-1214/Desktop/genai-project/complex_demo_violations.pdf"
    build_violations_pdf(output_path)
