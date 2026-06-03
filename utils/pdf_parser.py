import os
import fitz  # PyMuPDF
from typing import List, Dict, Any
from utils.logger import app_logger

class PDFParser:
    @staticmethod
    def extract_text_by_page(file_path: str) -> List[Dict[str, Any]]:
        """
        Loads a PDF, text, or code file and returns a list of dictionaries with page numbers and text.
        Validates structure and checks for encryption for PDFs.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File does not exist at {file_path}")
            
        if not file_path.lower().endswith(".pdf"):
            app_logger.info(f"Opening text/code document for extraction: {file_path}")
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                chunk_size = 3000
                chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
                if not chunks:
                    chunks = [""]
                
                extracted_pages = []
                for i, chunk in enumerate(chunks):
                    extracted_pages.append({
                        "page_num": i + 1,
                        "text": chunk
                    })
                app_logger.info(f"Extracted {len(extracted_pages)} chunks/pages from text/code file {os.path.basename(file_path)}")
                return extracted_pages
            except Exception as e:
                app_logger.error(f"Failed to read file as text: {e}")
                raise ValueError(f"Failed to parse text/code file: {e}")
                
        app_logger.info(f"Opening PDF document for extraction: {file_path}")
        
        try:
            doc = fitz.open(file_path)
            
            # Validation checks
            if doc.is_encrypted:
                app_logger.error(f"Failed to parse PDF: File '{file_path}' is encrypted.")
                raise ValueError("PDF is encrypted and cannot be parsed without a decryption key.")
                
            page_count = len(doc)
            if page_count == 0:
                app_logger.error(f"Failed to parse PDF: File '{file_path}' contains zero pages.")
                raise ValueError("PDF file contains no pages.")
                
            extracted_pages = []
            
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                # Get raw text
                text = page.get_text("text")
                
                extracted_pages.append({
                    "page_num": page_num + 1,
                    "text": text
                })
                
            doc.close()
            app_logger.info(f"Extracted {page_count} pages from {os.path.basename(file_path)}")
            return extracted_pages
            
        except Exception as e:
            app_logger.error(f"PyMuPDF failed to parse document: {e}")
            raise ValueError(f"Failed to parse PDF file: {e}")

# Global parser instance
pdf_parser = PDFParser()
