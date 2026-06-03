import re
from typing import List, Dict, Any
from utils.logger import app_logger

# Common mojibake patterns representing encoding translation anomalies
MOJIBAKE_PATTERNS = [
    r"â‚¬", r"â€[“™˜œ¢¦¨]", r"Ã[©¡³±º´¶·¼½¾¿]", r"Ã«", r"Ã¶", r"Ã¼", r"Ã¤", r"ÃŸ",
    r"Ã¦", r"Ã§", r"Ã¨", r"Ã¬", r"Ã²", r"Ã¹", r"Ã+", r"Ã\*", r"Â[°¢£§©®µ¶]"
]

class EncodingAgent:
    def analyze_page(self, page_num: int, page_text: str) -> List[Dict[str, Any]]:
        """
        Scans document text for UTF-8 encoding inconsistencies, Mojibake,
        and invalid characters. Runs programmatically to optimize cost.
        """
        app_logger.info(f"Encoding Validator Agent scanning page {page_num}...")
        violations = []

        # 1. Check for Unicode Replacement Character (\ufffd, '')
        if "\ufffd" in page_text:
            snippet_index = page_text.find("\ufffd")
            snippet_start = max(0, snippet_index - 30)
            snippet_end = min(len(page_text), snippet_index + 30)
            snippet = page_text[snippet_start:snippet_end]
            
            violations.append({
                "page_number": page_num,
                "category": "Encoding",
                "entity_type": "Unicode Replacement Character",
                "severity": "MEDIUM",
                "confidence": 1.0,
                "snippet": "",
                "reason": f"Detected replacement character ('') suggesting character set decoding failure at: '...{snippet}...'.",
                "remediation": "Re-export PDF with correct UTF-8 mapping, or perform OCR extraction fallback."
            })

        # 2. Check for typical Mojibake (corrupted characters)
        for pattern in MOJIBAKE_PATTERNS:
            match = re.search(pattern, page_text)
            if match:
                start = max(0, match.start() - 30)
                end = min(len(page_text), match.end() + 30)
                snippet = page_text[start:end]
                
                violations.append({
                    "page_number": page_num,
                    "category": "Encoding",
                    "entity_type": "Mixed Encoding Mojibake",
                    "severity": "LOW",
                    "confidence": 0.95,
                    "snippet": match.group(0),
                    "reason": f"Detected mixed encoding anomaly (Mojibake pattern '{match.group(0)}') suggesting UTF-8 bytes read as Latin-1/ISO-8859-1 at: '...{snippet}...'.",
                    "remediation": "Repackage the document with explicit UTF-8 character declarations."
                })
                # Break to avoid duplicating for multiple mojibake on same page
                break

        return violations

# Global agent instantiator
encoding_agent = EncodingAgent()
