import os
from datetime import datetime
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from utils.logger import app_logger

class AuditReportGenerator:
    @staticmethod
    def generate_pdf_report(
        output_path: str,
        filename: str,
        compliance_score: float,
        overall_risk: str,
        risk_summary: str,
        violations: List[Dict[str, Any]],
        policy_matches: List[Dict[str, Any]]
    ) -> str:
        """
        Creates a publication-grade GRC PDF audit report file using ReportLab.
        """
        app_logger.info(f"Generating PDF report file at {output_path}...")
        
        try:
            # Adjust margins to accommodate header/footer
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=54,
                leftMargin=54,
                topMargin=72,
                bottomMargin=72
            )
            
            styles = getSampleStyleSheet()
            
            # Custom Style Definitions
            primary_color = colors.HexColor("#1e293b")  # Dark Slate
            accent_color = colors.HexColor("#3b82f6")   # Slate Blue
            
            # Severity color helper
            def get_severity_color(sev: str):
                sev = sev.upper()
                if sev == "CRITICAL":
                    return colors.HexColor("#991b1b")  # Dark Red
                elif sev == "HIGH":
                    return colors.HexColor("#c2410c")      # Orange
                elif sev == "MEDIUM":
                    return colors.HexColor("#b45309")    # Yellow/Amber
                return colors.HexColor("#1e293b")        # Slate
                
            # Create custom paragraph styles
            title_style = ParagraphStyle(
                name="DocTitle",
                parent=styles["Title"],
                fontName="Helvetica-Bold",
                fontSize=24,
                leading=28,
                textColor=primary_color,
                alignment=0, # Left-aligned
                spaceAfter=15
            )
            
            h1_style = ParagraphStyle(
                name="Heading1Custom",
                parent=styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=14,
                leading=18,
                textColor=primary_color,
                spaceBefore=15,
                spaceAfter=10,
                keepWithNext=True
            )
            
            body_style = ParagraphStyle(
                name="BodyCustom",
                parent=styles["BodyText"],
                fontName="Helvetica",
                fontSize=10,
                leading=14,
                textColor=colors.HexColor("#334155")
            )
            
            bold_label_style = ParagraphStyle(
                name="BoldLabel",
                parent=body_style,
                fontName="Helvetica-Bold"
            )
            
            table_header_style = ParagraphStyle(
                name="TableHeader",
                parent=body_style,
                fontName="Helvetica-Bold",
                textColor=colors.white,
                fontSize=9,
                leading=11
            )
            
            table_cell_style = ParagraphStyle(
                name="TableCell",
                parent=body_style,
                fontSize=8.5,
                leading=11
            )
            
            table_cell_bold_style = ParagraphStyle(
                name="TableCellBold",
                parent=body_style,
                fontName="Helvetica-Bold",
                fontSize=8.5,
                leading=11
            )

            metric_title_style = ParagraphStyle(
                name="MetricTitleCustom",
                parent=body_style,
                fontName="Helvetica-Bold",
                fontSize=9,
                leading=12,
                alignment=1, # Centered
                textColor=colors.HexColor("#475569")
            )

            metric_val_style = ParagraphStyle(
                name="MetricValCustom",
                parent=body_style,
                fontName="Helvetica-Bold",
                fontSize=20,
                leading=24,
                alignment=1 # Centered
            )
            
            story = []
            
            # 1. Header Title
            story.append(Paragraph("PDF COMPLIANCE AUDIT REPORT", title_style))
            story.append(Paragraph(f"<b>Target Document:</b> {filename}", body_style))
            story.append(Paragraph(f"<b>Generated On:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body_style))
            story.append(Spacer(1, 15))
            
            # 2. Executive GRC Metrics Cards (Table format)
            risk_color = get_severity_color(overall_risk)
            metric_data = [
                [
                    Paragraph("COMPLIANCE SCORE", metric_title_style),
                    Paragraph("OVERALL RISK RATING", metric_title_style),
                    Paragraph("TOTAL VIOLATIONS", metric_title_style)
                ],
                [
                    Paragraph(f"<font color='{accent_color.hexval()}'>{compliance_score:.1f}/100</font>", metric_val_style),
                    Paragraph(f"<font color='{risk_color.hexval()}'>{overall_risk}</font>", metric_val_style),
                    Paragraph(f"<font color='#1e293b'>{len(violations)}</font>", metric_val_style)
                ]
            ]
            
            metric_table = Table(metric_data, colWidths=[168, 168, 168])
            metric_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 12),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ]))
            story.append(metric_table)
            story.append(Spacer(1, 20))
            
            # 3. Executive Summary
            story.append(Paragraph("Executive Summary", h1_style))
            story.append(Paragraph(risk_summary, body_style))
            story.append(Spacer(1, 20))
            
            # 4. Violations Ledger
            story.append(Paragraph("Detected Policy Violations Ledger", h1_style))
            if not violations:
                story.append(Paragraph("No compliance violations were detected in the document.", body_style))
            else:
                # Table headers
                table_data = [
                    [
                        Paragraph("Page", table_header_style),
                        Paragraph("Category", table_header_style),
                        Paragraph("Severity", table_header_style),
                        Paragraph("Sensitive Snippet", table_header_style),
                        Paragraph("Policy Clause / AI Reasoning", table_header_style)
                    ]
                ]
                
                # Fill table rows
                for v in violations:
                    page_num = str(v["page_number"])
                    category = v["category"]
                    severity = v["severity"].upper()
                    snippet = v.get("snippet", "")
                    
                    # Highlight severity text
                    sev_hex = get_severity_color(severity).hexval()
                    severity_para = Paragraph(f"<font color='{sev_hex}'><b>{severity}</b></font>", table_cell_bold_style)
                    
                    # Truncate snippet if too long
                    if len(snippet) > 60:
                        snippet = snippet[:57] + "..."
                        
                    reason_text = v.get("reason", "")
                    # Append policy reference context if any
                    policy_clause = v.get("policy_clause")
                    if policy_clause:
                        reason_text = f"<b>Policy Link:</b> {policy_clause}<br/>{reason_text}"
                    
                    table_data.append([
                        Paragraph(page_num, table_cell_style),
                        Paragraph(category, table_cell_style),
                        severity_para,
                        Paragraph(f"<code>{snippet}</code>" if snippet else "N/A", table_cell_style),
                        Paragraph(reason_text, table_cell_style)
                    ])
                
                # Calculate widths (sum is 504)
                violations_table = Table(table_data, colWidths=[35, 65, 55, 120, 229])
                violations_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), primary_color),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                    ("PADDING", (0, 0), (-1, -1), 6),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ]))
                story.append(violations_table)
                
            story.append(Spacer(1, 20))
            
            # 5. Core Security Recommendations
            story.append(Paragraph("Actionable Remediation Guidelines", h1_style))
            if not violations:
                story.append(Paragraph("1. No immediate actions required. Document is safe for distribution.", body_style))
            else:
                remediations = []
                # Deduplicate remediations
                seen_remeds = set()
                for v in violations:
                    remed = v.get("remediation")
                    if remed and remed not in seen_remeds:
                        seen_remeds.add(remed)
                        remediations.append(remed)
                        
                for i, r in enumerate(remediations):
                    story.append(Paragraph(f"<b>{i+1}.</b> {r}", body_style))
                    story.append(Spacer(1, 4))
                    
            story.append(Spacer(1, 30))
            
            # 6. Sign-off block
            story.append(Paragraph("Governance & Compliance Sign-off", h1_style))
            sign_data = [
                [Paragraph("<b>Audited By:</b> Automated Governance Agent", body_style), Paragraph("<b>Signature:</b> _________________________", body_style)],
                [Paragraph("<b>Consensus Status:</b> Verified by Lead Consensus Reviewer", body_style), Paragraph("<b>Date Approved:</b> _________________________", body_style)]
            ]
            sign_table = Table(sign_data, colWidths=[250, 254])
            sign_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(sign_table)
            
            # Custom running header/footer rendering
            def draw_cover_header_footer(canvas, doc_obj):
                canvas.saveState()
                canvas.setFont("Helvetica-Bold", 8)
                canvas.setFillColor(colors.HexColor("#64748B"))
                canvas.drawString(54, 30, "CONFIDENTIAL - SYSTEM GENERATED GRC REPORT")
                canvas.drawRightString(558, 30, "Page 1")
                canvas.setStrokeColor(colors.HexColor("#E2E8F0"))
                canvas.setLineWidth(0.5)
                canvas.line(54, 42, 558, 42)
                canvas.restoreState()

            def draw_later_header_footer(canvas, doc_obj):
                canvas.saveState()
                # Header
                canvas.setFont("Helvetica-Bold", 8)
                canvas.setFillColor(colors.HexColor("#64748B"))
                canvas.drawString(54, 755, f"COMPLIANCE AUDIT REPORT: {filename.upper()}")
                canvas.setStrokeColor(colors.HexColor("#E2E8F0"))
                canvas.setLineWidth(0.5)
                canvas.line(54, 747, 558, 747)
                # Footer
                canvas.setFont("Helvetica-Bold", 8)
                canvas.drawString(54, 30, "CONFIDENTIAL - SYSTEM GENERATED GRC REPORT")
                canvas.drawRightString(558, 30, f"Page {doc_obj.page}")
                canvas.line(54, 42, 558, 42)
                canvas.restoreState()

            # Compile document
            doc.build(story, onFirstPage=draw_cover_header_footer, onLaterPages=draw_later_header_footer)
            app_logger.info("PDF report compiled successfully.")
            return output_path
            
        except Exception as e:
            app_logger.error(f"Failed compiling ReportLab document flow: {e}")
            raise ValueError(f"Failed to generate report: {e}")

# Global report generator reference
report_generator = AuditReportGenerator()
