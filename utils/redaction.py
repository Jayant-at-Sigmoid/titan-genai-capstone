import os
import fitz  # PyMuPDF
from typing import List, Dict, Any
from utils.logger import app_logger

class PDFRedactionPipeline:
    @staticmethod
    def redact_pdf(original_pdf_path: str, output_pdf_path: str, violations: List[Dict[str, Any]]) -> str:
        """
        Redacts identified sensitive text (PII and Confidential snippets) in the PDF.
        Draws black bounding boxes and scrubs metadata using PyMuPDF.
        """
        if not os.path.exists(original_pdf_path):
            raise FileNotFoundError(f"Source PDF file not found at: {original_pdf_path}")
            
        app_logger.info(f"Initiating PDF Redaction pipeline from '{original_pdf_path}' to '{output_pdf_path}'...")
        
        try:
            doc = fitz.open(original_pdf_path)
            redacted_count = 0
            
            for v in violations:
                # We redact PII and Confidential categories containing snippets
                if v["category"] not in ["PII", "Confidential"]:
                    continue
                    
                page_num = v["page_number"]
                snippet = v.get("snippet")
                
                # Check valid bounds
                if not snippet or not snippet.strip():
                    continue
                if page_num < 1 or page_num > len(doc):
                    continue
                    
                page = doc.load_page(page_num - 1)
                
                # Search for coordinates of the violation snippet
                rects = page.search_for(snippet)
                
                if rects:
                    for rect in rects:
                        # Draw black redact box annotation
                        page.add_redact_annot(rect, text="", fill=(0, 0, 0))
                    page.apply_redactions()
                    redacted_count += len(rects)
                    
            # Scrub metadata for security compliance
            doc.set_metadata({
                "producer": "Enterprise PDF Compliance Engine",
                "creator": "Security Governor Agent",
                "title": f"Redacted - {os.path.basename(original_pdf_path)}"
            })
            
            # Ensure folder exists
            os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
            
            # Save the clean copy
            doc.save(output_pdf_path, garbage=4, deflate=True)
            doc.close()
            
            app_logger.info(f"Redaction process completed. Applied {redacted_count} blackbox overlays. Saved to {output_pdf_path}.")
            return output_pdf_path
            
        except Exception as e:
            app_logger.error(f"Failed to redact PDF: {e}")
            raise ValueError(f"Failed to redact PDF document: {e}")

# Global redactor reference
redactor = PDFRedactionPipeline()
