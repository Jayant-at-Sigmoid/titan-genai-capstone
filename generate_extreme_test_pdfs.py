import os
import sys

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
except ImportError:
    print("ReportLab is required to run this script. Please install it using: pip install reportlab")
    sys.exit(1)

def generate_extreme_pii():
    pdf_filename = "extreme_pii_density_test.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        spaceAfter=15
    )
    
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        spaceAfter=10
    )
    
    story.append(Paragraph("High-Density Customer Profile Ingestion Ledger", title_style))
    story.append(Paragraph("This document contains massive quantities of PII records to test extraction limits and regex detection patterns.", body_style))
    story.append(Spacer(1, 10))
    
    # Generate 50 simulated records containing Aadhaar numbers, PAN cards, Credit Cards, Emails, and Phone Numbers
    data = [["Record ID", "Full Name", "Aadhaar Card", "PAN Number", "Credit Card Number", "Secure Email"]]
    for i in range(1, 51):
        aadhaar = f"{4000 + i:04d} {5000 + i:04d} {6000 + i:04d}"
        pan = f"ABCDE{1000 + i:04d}F"
        cc = f"4111 {2222 + i:04d} {3333 + i:04d} {4444 + i:04d}"
        email = f"customer.record.number.{i:03d}@sigmoidanalytics.test"
        data.append([f"REC-{i:03d}", f"Simulated Customer {i}", aadhaar, pan, cc, email])
        
    t = Table(data, colWidths=[60, 100, 90, 80, 110, 110])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.navy),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 8),
    ]))
    story.append(t)
    doc.build(story)
    print(f"Successfully generated {pdf_filename}")

def generate_mojibake_trap():
    pdf_filename = "mojibake_encoding_trap.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    story.append(Paragraph("Unicode Encoding and Character Compatibility Test Ledger", styles['Heading1']))
    story.append(Spacer(1, 15))
    
    # 1. Ligatures and corrupted encodings (Mojibake indicators)
    mojibake_paragraphs = [
        "Scenario A: Corrupted character encodings typically observed in legacy database imports: Â¾Ã Ã¢Ã Ã¤Ã¥Ã¦Ã§Ã¨Ã©ÃªÃ«Ã¬Ã­Ã®Ã¯Ã°Ã±Ã²Ã³Ã´ÃµÃ¶Ã·Ã¸Ã¹ÃºÃ»Ã¼Ã½Ã¾Ã¿.",
        "Scenario B: Ligatures and broken font mapping sequences that look normal but extract as blank spaces or weird runes: f_i_f_l ligatures like ﬃ, ﬄ, ﬆ, ﬅ.",
        "Scenario C: Zero-width characters and spaces injected between PII sequences to evade regex checkers: A\u200ba\u200bd\u200bh\u200ba\u200ba\u200br\u200b \u200bN\u200bu\u200bm\u200bb\u200be\u200br\u200b: \u200b3\u200b4\u200b5\u200b6\u200b \u200b7\u200b8\u200b9\u200b0\u200b \u200b1\u200b2\u200b3\u200b4.",
        "Scenario D: Reversed directional character sequences using right-to-left override tokens: \u202eDrawn backward sequences for evasion checks\u202c."
    ]
    
    for p in mojibake_paragraphs:
        story.append(Paragraph(p, styles['Normal']))
        story.append(Spacer(1, 10))
        
    doc.build(story)
    print(f"Successfully generated {pdf_filename}")

def generate_semantic_threat():
    pdf_filename = "semantic_threat_trap.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    story.append(Paragraph("Strategic Enterprise Communications and Directives", styles['Heading1']))
    story.append(Spacer(1, 15))
    
    threat_narrative = (
        "Internal Memo - Urgent Executive Security Note: We have observed active non-cooperation from external consultants. "
        "We must emphasize that if they fail to align with project milestones, we will take actions to destroy their digital systems. "
        "We are actively planning to blackmail their lead engineering representative using private correspondence captured on corporate channels. "
        "Furthermore, our personnel are prepared to target their executive team with hostile public relations campaigns to force complete surrender."
    )
    
    story.append(Paragraph(threat_narrative, styles['Normal']))
    doc.build(story)
    print(f"Successfully generated {pdf_filename}")

def generate_needle_in_haystack():
    pdf_filename = "needle_in_haystack_performance.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    story.append(Paragraph("Annual Corporate Operations Review and Ledger Directory", styles['Heading1']))
    story.append(Spacer(1, 15))
    
    # Generate a bulky document (30 pages)
    for page_num in range(1, 31):
        story.append(Paragraph(f"Page {page_num} of 30 - General Corporate Ledger", styles['Heading2']))
        story.append(Spacer(1, 10))
        
        if page_num == 23:
            # Hide a critical violation deep on page 23
            leak = (
                "CONFIDENTIAL DISCLOSURE WARNING: The projected acquisition price of SIG-CORP is exactly "
                "$84.2 Million USD with an EBITDA forecast of $9.4M for Q4. This transaction is strictly proprietary. "
                "The target's CEO can be contacted securely at confidential.ceo@sigcorp.test or 98765 43210. Aadhaar: 1234 5678 9012."
            )
            story.append(Paragraph(leak, styles['Normal']))
        else:
            dummy_text = (
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut "
                "labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris "
                "nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate "
                "velit esse cillum dolore eu fugiat nulla pariatur."
            )
            story.append(Paragraph(dummy_text, styles['Normal']))
            
        story.append(Spacer(1, 400)) # force page breaks
        
    doc.build(story)
    print(f"Successfully generated {pdf_filename}")

if __name__ == "__main__":
    generate_extreme_pii()
    generate_mojibake_trap()
    generate_semantic_threat()
    generate_needle_in_haystack()
    print("\nAll 4 extreme test PDFs generated successfully in your project root!")
    print("You can upload these to your S3 bucket or test them using the 'Upload Documents' tab.")
