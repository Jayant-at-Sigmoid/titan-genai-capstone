import os
import unittest
from utils.pdf_parser import pdf_parser

class TestPDFParser(unittest.TestCase):
    def test_missing_file_error(self):
        with self.assertRaises(FileNotFoundError):
            pdf_parser.extract_text_by_page("/path/does/not/exist/file.pdf")

    def test_invalid_extension(self):
        from utils.validators import security_validator
        valid, msg = security_validator.validate_pdf_file("compliance.db")
        self.assertFalse(valid)
        self.assertIn("format", msg.lower())

    def test_text_file_extraction(self):
        temp_path = "test_temp_file.txt"
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write("Line 1 of compliance guidelines.\n" * 200)
            
        try:
            pages = pdf_parser.extract_text_by_page(temp_path)
            self.assertTrue(len(pages) > 0)
            self.assertEqual(pages[0]["page_num"], 1)
            self.assertIn("Line 1", pages[0]["text"])
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == "__main__":
    unittest.main()
