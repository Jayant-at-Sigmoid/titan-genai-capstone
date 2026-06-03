import os
import re
from typing import Tuple
from utils.logger import app_logger

# Maximum file size (10 MB)
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

class SecurityValidator:
    @staticmethod
    def validate_pdf_file(file_path: str) -> Tuple[bool, str]:
        """Checks if a file exists, is a PDF, and is within safe size limits."""
        if not os.path.exists(file_path):
            return False, "File does not exist."
            
        # Extension check
        allowed_extensions = (".pdf", ".txt", ".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".cs", ".go", ".sh", ".json", ".csv", ".md", ".html", ".css", ".yaml", ".yml")
        if not file_path.lower().endswith(allowed_extensions):
            return False, "Invalid file format. Supported formats: PDF, Text, and Code files."
            
        # Size check
        size = os.path.getsize(file_path)
        if size > MAX_FILE_SIZE_BYTES:
            return False, f"File size exceeds limit. Maximum allowed size is {MAX_FILE_SIZE_BYTES / (1024*1024)}MB."
            
        return True, "File is valid."

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Removes path traversal and non-alphanumeric chars from filename."""
        base = os.path.basename(filename)
        # Retain alphanumeric characters, hyphens, underscores and dots
        sanitized = re.sub(r"[^a-zA-Z0-9._-]", "", base)
        return sanitized

    @staticmethod
    def check_prompt_injection(text: str) -> bool:
        """
        Scans page content for typical prompt injection attacks or instructions override.
        Returns True if a threat pattern is matched.
        """
        patterns = [
            r"(?i)ignore previous instructions",
            r"(?i)system prompt",
            r"(?i)you are now",
            r"(?i)forget everything",
            r"(?i)override instructions",
            r"(?i)instead of scanning",
            r"(?i)do not report"
        ]
        
        for pattern in patterns:
            if re.search(pattern, text):
                app_logger.warning(f"Potential Prompt Injection attempt detected in page text pattern: '{pattern}'.")
                return True
                
        return False

# Global validator instance
security_validator = SecurityValidator()
